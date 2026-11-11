#!/usr/bin/env python3
"""Envoi pour validation sur Telegram, publication LinkedIn (via Upload-Post) et écoute des boutons.

  python3 pipeline/publication.py envoyer     après fabriquer.py : range la vidéo (release GitHub « jour-<date> »),
                                              puis l'envoie sur Telegram avec Publier / Rejeter
                                              (ou publie directement si la variable PUBLICATION_AUTO vaut « oui »)
  python3 pipeline/publication.py ecouter     lit les clics Telegram et publie / rejette (lancé toutes les 30 min)
  python3 pipeline/publication.py remplacer <dossier>
                                              remplace la vidéo d'un jour pas encore publié par celle d'un essai
                                              (téléchargée dans <dossier> par le workflow « Remplacer la vidéo du jour »),
                                              puis la renvoie sur Telegram avec Publier / Rejeter
Secrets : TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, UPLOAD_POST_API_KEY ; GH_TOKEN fourni par GitHub Actions.
"""
import os
import pathlib
import subprocess
import sys
import time

import linkedin
from commun import HISTORIQUE, JOURS, dossier_du_jour, ecrire_json, env, http, lire_json, multipart, tg, tg_message

UP = "https://api.upload-post.com/api"
PROFIL = os.environ.get("UPLOAD_POST_USER") or "default"
PAGE = os.environ.get("LINKEDIN_PAGE_ID") or "urn:li:organization:145361149"   # page Papercraft.AI


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def ranger(date, jour, noms=("final.mp4", "post.txt", "etude.json", "film.json", "faits.json")):
    fichiers = [str(jour / n) for n in noms if (jour / n).exists()]
    etude = lire_json(jour / "etude.json", {})
    try:
        gh("release", "view", f"jour-{date}")
        gh("release", "upload", f"jour-{date}", *fichiers, "--clobber")
    except subprocess.CalledProcessError:
        gh("release", "create", f"jour-{date}", *fichiers, "--title", f"{date} · {etude.get('titre', '')[:80]}",
           "--notes", f"En attente de validation.\n{etude.get('lien', '')}", "--prerelease")


def recuperer(date):
    jour = JOURS / date
    jour.mkdir(parents=True, exist_ok=True)
    if not (jour / "final.mp4").exists():
        gh("release", "download", f"jour-{date}", "--dir", str(jour), "--clobber", "-p", "final.mp4", "-p", "post.txt", "-p", "etude.json")
    return jour


def publier(date):
    """LinkedIn en direct (API officielle, gratuite) si l'accès est configuré ; Upload-Post en secours.
    Renvoie le canal utilisé (« LinkedIn » ou « Upload-Post »)."""
    jour = recuperer(date)
    post = (jour / "post.txt").read_text(encoding="utf-8").strip()
    titre = post.splitlines()[0][:150]
    erreur_li = None
    if linkedin.configure():
        try:
            pid = linkedin.publier(jour / "final.mp4", post, titre)
            print(f"publié sur LinkedIn en direct : {pid}")
            return "LinkedIn"
        except Exception as e:      # jeton expiré, accès refusé… : on tente le secours
            erreur_li = e
            print(f"LinkedIn direct impossible : {e}")
    if not os.environ.get("UPLOAD_POST_API_KEY", "").strip():
        raise RuntimeError(f"LinkedIn : {erreur_li}" if erreur_li else "ni accès LinkedIn ni clé Upload-Post")
    try:
        publier_upload_post(jour, post, titre)
    except Exception as e:
        raise RuntimeError(f"LinkedIn : {erreur_li} · Upload-Post : {e}" if erreur_li else str(e))
    return "Upload-Post"


def publier_upload_post(jour, post, titre):
    corps, ct = multipart([("user", PROFIL), ("platform[]", "linkedin"), ("title", titre), ("description", post),
                           ("target_linkedin_page_id", PAGE), ("async_upload", "true")], [("video", jour / "final.mp4")])
    cle = {"Authorization": f"Apikey {env('UPLOAD_POST_API_KEY')}"}
    r = http(f"{UP}/upload", corps, {**cle, "Content-Type": ct}, method="POST", timeout=600, essais=1)
    rid = r.get("request_id")
    if not rid:
        if r.get("success") and r.get("results"):
            return r
        raise RuntimeError(f"Upload-Post : réponse inattendue {str(r)[:300]}")
    for _ in range(60):
        time.sleep(10)
        s = http(f"{UP}/uploadposts/status?request_id={rid}", headers=cle)
        if s.get("status") in ("completed", "failed"):
            if s["status"] == "failed" or not all(x.get("success") for x in s.get("results", [{}])):
                raise RuntimeError(f"Upload-Post : échec {str(s)[:400]}")
            return s
    raise RuntimeError("Upload-Post : publication toujours en cours après 10 minutes")


def noter_historique(date, statut):
    h = lire_json(HISTORIQUE, [])
    etude = lire_json(JOURS / date / "etude.json", {})
    doi = (etude.get("doi") or "").lower()
    for e in h:
        if e.get("date") == date:
            # plusieurs runs le même jour : l'entrée suit l'étude envoyée en dernier, les précédentes restent exclues de la veille
            if doi and e.get("doi") and e["doi"] != doi:
                e["doi_ecartes"] = sorted(set(e.get("doi_ecartes", [])) | {e["doi"]})
                e["doi"], e["titre"] = doi, etude.get("titre", "")
            e["statut"] = statut
            break
    else:
        h.append({"date": date, "doi": doi, "titre": etude.get("titre", ""), "statut": statut})
    ecrire_json(HISTORIQUE, h)


def rappel_linkedin():
    """Le jeton LinkedIn vit 60 jours : le bot prévient sur Telegram dix jours avant, puis chaque jour."""
    try:
        j = linkedin.jours_restants()
    except Exception:
        return
    if j is not None and j <= 10:
        tg_message(f"🔑 L'accès LinkedIn du bot expire dans {j} jour(s). Sur le Mac : cd ~/ma-video/papercraft-push && "
                   "git pull && python3 pipeline/linkedin_connexion.py (deux minutes). Sans ça, la publication passera par "
                   "Upload-Post (10 par mois)." if j else
                   "🔑 L'accès LinkedIn du bot a expiré. Sur le Mac : cd ~/ma-video/papercraft-push && git pull && "
                   "python3 pipeline/linkedin_connexion.py")


def envoyer():
    rappel_linkedin()
    jour = dossier_du_jour()
    date = jour.name
    ranger(date, jour)
    noter_historique(date, "en attente")
    etude = lire_json(jour / "etude.json", {})
    if (os.environ.get("PUBLICATION_AUTO") or "").lower() == "oui":
        canal = publier(date)
        noter_historique(date, "publiée")
        tg("sendVideo", {"chat_id": env("TELEGRAM_CHAT_ID"), "caption": f"Publiée sur Papercraft.AI ({canal}) · {date}\n{etude.get('lien', '')}"[:1000],
                         "supports_streaming": "true"}, [("video", jour / "final.mp4")], timeout=600)
        return
    proposer(date, jour, f"Vidéo du {date}")


def proposer(date, jour, entete):
    etude = lire_json(jour / "etude.json", {})
    post = (jour / "post.txt").read_text(encoding="utf-8").strip()
    # ce que les contrôles automatiques ont vu, pour celui qui valide : la relecture indépendante et le contrôle d'images
    lignes = [entete, etude.get("titre", "")]
    rel, img = lire_json(jour / "relecture.json", {}) or {}, lire_json(jour / "images.json", {}) or {}
    if rel.get("verdict"):
        lignes.append(f"Relecture : {rel['verdict']}" + (f" ({rel['resume']})" if rel.get("resume") else ""))
    if img.get("bilan"):
        lignes.append(f"Images : {img['bilan']}")
    tg("sendVideo", {"chat_id": env("TELEGRAM_CHAT_ID"), "caption": "\n".join(lignes)[:1000],
                     "supports_streaming": "true"}, [("video", jour / "final.mp4")], timeout=600)
    clavier = {"inline_keyboard": [[{"text": "✅ Publier", "callback_data": f"pub:{date}"}, {"text": "❌ Rejeter", "callback_data": f"rej:{date}"}]]}
    tg_message(f"{post}\n\n— Texte du post. Publier sur la page Papercraft.AI ?", reply_markup=clavier)
    print("envoyé sur Telegram")


def remplacer(dossier):
    """La vidéo d'un essai (Essai DA, téléchargée dans <dossier>) devient la vidéo du jour : elle remplace celle de la
    release « jour-<date> », et le bouton Publier publiera donc celle-ci. Refuse un jour déjà publié, et un essai qui
    porte sur une autre étude sans apporter son propre post."""
    import json
    import shutil
    src = pathlib.Path(dossier)
    jour = dossier_du_jour()
    date = jour.name
    statut = next((e.get("statut") for e in lire_json(HISTORIQUE, []) if e.get("date") == date), None)
    if statut == "publiée":
        sys.exit(f"le {date} est déjà publié : rien n'est remplacé")
    if not (src / "final.mp4").exists() or not (src / "film.json").exists():
        sys.exit(f"l'essai doit contenir final.mp4 et film.json (trouvé : {sorted(x.name for x in src.iterdir())})")
    doi_jour = (lire_json(jour / "etude.json", {}).get("doi") or "").lower()
    film = json.loads((src / "film.json").read_text(encoding="utf-8"))
    doi_essai = (lire_json(src / "etude.json", {}).get("doi") or str(film.get("end", {}).get("doi", "")).replace("doi:", "")).strip().lower()
    if doi_essai != doi_jour and not ((src / "post.txt").exists() and (src / "etude.json").exists()):
        sys.exit(f"l'essai porte sur une autre étude ({doi_essai or '?'}) que celle du {date} ({doi_jour or '?'}) et n'apporte pas "
                 "son post.txt ni son etude.json : rien n'est remplacé")
    noms = []
    for n in ("final.mp4", "film.json", "post.txt", "etude.json", "faits.json"):
        if (src / n).exists():
            shutil.copy2(src / n, jour / n)
            noms.append(n)
    ranger(date, jour, noms)
    noter_historique(date, "en attente")
    proposer(date, jour, f"Vidéo du {date} · version corrigée (elle remplace la précédente : les deux boutons Publier publient celle-ci)")
    print(f"remplacée dans la release jour-{date} : {', '.join(noms)} (étude {doi_essai})")


def ecouter():
    moi = str(env("TELEGRAM_CHAT_ID"))
    maj = tg("getUpdates", {"timeout": 0, "allowed_updates": ["callback_query"]})
    dernier = None
    for u in maj:
        dernier = u["update_id"]
        q = u.get("callback_query")
        if not q or str(q["from"]["id"]) != moi:
            continue
        action, _, date = (q.get("data") or "").partition(":")
        msg = q.get("message", {})
        try:
            tg("answerCallbackQuery", {"callback_query_id": q["id"], "text": "Reçu, je m'en occupe."})
        except Exception:
            pass  # clic trop ancien : on traite quand même
        statut = next((e.get("statut") for e in lire_json(HISTORIQUE, []) if e.get("date") == date), None)
        if statut in ("publiée", "rejetée"):
            continue
        try:
            tg("editMessageReplyMarkup", {"chat_id": msg["chat"]["id"], "message_id": msg["message_id"], "reply_markup": {"inline_keyboard": []}})
        except Exception:
            pass
        if action == "pub":
            try:
                canal = publier(date)
                noter_historique(date, "publiée")
                gh("release", "edit", f"jour-{date}", "--prerelease=false", "--notes", f"Publiée sur LinkedIn (page Papercraft.AI, via {canal}).")
                tg_message(f"✅ Publiée sur la page Papercraft.AI ({date}, via {canal}).")
            except Exception as e:
                tg_message(f"⚠️ Publication du {date} impossible : {str(e)[:500]}\nRéessaie en recliquant plus tard ou préviens Claude.",
                           reply_markup={"inline_keyboard": [[{"text": "🔁 Réessayer", "callback_data": f"pub:{date}"}]]})
        elif action == "rej":
            noter_historique(date, "rejetée")
            tg_message(f"❌ Vidéo du {date} rejetée, rien n'est publié.")
    if dernier is not None:
        tg("getUpdates", {"offset": dernier + 1, "timeout": 0})


if __name__ == "__main__":
    {"envoyer": envoyer, "ecouter": ecouter, "remplacer": remplacer}[sys.argv[1]](*sys.argv[2:])
