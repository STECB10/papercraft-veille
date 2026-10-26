#!/usr/bin/env python3
"""Banc d'essai du moteur, sans voix réelle : rejoue un film.json avec des temps de parole simulés et sort une planche
contact des moments clés (une image par planche, une fois l'animation posée).

Usage : python3 serie/moteur/essai.py <film.json ou dossier du jour> <dossier de sortie> [--video]
  --video : rend aussi la vidéo muette avec HyperFrames (plus long)
Sert à vérifier une planche ou une modification du moteur avant de lancer la vraie chaîne (voix ElevenLabs).
Nécessite Playwright (Chromium) pour les images.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys

RACINE = pathlib.Path(__file__).resolve().parents[2]
MOTEUR = RACINE / "serie" / "moteur"


def faux_mots(film):
    """Débit d'environ 2,7 mots par seconde, silences de fin de phrase et pauses voulues (pause_apres)."""
    mots, t = [], 0.35
    for s in film["sentences"]:
        for w in s["text"].split():
            d = 0.12 + 0.045 * len(w)
            mots.append({"w": w, "s": round(t, 3), "e": round(t + d, 3)})
            t += d + 0.06
        t += 0.32 + float(s.get("pause_apres", 0) or 0)
    return mots, round(t + 3.6, 1)


def main():
    src = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2]).resolve()
    video = "--video" in sys.argv
    film_path = src / "film.json" if src.is_dir() else src
    out.mkdir(parents=True, exist_ok=True)
    for p in (RACINE / "serie" / "gabarit").rglob("*"):
        if p.is_file():
            d = out / p.relative_to(RACINE / "serie" / "gabarit")
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, d)
    film = json.loads(film_path.read_text(encoding="utf-8"))
    mots, duree = faux_mots(film)
    (out / "onsets.json").write_text(json.dumps({"words": mots}, ensure_ascii=False), encoding="utf-8")
    film.update(duration=duree, words_file="onsets.json", audio="assets/audio/mix.wav")
    (out / "film.json").write_text(json.dumps(film, ensure_ascii=False, indent=1), encoding="utf-8")
    a = out / "assets" / "audio"
    a.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(duree), str(a / "mix.wav")], check=True)
    (out / "meta.json").write_text(json.dumps({"id": "essai", "name": "essai", "width": 1080, "height": 1350, "fps": 30}), encoding="utf-8")
    subprocess.run([sys.executable, str(MOTEUR / "build.py"), str(out)], check=True)
    res = json.loads((out / "film.resolu.json").read_text(encoding="utf-8"))
    # moments clés : chaque planche une fois posée (juste avant la suivante), le pivot, la déchirure, la fin
    temps = []
    sts = res["night"]["stations"]
    for i, st in enumerate(sts):
        nxt = sts[i + 1]["cam_at"] if i + 1 < len(sts) else res["night"]["end"]
        temps.append((f"table · {st['type']}", round(nxt - 0.15, 2)))
    temps.append(("pivot", round(res["pivot"]["fold_at"] - 0.2, 2)))
    sts = res["paper"]["stations"]
    first_typo = next((i for i, s in enumerate(sts) if s["type"] == "typo" and i > 0), None)
    for i, st in enumerate(sts):
        nxt = sts[i + 1]["cam_at"] if i + 1 < len(sts) else res["end"]["fold_at"]
        if first_typo is not None and i + 1 == first_typo:
            nxt -= 0.45
        temps.append((st["type"], round(nxt - 0.15, 2)))
        if st["type"] == "typo" and i > 0 and not any(s["type"] == "typo" for s in sts[:i]):
            temps.append(("déchirure", round(st["cam_at"] - 0.45 + 0.55, 2)))
    temps.append(("fin", round(res["duration"] - 0.3, 2)))
    (out / "moments.json").write_text(json.dumps(temps, ensure_ascii=False), encoding="utf-8")
    env = dict(os.environ)
    try:
        env.setdefault("NODE_PATH", subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip())
    except OSError:
        pass
    subprocess.run(["node", str(MOTEUR / "essai_images.mjs"), str(out)], check=True, env=env)
    if video:
        subprocess.run(["npx", "hyperframes", "render", str(out), "--workers", "auto", "--quiet", "--output", str(out / "essai.mp4")], check=True, cwd=RACINE)
    print(f"essai : {out / 'planche.png'}")


if __name__ == "__main__":
    main()
