#!/usr/bin/env python3
"""Cale la musique du jour sur le film : le « drop » du morceau tombe sur le pli du pivot,
puis la musique s'efface sous la voix (compression déclenchée par la voix).

Usage : python3 serie/moteur/musique.py <projet>
  lit  serie/audio/musiques.json (le stock de morceaux), <projet>/film.resolu.json (écrit par build.py),
       <projet>/assets/audio/voix-montage.wav
  écrit <projet>/assets/audio/musique-calee.wav (durée du film)
       python3 serie/moteur/musique.py drop <morceau.mp3>   repère le drop d'un nouveau morceau (à noter dans musiques.json)

Le morceau change chaque jour (rotation dans le stock, d'après la date du projet). S'il est plus court que le film,
la partie après le drop est rejouée en fondu enchaîné : la musique ne s'arrête jamais avant la fin.
"""
import datetime
import json
import math
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUDIO = HERE.parent / "audio"
STOCK = AUDIO / "musiques.json"
AFTER_FOLD = 0.30     # le drop tombe 0,3 s après le début du pli, quand le papier se découvre
LEVEL = 0.40          # niveau de la musique hors voix (≈ -25 LUFS) ; sous la voix, environ 8 dB de moins
XFADE = 3.0           # fondu enchaîné quand la partie après le drop est rejouée


def duree(chemin):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(chemin)],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def morceau_du_jour(proj):
    stock = json.loads(STOCK.read_text(encoding="utf-8"))
    try:
        jour = datetime.date.fromisoformat(proj.name).toordinal()
    except ValueError:
        jour = 0
    return stock[jour % len(stock)]


def main(project):
    proj = pathlib.Path(project).resolve()
    film = json.loads((proj / "film.resolu.json").read_text(encoding="utf-8"))
    m = morceau_du_jour(proj)
    track, drop = AUDIO / m["fichier"], float(m["drop"])
    L = duree(track)
    D = float(film["duration"])
    target = film["pivot"]["fold_at"] + AFTER_FOLD
    shift = target - drop                      # > 0 : on retarde la musique ; < 0 : on entre plus loin dans le morceau
    # combien de fois rejouer la partie après le drop pour couvrir tout le film
    besoin = D - shift
    reprises = max(0, math.ceil((besoin - L) / max(1.0, L - drop - XFADE))) if besoin > L else 0
    voice = proj / "assets" / "audio" / "voix-montage.wav"
    out = proj / "assets" / "audio" / "musique-calee.wav"
    source = track
    if reprises:
        # 1er passage : le morceau rallongé (la partie après le drop rejouée en fondu enchaîné), dans un fichier à part
        source = proj / "assets" / "audio" / "musique-longue.wav"
        inputs = sum((["-i", str(track)] for _ in range(reprises + 1)), [])
        parts = ["[0]aformat=sample_rates=44100:channel_layouts=stereo[s0]"]
        cur = "s0"
        for k in range(1, reprises + 1):
            parts.append(f"[{k}]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start={drop:.3f},asetpts=PTS-STARTPTS[r{k}]")
            parts.append(f"[{cur}][r{k}]acrossfade=d={XFADE}[s{k}]")
            cur = f"s{k}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(parts), "-map", f"[{cur}]", str(source)], check=True)
    if shift >= 0:
        cue = f"adelay={int(round(shift * 1000))}|{int(round(shift * 1000))}"
    else:
        cue = f"atrim=start={-shift:.3f},asetpts=PTS-STARTPTS"
    graph = (f"[0]aformat=sample_rates=44100:channel_layouts=stereo,{cue},apad,atrim=0:{D:.3f},volume={LEVEL}[m];"
             f"[1]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[sc][vx];"
             f"[m][sc]sidechaincompress=threshold=0.03:ratio=5:attack=40:release=450:makeup=1[d];"
             f"[vx]anullsink")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-i", str(voice), "-filter_complex", graph,
                    "-map", "[d]", "-t", f"{D:.3f}", str(out)], check=True)
    print(f"musique calée : {m['fichier']} ({m.get('titre', '')}), drop à {drop:.2f} s -> {target:.2f} s dans le film, "
          f"décalage {shift:+.2f} s, partie après le drop rejouée {reprises} fois")


def reperer_drop(chemin):
    """Le drop : le moment où les graves (sous 160 Hz) passent durablement au-dessus du double de l'intro."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(chemin), "-af", "lowpass=f=160,aresample=8000", "-ac", "1",
                          "-f", "s16le", "-"], check=True, capture_output=True).stdout
    import array
    a = array.array("h", raw)
    win = 800                                   # 0,1 s à 8 kHz
    rms = [math.sqrt(sum(x * x for x in a[i:i + win]) / win) for i in range(0, len(a) - win, win)]
    intro = sorted(rms[20:80])[len(rms[20:80]) // 2] if len(rms) > 80 else 1
    for i in range(80, len(rms) - 10):
        if all(r > 2.2 * intro for r in rms[i:i + 10]):
            print(f"drop vers {i / 10:.2f} s")
            return i / 10
    print("aucun drop net trouvé : écouter et noter le moment à la main")
    return None


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "drop":
        reperer_drop(sys.argv[2])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else ".")
