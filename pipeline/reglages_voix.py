#!/usr/bin/env python3
"""Retrouve dans l'historique ElevenLabs les réglages exacts de la voix Léo du pilote Tanzanie
(modèle, stabilité, similarité, style, vitesse…) et les fige dans serie/audio/voix-leo.json.
voix.py les réutilise ensuite à chaque vidéo, pour garder la même tonalité et le même naturel.

Usage : ELEVENLABS_API_KEY=… python3 pipeline/reglages_voix.py [mot-du-texte] [--id <history_item_id>]
        (par défaut, cherche la génération la plus récente dont le texte contient « Tanzanie »)
"""
import datetime as dt
import json
import sys

from commun import RACINE, env, http

VOIX = "AfbuxQ9DVtS4azaxN1W7"          # Léo
API = "https://api.elevenlabs.io/v1"
SORTIE = RACINE / "serie" / "audio" / "voix-leo.json"


def main():
    args = sys.argv[1:]
    choix = args[args.index("--id") + 1] if "--id" in args else None
    mot = next((a for a in args if not a.startswith("--") and a != choix), "Tanzanie")
    cle = env("ELEVENLABS_API_KEY")
    items, apres = [], None
    for _ in range(20):
        url = f"{API}/history?page_size=1000&voice_id={VOIX}" + (f"&start_after_history_item_id={apres}" if apres else "")
        r = http(url, headers={"xi-api-key": cle})
        items += r.get("history", [])
        if not r.get("has_more"):
            break
        apres = r.get("last_history_item_id")
    if choix:
        trouves = [i for i in items if i.get("history_item_id") == choix]
    else:
        trouves = [i for i in items if mot.lower() in (i.get("text") or "").lower()]
    if not trouves:
        sys.exit(f"aucune génération de Léo contenant « {mot} » dans l'historique ({len(items)} générations lues)")
    trouves.sort(key=lambda i: i.get("date_unix", 0), reverse=True)
    for i in trouves[:10]:
        date = dt.datetime.fromtimestamp(i.get("date_unix", 0)).strftime("%Y-%m-%d %H:%M")
        print(f"{i['history_item_id']}  {date}  {i.get('model_id')}  {json.dumps(i.get('settings'), ensure_ascii=False)}  « {(i.get('text') or '')[:60]}… »")
    g = trouves[0]
    reglages = {k: v for k, v in (g.get("settings") or {}).items() if v is not None}
    out = {"voix": VOIX, "model_id": g.get("model_id") or "eleven_v4", "voice_settings": reglages,
           "source": f"historique ElevenLabs, génération {g['history_item_id']} du "
                     f"{dt.datetime.fromtimestamp(g.get('date_unix', 0)).strftime('%Y-%m-%d')} (pilote Tanzanie)"}
    SORTIE.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nréglages figés dans {SORTIE.relative_to(RACINE)} :\n{json.dumps(out, ensure_ascii=False, indent=1)}")


if __name__ == "__main__":
    main()
