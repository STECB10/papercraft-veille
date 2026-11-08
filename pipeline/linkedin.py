#!/usr/bin/env python3
"""Publication directe sur la page LinkedIn Papercraft.AI, par l'API officielle (Community Management API), sans
intermédiaire payant. Utilisée en premier par publication.py ; Upload-Post reste le secours.

Le parcours (documentation LinkedIn « Videos API » et « Posts API ») :
  1. POST /rest/videos?action=initializeUpload   -> l'URN de la vidéo et les adresses d'envoi, morceau par morceau
  2. PUT de chaque morceau                        -> on garde l'ETag de chacun
  3. POST /rest/videos?action=finalizeUpload     -> LinkedIn assemble la vidéo
  4. GET /rest/videos/<urn> jusqu'à AVAILABLE    -> la vidéo est prête
  5. POST /rest/posts                            -> le post (texte + vidéo) sur la page, au nom de l'organisation

Secrets (GitHub Actions) :
  LINKEDIN_ACCESS_TOKEN    jeton d'accès (60 jours), écrit par pipeline/linkedin_connexion.py
  LINKEDIN_REFRESH_TOKEN   jeton de renouvellement, si LinkedIn en donne un à l'application (sinon vide)
  LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET   identifiants de l'application (renouvellement, date d'expiration)
  LINKEDIN_PAGE_ID         facultatif : l'URN de la page (par défaut Papercraft.AI)
"""
import datetime as dt
import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.linkedin.com/rest"
OAUTH = "https://www.linkedin.com/oauth/v2"
PAGE = os.environ.get("LINKEDIN_PAGE_ID") or "urn:li:organization:145361149"   # page Papercraft.AI
RESERVES = set("\\|{}@[]()<>*_~")


class ErreurLinkedIn(RuntimeError):
    pass


def configure():
    return bool(os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip() or os.environ.get("LINKEDIN_REFRESH_TOKEN", "").strip())


def versions():
    """L'en-tête Linkedin-Version (AAAAMM) : chaque version vit au moins un an. On prend celle d'il y a deux mois
    (toujours sortie, jamais en fin de vie), puis les précédentes si LinkedIn la refuse."""
    v = os.environ.get("LINKEDIN_VERSION", "").strip()
    if v:
        return [v]
    d = dt.date.today()
    base = d.year * 12 + d.month - 1
    return [f"{(base - k) // 12}{(base - k) % 12 + 1:02d}" for k in range(2, 6)]


def _req(methode, url, corps=None, entetes=None, timeout=120):
    """Renvoie (code, en-têtes en minuscules, corps décodé en JSON si possible)."""
    data = None
    h = dict(entetes or {})
    if isinstance(corps, (dict, list)):
        data = json.dumps(corps, ensure_ascii=False).encode()
        h.setdefault("Content-Type", "application/json")
    elif corps is not None:
        data = corps
    req = urllib.request.Request(url, data=data, headers=h, method=methode)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            brut = r.read()
            code, hd = r.status, {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        brut = e.read()
        code, hd = e.code, {k.lower(): v for k, v in (e.headers or {}).items()}
    try:
        js = json.loads(brut.decode() or "{}")
    except ValueError:
        js = {"brut": brut.decode(errors="replace")[:500]}
    return code, hd, js


def jeton():
    """Le jeton d'accès : renouvelé avec le jeton de renouvellement s'il existe, sinon celui des secrets."""
    rt = os.environ.get("LINKEDIN_REFRESH_TOKEN", "").strip()
    cid, sec = os.environ.get("LINKEDIN_CLIENT_ID", "").strip(), os.environ.get("LINKEDIN_CLIENT_SECRET", "").strip()
    if rt and cid and sec:
        corps = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": rt, "client_id": cid,
                                        "client_secret": sec}).encode()
        code, _, js = _req("POST", f"{OAUTH}/accessToken", corps, {"Content-Type": "application/x-www-form-urlencoded"})
        if code == 200 and js.get("access_token"):
            return js["access_token"]
        if not os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip():
            raise ErreurLinkedIn(f"renouvellement du jeton refusé ({code}) : relancer pipeline/linkedin_connexion.py — {js}")
    t = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not t:
        raise ErreurLinkedIn("pas de jeton LinkedIn (secret LINKEDIN_ACCESS_TOKEN)")
    return t


class Client:
    def __init__(self, token=None):
        self.token = token or jeton()
        self.version = None

    def appel(self, methode, chemin, corps=None, attendu=(200, 201)):
        essais = [self.version] if self.version else versions()
        for v in essais:
            h = {"Authorization": f"Bearer {self.token}", "Linkedin-Version": v, "X-Restli-Protocol-Version": "2.0.0"}
            code, hd, js = _req(methode, f"{API}{chemin}", corps, h)
            if code in (426, 400) and "version" in json.dumps(js).lower() and v != essais[-1]:
                continue        # version refusée (trop ancienne ou pas encore sortie) : la précédente
            self.version = v
            if code == 401:
                raise ErreurLinkedIn("jeton LinkedIn expiré ou révoqué : relancer pipeline/linkedin_connexion.py sur le Mac")
            if code == 403:
                raise ErreurLinkedIn(f"accès refusé par LinkedIn (droits sur la page ou accès à l'API) : {js}")
            if code not in attendu:
                raise ErreurLinkedIn(f"LinkedIn {methode} {chemin.split('?')[0]} : {code} {json.dumps(js, ensure_ascii=False)[:400]}")
            return hd, js
        raise ErreurLinkedIn("aucune version de l'API acceptée")

    def envoyer_video(self, chemin, owner=PAGE, attente=600):
        chemin = pathlib.Path(chemin)
        taille = chemin.stat().st_size
        _, js = self.appel("POST", "/videos?action=initializeUpload", {"initializeUploadRequest": {
            "owner": owner, "fileSizeBytes": taille, "uploadCaptions": False, "uploadThumbnail": False}})
        v = js["value"]
        urn, morceaux, jeton_envoi = v["video"], v["uploadInstructions"], v.get("uploadToken", "")
        etags = []
        with open(chemin, "rb") as f:
            for m in morceaux:
                a, b = int(m["firstByte"]), int(m["lastByte"])
                f.seek(a)
                part = f.read(b - a + 1)
                for essai in range(3):
                    code, hd, js2 = _req("PUT", m["uploadUrl"], part, {"Content-Type": "application/octet-stream"}, timeout=300)
                    if code in (200, 201) and hd.get("etag"):
                        etags.append(hd["etag"].strip('"'))
                        break
                    time.sleep(5 * (essai + 1))
                else:
                    raise ErreurLinkedIn(f"envoi du morceau {a}-{b} refusé : {code} {js2}")
        self.appel("POST", "/videos?action=finalizeUpload", {"finalizeUploadRequest": {
            "video": urn, "uploadToken": jeton_envoi, "uploadedPartIds": etags}})
        fin = time.time() + attente
        statut = "?"
        while time.time() < fin:
            _, js = self.appel("GET", f"/videos/{urllib.parse.quote(urn, safe='')}")
            statut = js.get("status")
            if statut == "AVAILABLE":
                return urn
            if statut == "PROCESSING_FAILED":
                raise ErreurLinkedIn(f"LinkedIn n'a pas pu traiter la vidéo : {js.get('processingFailureReason')}")
            time.sleep(10)
        raise ErreurLinkedIn(f"vidéo toujours en traitement après {attente} s (statut {statut})")

    def poster(self, texte, video_urn, titre, auteur=PAGE):
        hd, _ = self.appel("POST", "/posts", {
            "author": auteur, "commentary": echapper(texte), "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": {"media": {"title": titre[:200], "id": video_urn}},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}, attendu=(201,))
        return hd.get("x-restli-id", "")


def echapper(texte):
    """Format « little text » de LinkedIn : les caractères réservés sont précédés d'une barre oblique inverse, sinon le
    post est coupé ou refusé. Les hashtags (# suivi d'un mot) restent des hashtags ; un # isolé est échappé."""
    out = []
    for i, c in enumerate(texte):
        if c in RESERVES:
            out.append("\\" + c)
        elif c == "#":
            suivant = texte[i + 1] if i + 1 < len(texte) else ""
            out.append("#" if (suivant.isalnum() and (i == 0 or not texte[i - 1].isalnum())) else "\\#")
        else:
            out.append(c)
    return "".join(out)


def publier(video, texte, titre):
    """Publie la vidéo et son texte sur la page. Renvoie l'identifiant du post."""
    c = Client()
    urn = c.envoyer_video(video)
    return c.poster(texte, urn, titre)


def jours_restants():
    """Jours avant l'expiration du jeton d'accès (introspection LinkedIn), ou None si on ne peut pas le savoir."""
    t = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    cid, sec = os.environ.get("LINKEDIN_CLIENT_ID", "").strip(), os.environ.get("LINKEDIN_CLIENT_SECRET", "").strip()
    if not (t and cid and sec) or os.environ.get("LINKEDIN_REFRESH_TOKEN", "").strip():
        return None
    corps = urllib.parse.urlencode({"client_id": cid, "client_secret": sec, "token": t}).encode()
    code, _, js = _req("POST", f"{OAUTH}/introspectToken", corps, {"Content-Type": "application/x-www-form-urlencoded"})
    if code != 200:
        return None
    if not js.get("active", True):
        return 0
    exp = js.get("expires_at")
    return None if not exp else max(0, int((float(exp) - time.time()) // 86400))
