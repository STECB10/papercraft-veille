#!/usr/bin/env python3
"""Envoi pour validation sur Telegram, publication LinkedIn (via Upload-Post) et écoute des boutons.

  python3 pipeline/publication.py envoyer     après fabriquer.py : range la vidéo (release GitHub « jour-<date> »),
                                              puis l'envoie sur Telegram avec Publier / Rejeter
                                              (ou publie directement si la variable PUBLICATION_AUTO vaut « oui »)
  python3 pipeline/publication.py ecouter     lit les clics Telegram et publie / rejette (lancé toutes les 30 min)
Secrets : TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, UPLOAD_POST_API_KEY ; GH_TOKEN fourni par GitHub Actions.
"""
import os
import subprocess
import sys
import time

from commun import HISTORIQUE, JOURS, dossier_du_jour, ecrire_json, env, http, lire_json, multipart, tg, tg_message

UP = "https://api.upload-post.com/api"
PROFIL = os.environ.get("UPLOAD_POST_USER") or "default"
PAGE = os.environ.get("LINKEDIN_PAGE_ID") or "urn:li:organization:145361149"   # page Papercraft.AI


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def ranger(date, jour):
    fichiers = [str(jour / n) for n in ("final.mp4", "post.txt", "etude.json", "film.json", "faits.json") if (jour / n).exists()]
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
    jour = recuperer(date)
    post = (jour / "post.txt").read_text(encoding="utf-8").strip()
    titre = post.splitlines()[0][:150]
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
    for e in h:
        if e.get("date") == date:
            e["statut"] = statut
            break
    else:
        h.append({"date": date, "doi": (etude.get("doi") or "").lower(), "titre": etude.get("titre", ""), "statut": statut})
    ecrire_json(HISTORIQUE, h)


def envoyer():
    jour = dossier_du_jour()
    date = jour.name
    ranger(date, jour)
    noter_historique(date, "en attente")
    etude = lire_json(jour / "etude.json", {})
    post = (jour / "post.txt").read_text(encoding="utf-8").strip()
    if (os.environ.get("PUBLICATION_AUTO") or "").lower() == "oui":
        publier(date)
        noter_historique(date, "publiée")
        tg("sendVideo", {"chat_id": env("TELEGRAM_CHAT_ID"), "caption": f"Publiée sur Papercraft.AI · {date}\n{etude.get('lien', '')}"[:1000],
                         "supports_streaming": "true"}, [("video", jour / "final.mp4")], timeout=600)
        return
    tg("sendVideo", {"chat_id": env("TELEGRAM_CHAT_ID"), "caption": f"Vidéo du {date}\n{etude.get('titre', '')}"[:1000],
                     "supports_streaming": "true"}, [("video", jour / "final.mp4")], timeout=600)
    clavier = {"inline_keyboard": [[{"text": "✅ Publier", "callback_data": f"pub:{date}"}, {"text": "❌ Rejeter", "callback_data": f"rej:{date}"}]]}
    tg_message(f"{post}\n\n— Texte du post. Publier sur la page Papercraft.AI ?", reply_markup=clavier)
    print("envoyé sur Telegram")


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
                publier(date)
                noter_historique(date, "publiée")
                gh("release", "edit", f"jour-{date}", "--prerelease=false", "--notes", "Publiée sur LinkedIn (page Papercraft.AI).")
                tg_message(f"✅ Publiée sur la page Papercraft.AI ({date}).")
            except Exception as e:
                tg_message(f"⚠️ Publication du {date} impossible : {str(e)[:500]}\nRéessaie en recliquant plus tard ou préviens Claude.",
                           reply_markup={"inline_keyboard": [[{"text": "🔁 Réessayer", "callback_data": f"pub:{date}"}]]})
        elif action == "rej":
            noter_historique(date, "rejetée")
            tg_message(f"❌ Vidéo du {date} rejetée, rien n'est publié.")
    if dernier is not None:
        tg("getUpdates", {"offset": dernier + 1, "timeout": 0})


if __name__ == "__main__":
    {"envoyer": envoyer, "ecouter": ecouter}[sys.argv[1]]()
