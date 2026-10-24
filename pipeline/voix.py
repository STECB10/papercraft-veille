#!/usr/bin/env python3
"""Voix du jour : 2 prises ElevenLabs (Léo), transcription Scribe, on garde la prise qui dit le texte mot pour mot.

Usage : python3 pipeline/voix.py        (lit jours/<date>/film.json, écrit jours/<date>/assets/audio/voix.mp3 et voix-mots-brut.json)
Secret : ELEVENLABS_API_KEY
"""
import difflib
import json
import sys

from commun import RACINE, dossier_du_jour, env, http, lire_json, multipart

VOIX = "AfbuxQ9DVtS4azaxN1W7"          # Léo, choisie par Steven le 24 octobre 2026
API = "https://api.elevenlabs.io/v1"
# Réglages du pilote Tanzanie (tonalité, naturel), retrouvés par pipeline/reglages_voix.py. Un seul modèle : pas de
# repli sur un autre modèle, qui changerait le timbre de Léo d'une vidéo à l'autre.
REGLAGES = lire_json(RACINE / "serie" / "audio" / "voix-leo.json", {}) or {}
MODELE = REGLAGES.get("model_id", "eleven_v4")
VOICE_SETTINGS = REGLAGES.get("voice_settings")


def norm(w):
    return w.replace("’", "'").strip(".,;:!?«»\"()…").lower()


def aligner(mots, texte_mots):
    """Aligne la transcription sur le script (difflib) : compte les vrais écarts sans effet de décalage,
    et rend un mot horodaté par mot du script (temps répartis sur les passages qui diffèrent)."""
    dits = [norm(w["w"]) for w in mots]
    attendu = [norm(w) for w in texte_mots]
    temps = [None] * len(attendu)
    ecarts, details = 0, []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, dits, attendu, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                temps[j1 + k] = (mots[i1 + k]["start"], mots[i1 + k]["end"])
            continue
        ecarts += max(i2 - i1, j2 - j1)
        details.append(f"dit « {' '.join(dits[i1:i2])} » / attendu « {' '.join(attendu[j1:j2])} »")
        if i2 > i1:
            t0, t1 = mots[i1]["start"], mots[i2 - 1]["end"]
        else:
            t0 = mots[i1 - 1]["end"] if i1 > 0 else 0.0
            t1 = mots[i1]["start"] if i1 < len(mots) else t0
        n = j2 - j1
        for k in range(n):
            temps[j1 + k] = (t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n)
    alignes = [{"w": t, "start": a, "end": b} for t, (a, b) in zip(texte_mots, temps)]
    return ecarts, details, alignes


def tts(texte, cle, graine):
    body = {"text": texte, "model_id": MODELE, "language_code": "fr", "seed": graine}
    if VOICE_SETTINGS:
        body["voice_settings"] = VOICE_SETTINGS
    try:
        return http(f"{API}/text-to-speech/{VOIX}?output_format=mp3_44100_128", body,
                    {"xi-api-key": cle, "Accept": "audio/mpeg"}, method="POST", timeout=300, brut=True), MODELE
    except RuntimeError as e:
        raise SystemExit(f"voix : le modèle {MODELE} de Léo a refusé ({str(e)[:200]})")


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
    texte_mots = [w for s in film["sentences"] for w in s["text"].split()]
    tolerance = max(3, len(texte_mots) // 20)          # 5 % des mots, au moins 3
    a = jour / "assets" / "audio"
    a.mkdir(parents=True, exist_ok=True)
    meilleure = None
    for k, graine in enumerate((11, 29), start=1):
        mp3, modele = tts(texte, cle, graine)
        p = a / f"prise{k}.mp3"
        p.write_bytes(mp3)
        ecarts, details, alignes = aligner(scribe(p, cle), texte_mots)
        print(f"prise {k} ({modele}) : {ecarts} écart(s) réel(s) sur {len(texte_mots)} mots (tolérance {tolerance})")
        for d in details[:15]:
            print(f"   {d}")
        if meilleure is None or ecarts < meilleure[0]:
            meilleure = (ecarts, p, alignes, modele)
        if ecarts == 0:
            break
    ecarts, p, mots, modele = meilleure
    if ecarts > tolerance:
        raise SystemExit(f"voix : aucune prise ne colle au texte ({ecarts} écarts réels, tolérance {tolerance})")
    if ecarts:
        print(f"voix : {ecarts} variante(s) de transcription recalée(s) sur le script")
    (a / "voix.mp3").write_bytes(p.read_bytes())
    (a / "voix-mots-brut.json").write_text(json.dumps({"source": f"ElevenLabs {modele}, voix Léo, réglages {VOICE_SETTINGS or 'par défaut'}, Scribe v1", "words": mots},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"voix : {p.name} retenue")


if __name__ == "__main__":
    main()
