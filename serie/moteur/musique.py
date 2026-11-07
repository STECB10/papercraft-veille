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
LEVEL = 0.48          # niveau de la musique hors voix (≈ -23,5 LUFS) ; sous la voix (normalisée à -16 LUFS), environ 17 LU plus bas
XFADE = 3.0           # fondu enchaîné quand une partie du morceau est rejouée
BOUCLE = 16.0         # avant le drop : on rejoue les 16 dernières secondes de l'intro autant qu'il faut
# Retour du 7 novembre 2026 : la musique commençait en retard (les scripts plus longs reculent le pivot : le morceau était
# retardé d'autant) et couvrait la voix. Désormais elle part dès la première image : si le drop doit tomber plus tard que
# dans le morceau, l'intro est rallongée (la fin de l'intro rejouée en fondu enchaîné) au lieu de retarder le départ.


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
    # avant le drop : l'intro, plus n fois la fin de l'intro (fondu enchaîné), pour que le drop tombe au pivot
    # alors que la musique a commencé à la première image
    p0 = max(0.0, drop - BOUCLE)
    pas = max(1.0, (drop - p0) - XFADE)
    n_pre = max(0, math.ceil((target - drop) / pas)) if target > drop else 0
    drop2 = drop + n_pre * pas                 # où tombe le drop dans le morceau rallongé
    shift = target - drop2                     # <= 0 : on entre un peu plus loin dans le morceau rallongé
    # après le drop : la suite rejouée en fondu enchaîné tant qu'il le faut pour couvrir tout le film
    besoin = D - shift                         # durée du morceau rallongé nécessaire
    long_pre = drop2 + (L - drop)
    reprises = max(0, math.ceil((besoin - long_pre) / max(1.0, L - drop - XFADE))) if besoin > long_pre else 0
    voice = proj / "assets" / "audio" / "voix-montage.wav"
    out = proj / "assets" / "audio" / "musique-calee.wav"
    source = track
    if n_pre or reprises:
        source = proj / "assets" / "audio" / "musique-longue.wav"
        segs = [(0.0, drop)] + [(p0, drop)] * n_pre      # l'intro, puis la fin de l'intro rejouée
        inputs = sum((["-i", str(track)] for _ in range(len(segs) + 1 + reprises)), [])
        parts, cur = [], None
        for k, (a0, a1) in enumerate(segs):
            parts.append(f"[{k}]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start={a0:.3f}:end={a1:.3f},asetpts=PTS-STARTPTS[p{k}]")
            if cur is None:
                cur = f"p{k}"
            else:
                parts.append(f"[{cur}][p{k}]acrossfade=d={XFADE}[q{k}]")
                cur = f"q{k}"
        k = len(segs)
        # la suite du drop se colle sans fondu : la fin de l'intro et le drop se suivent dans le morceau d'origine
        parts.append(f"[{k}]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start={drop:.3f},asetpts=PTS-STARTPTS[t0]")
        parts.append(f"[{cur}][t0]concat=n=2:v=0:a=1[c0]")
        cur = "c0"
        for r in range(1, reprises + 1):
            parts.append(f"[{k + r}]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start={drop:.3f},asetpts=PTS-STARTPTS[r{r}]")
            parts.append(f"[{cur}][r{r}]acrossfade=d={XFADE}[s{r}]")
            cur = f"s{r}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-nostdin", *inputs, "-filter_complex", ";".join(parts), "-map", f"[{cur}]", str(source)], check=True)
    cue = f"atrim=start={-shift:.3f},asetpts=PTS-STARTPTS" if shift < 0 else "anull"
    # la musique s'efface sous la voix (voix normalisée à -16 LUFS au montage, donc toujours le même effacement)
    graph = (f"[0]aformat=sample_rates=44100:channel_layouts=stereo,{cue},apad,atrim=0:{D:.3f},volume={LEVEL}[m];"
             f"[1]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[sc][vx];"
             f"[m][sc]sidechaincompress=threshold=0.03:ratio=2.5:attack=25:release=600:makeup=1[d];"
             f"[vx]anullsink")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-i", str(voice), "-filter_complex", graph,
                    "-map", "[d]", "-t", f"{D:.3f}", str(out)], check=True)
    print(f"musique calée : {m['fichier']} ({m.get('titre', '')}), départ à la première image, drop à {drop:.2f} s -> {target:.2f} s "
          f"dans le film (intro rallongée {n_pre} fois), partie après le drop rejouée {reprises} fois")


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
