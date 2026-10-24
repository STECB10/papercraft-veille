#!/usr/bin/env python3
"""Voix du jour : 2 prises ElevenLabs (Léo), transcription Scribe, on garde la prise qui dit le texte mot pour mot.

Usage : python3 pipeline/voix.py        (lit jours/<date>/film.json, écrit jours/<date>/assets/audio/voix.mp3 et voix-mots-brut.json)
Secret : ELEVENLABS_API_KEY
"""
import json
import sys

from commun import dossier_du_jour, env, http, lire_json, multipart

VOIX = "AfbuxQ9DVtS4azaxN1W7"          # Léo, choisie par Steven le 24 octobre 2026
MODELES = ["eleven_v4", "eleven_v3", "eleven_multilingual_v2"]
API = "https://api.elevenlabs.io/v1"


def norm(w):
    return w.replace("’", "'").strip(".,;:!?«»\"()…").lower()


def tts(texte, cle, graine):
    err = None
    for m in MODELES:
        try:
            body = {"text": texte, "model_id": m, "language_code": "fr", "seed": graine}
            return http(f"{API}/text-to-speech/{VOIX}?output_format=mp3_44100_128", body,
                        {"xi-api-key": cle, "Accept": "audio/mpeg"}, method="POST", timeout=300, brut=True), m
        except RuntimeError as e:
            err = e
            print(f"modèle {m} refusé : {str(e)[:160]}")
    raise SystemExit(f"voix : aucun modèle n'a fonctionné ({err})")


def scribe(chemin, cle):
    corps, ct = multipart([("model_id", "scribe_v1"), ("language_code", "fra"), ("timestamps_granularity", "word"),
                           ("tag_audio_events", "false")], [("file", chemin)])
    r = http(f"{API}/speech-to-text", corps, {"xi-api-key": cle, "Content-Type": ct}, method="POST", timeout=300)
    return [{"w": w["text"], "start": float(w["start"]), "end": float(w["end"])} for w in r.get("words", []) if w.get("type") == "word"]


def main():
    jour = dossier_du_jour()
    cle = env("ELEVENLABS_API_KEY")
    film = lire_json(jour / "film.json")
    texte = "\n".join(s["text"] for s in film["sentences"])
    attendu = [norm(w) for s in film["sentences"] for w in s["text"].split()]
    a = jour / "assets" / "audio"
    a.mkdir(parents=True, exist_ok=True)
    meilleure = None
    for k, graine in enumerate((11, 29), start=1):
        mp3, modele = tts(texte, cle, graine)
        p = a / f"prise{k}.mp3"
        p.write_bytes(mp3)
        mots = scribe(p, cle)
        dits = [norm(w["w"]) for w in mots]
        ecarts = sum(1 for x, y in zip(dits, attendu) if x != y) + abs(len(dits) - len(attendu))
        print(f"prise {k} ({modele}) : {len(dits)} mots, {ecarts} écart(s) avec le texte")
        if meilleure is None or ecarts < meilleure[0]:
            meilleure = (ecarts, p, mots, modele)
        if ecarts == 0:
            break
    ecarts, p, mots, modele = meilleure
    if ecarts:
        if len(mots) != len(attendu) or ecarts > 3:
            raise SystemExit(f"voix : aucune prise ne colle au texte ({ecarts} écarts, {len(mots)} mots contre {len(attendu)})")
        # même nombre de mots, petites variantes de transcription : on garde les temps, on remet le texte du script
        texte_mots = [w for s in film["sentences"] for w in s["text"].split()]
        for w, t in zip(mots, texte_mots):
            w["w"] = t
        print(f"voix : {ecarts} variante(s) de transcription corrigée(s) d'après le script")
    (a / "voix.mp3").write_bytes(p.read_bytes())
    (a / "voix-mots-brut.json").write_text(json.dumps({"source": f"ElevenLabs {modele}, voix Léo, Scribe v1", "words": mots},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"voix : {p.name} retenue")


if __name__ == "__main__":
    main()
