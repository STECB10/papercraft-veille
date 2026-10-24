"""Outils partagés du bot : chemins, appels HTTP, Telegram."""
import datetime as dt
import json
import mimetypes
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

RACINE = pathlib.Path(__file__).resolve().parent.parent
JOURS = RACINE / "jours"
HISTORIQUE = RACINE / "pipeline" / "historique.json"


def aujourdhui():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=1))).strftime("%Y-%m-%d")


def dossier_du_jour(date=None):
    return JOURS / (date or os.environ.get("DATE_DU_JOUR") or aujourdhui())


def env(nom):
    v = os.environ.get(nom, "").strip()
    if not v:
        raise SystemExit(f"secret manquant : {nom}")
    return v


def lire_json(p, defaut=None):
    p = pathlib.Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else defaut


def ecrire_json(p, data):
    pathlib.Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def http(url, data=None, headers=None, method=None, timeout=120, essais=3, brut=False):
    """GET/POST avec reprises. data : dict (JSON), bytes, ou None."""
    headers = dict(headers or {})
    body = None
    if isinstance(data, dict):
        body = json.dumps(data).encode()
        headers.setdefault("Content-Type", "application/json")
    elif data is not None:
        body = data
    for k in range(essais):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = r.read()
                return out if brut else json.loads(out.decode() or "{}")
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if e.code < 500 and e.code != 429:
                raise RuntimeError(f"HTTP {e.code} sur {url.split('?')[0]} : {msg}")
            err = f"HTTP {e.code} : {msg}"
        except Exception as e:  # réseau
            err = str(e)
        time.sleep(4 * (k + 1))
    raise RuntimeError(f"échec après {essais} essais sur {url.split('?')[0]} : {err}")


def multipart(champs, fichiers):
    """champs : liste (nom, valeur) ; fichiers : liste (nom, chemin). Retourne (corps, content-type)."""
    b = "----pc" + uuid.uuid4().hex
    out = bytearray()
    for nom, val in champs:
        out += f"--{b}\r\nContent-Disposition: form-data; name=\"{nom}\"\r\n\r\n{val}\r\n".encode()
    for nom, chemin in fichiers:
        chemin = pathlib.Path(chemin)
        ct = mimetypes.guess_type(chemin.name)[0] or "application/octet-stream"
        out += f"--{b}\r\nContent-Disposition: form-data; name=\"{nom}\"; filename=\"{chemin.name}\"\r\nContent-Type: {ct}\r\n\r\n".encode()
        out += chemin.read_bytes() + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={b}"


# ------------------------------------------------------------------ Telegram
def tg(methode, data=None, fichiers=None, timeout=120):
    url = f"https://api.telegram.org/bot{env('TELEGRAM_BOT_TOKEN')}/{methode}"
    if fichiers:
        champs = [(k, json.dumps(v) if isinstance(v, (dict, list)) else str(v)) for k, v in (data or {}).items()]
        corps, ct = multipart(champs, fichiers)
        r = http(url, corps, {"Content-Type": ct}, timeout=timeout)
    else:
        r = http(url, data or {}, timeout=timeout)
    if not r.get("ok"):
        raise RuntimeError(f"Telegram {methode} : {r}")
    return r["result"]


def tg_message(texte, **extra):
    return tg("sendMessage", {"chat_id": env("TELEGRAM_CHAT_ID"), "text": texte[:4000], "disable_web_page_preview": True, **extra})
