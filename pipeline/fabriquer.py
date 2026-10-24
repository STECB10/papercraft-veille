#!/usr/bin/env python3
"""Fabrique la vidéo du jour une fois film.json validé : voix, montage, animation, musique, mixage, rendu, contrôles.

Usage : python3 pipeline/fabriquer.py          -> jours/<date>/final.mp4 (moins de 48 Mo, prêt pour Telegram et LinkedIn)
"""
import json
import os
import re
import shutil
import subprocess
import sys

from commun import RACINE, dossier_du_jour, lire_json

MOTEUR = RACINE / "serie" / "moteur"
ENV = dict(os.environ, HYPERFRAMES_NO_TELEMETRY="1", DO_NOT_TRACK="1", HYPERFRAMES_SKIP_SKILLS="1", HYPERFRAMES_NO_UPDATE_CHECK="1")


def run(*cmd, **kw):
    print("→", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, env=ENV, **kw)


def mesure(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, env=ENV).stderr


def controles(jour, mp4, duree):
    err = []
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(mp4)],
                         capture_output=True, text=True).stdout
    info = json.loads(out)
    types = [s["codec_type"] for s in info["streams"]]
    if "audio" not in types or "video" not in types:
        err.append(f"flux manquant : {types}")
    d = float(info["format"]["duration"])
    if abs(d - duree) > 0.15:
        err.append(f"durée {d:.2f} s au lieu de {duree:.2f} s")
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    if (v["width"], v["height"]) != (1080, 1350):
        err.append(f"format {v['width']}x{v['height']}")
    noir = sum(float(x) for x in re.findall(r"black_duration:([\d.]+)", mesure(["ffmpeg", "-hide_banner", "-i", str(mp4), "-vf", "blackdetect=d=0.6:pix_th=0.08", "-an", "-f", "null", "-"])))
    if noir > 3.2:
        err.append(f"{noir:.1f} s d'écran noir (3,2 s au plus : le pivot)")
    gel = re.findall(r"freeze_duration: ([\d.]+)", mesure(["ffmpeg", "-hide_banner", "-i", str(mp4), "-vf", "freezedetect=n=0.002:d=2.5", "-an", "-f", "null", "-"]))
    if gel:
        err.append(f"image figée {', '.join(gel)} s")
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", mesure(["ffmpeg", "-hide_banner", "-i", str(mp4), "-vn", "-af", "ebur128", "-f", "null", "-"]))
    if not lufs or abs(float(lufs[-1]) + 16) > 1.5:
        err.append(f"volume {lufs[-1] if lufs else '?'} LUFS (attendu -16)")
    taille = mp4.stat().st_size / 1e6
    if taille > 48:
        err.append(f"fichier de {taille:.0f} Mo (48 au plus pour Telegram)")
    return err


def main():
    jour = dossier_du_jour()
    # projet HyperFrames du jour : gabarit (polices, GSAP local, réglages) + son
    for p in (RACINE / "serie" / "gabarit").rglob("*"):
        if p.is_file():
            dest = jour / p.relative_to(RACINE / "serie" / "gabarit")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
    (jour / "meta.json").write_text(json.dumps({"id": jour.name, "name": jour.name, "width": 1080, "height": 1350, "fps": 30}), encoding="utf-8")
    py = sys.executable
    if not (jour / "assets" / "audio" / "voix.mp3").exists():
        run(py, RACINE / "pipeline" / "voix.py")
    run(py, MOTEUR / "audio.py", "montage", jour)
    run(py, MOTEUR / "build.py", jour)
    run(py, MOTEUR / "musique.py", jour)
    run(py, MOTEUR / "audio.py", "mix", jour)
    run(py, MOTEUR / "normaliser.py", jour)
    rendu = jour / "renders" / "rendu.mp4"
    rendu.parent.mkdir(exist_ok=True)
    run("npx", "hyperframes", "render", jour, "--workers", "auto", "--quiet", "--output", rendu, cwd=RACINE)
    duree = float(lire_json(jour / "film.json")["duration"])
    final = jour / "final.mp4"
    for crf in (19, 22, 25):
        run("ffmpeg", "-v", "error", "-y", "-i", rendu, "-i", jour / "assets" / "audio" / "mix.wav", "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", "-t", f"{duree:.3f}", final)
        if final.stat().st_size < 48e6:
            break
    err = controles(jour, final, duree)
    if err:
        raise SystemExit("contrôles refusés :\n- " + "\n- ".join(err))
    print(f"vidéo prête : {final} ({final.stat().st_size / 1e6:.1f} Mo, {duree:.1f} s), contrôles OK")


if __name__ == "__main__":
    main()
