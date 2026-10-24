#!/usr/bin/env python3
"""Cale la musique de série sur le film du jour : le « drop » de la musique tombe sur le pli du pivot,
puis la musique s'efface sous la voix (compression déclenchée par la voix).

Usage : python3 serie/moteur/musique.py <projet>
  lit  <projet>/film.resolu.json (écrit par build.py), <projet>/assets/audio/voix-montage.wav
  écrit <projet>/assets/audio/musique-calee.wav (durée du film), à passer à build-audio.sh :
  MUSIC=assets/audio/musique-calee.wav MUSIC_VOLUME=1.0
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TRACK = HERE.parent / "audio" / "papercraft-musique-v2.mp3"   # musique de série (ElevenLabs Music v2.5, 62 s, instrumentale)
DROP = 21.30          # premier coup de grosse caisse du morceau, en secondes
AFTER_FOLD = 0.30     # le drop tombe 0,3 s après le début du pli, quand le papier se découvre
LEVEL = 0.40          # niveau de la musique hors voix (≈ -25 LUFS) ; sous la voix, environ 8 dB de moins


def main(project):
    proj = pathlib.Path(project).resolve()
    film = json.loads((proj / "film.resolu.json").read_text(encoding="utf-8"))
    D = float(film["duration"])
    target = film["pivot"]["fold_at"] + AFTER_FOLD
    shift = target - DROP                      # > 0 : on retarde la musique ; < 0 : on entre plus loin dans le morceau
    voice = proj / "assets" / "audio" / "voix-montage.wav"
    out = proj / "assets" / "audio" / "musique-calee.wav"
    if shift >= 0:
        cue = f"adelay={int(round(shift * 1000))}|{int(round(shift * 1000))}"
    else:
        cue = f"atrim=start={-shift:.3f},asetpts=PTS-STARTPTS"
    graph = (f"[0]aformat=sample_rates=44100:channel_layouts=stereo,{cue},apad,atrim=0:{D:.3f},volume={LEVEL}[m];"
             f"[1]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[sc][vx];"
             f"[m][sc]sidechaincompress=threshold=0.03:ratio=5:attack=40:release=450:makeup=1[d];"
             f"[vx]anullsink")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(TRACK), "-i", str(voice), "-filter_complex", graph,
                    "-map", "[d]", "-t", f"{D:.3f}", str(out)], check=True)
    print(f"musique calée : {out.name} (drop du morceau à {DROP:.2f} s -> {target:.2f} s dans le film, décalage {shift:+.2f} s)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
