#!/usr/bin/env python3
"""Son du film : montage de la voix (silences voulus), repères de mots, mixage final.

  python3 serie/moteur/audio.py montage <projet>   voix.mp3 + voix-mots-brut.json + film.json
        -> voix-montage.wav, onsets.json, et film.json["duration"] mis à jour
  python3 serie/moteur/audio.py mix <projet>       voix-montage.wav + musique-calee.wav + sfx-events.json -> mix.wav

Silences voulus : chaque phrase de film.json peut porter "pause_apres" (secondes ajoutées au milieu du silence qui
la suit). Usage de la série : 2,5 s pour le moment muet, 1,4 s après la phrase du pivot, 0,3 s avant la promesse.
Entrée : LEAD secondes de silence avant le premier mot (les lecteurs mangent souvent le tout début d'une vidéo) ;
film.json["lead"] le dit à build.py, qui y cale aussi les temps écrits en chiffres (0 = la voix commence).
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SFX_DIR = HERE.parent / "audio" / "sfx"
TAIL = 3.6
LEAD = 0.8
DEBIT = 0.77      # voix Brick : un mot dure 0,77 × l'estimation de base du banc d'essai (calé sur la vraie voix, 8 novembre 2026)
VOIX_LUFS = -16.0     # la voix est mise à ce niveau avant tout (montage) : la musique et les bruitages se règlent par rapport à elle
# bruitages : chaque fichier est d'abord ramené à un même niveau (mesures ci-dessous, ebur128), puis placé selon le volume
# demandé par build.py : un volume de 0,2 donne SFX_REF LUFS, 16 LU sous la voix (retour du 7 novembre 2026 : bruitages et
# musique trop forts, voix trop basse).
SFX_REF = -32.0
SFX_MAX = -29.0
SFX_LUFS = {"chime": -28.0, "click": -20.0, "impact-bass-1": -6.5, "notification": -19.3, "papier-dechire": -9.7, "papier-pli": -19.1,
            "papier-pose": -19.5, "ping": -25.4, "pop": -21.3, "whoosh-cinematic": -14.1, "whoosh-short": -15.2}


def lead_for(film):
    """Silence avant le premier mot. Avec la couverture (première image), le temps de la lire : 2,8 à 3,6 s selon la
    longueur de son texte (la couverture reste ~2,4 à 3,2 s, puis se soulève) ; sinon 0,8 s (les lecteurs mangent souvent le tout début d'une vidéo)."""
    sts = film.get("night", {}).get("stations", [])
    if not film.get("couverture", True) or not sts or not str(sts[0].get("type", "")).startswith("hook_"):
        return LEAD
    h = sts[0]
    t = h["type"]
    texte = {"hook_number": f"{h.get('number', '')} {h.get('unit', '')} {h.get('caption', '')}",
             "hook_question": h.get("text") or (film.get("sentences") or [{"text": ""}])[0]["text"],
             "hook_image": h.get("title", ""), "hook_headline": h.get("headline", ""),
             "hook_versus": f"{(h.get('left') or {}).get('label', '')} {(h.get('right') or {}).get('label', '')} {h.get('caption', '')}"}.get(t, "")
    mots = len(texte.split())
    return round(min(3.6, max(2.8, 1.9 + 0.1 * mots)), 2)


def niveau(path):
    """Intensité intégrée (LUFS) d'un fichier son."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    vals = [float(l.split("I:")[1].split("LUFS")[0]) for l in err.splitlines() if "I:" in l and "LUFS" in l]
    return vals[-1] if vals else -70.0


def normaliser_voix(path):
    """La voix devant : légère compression (niveau régulier d'une phrase à l'autre), puis gain linéaire jusqu'à VOIX_LUFS,
    crêtes limitées. Rien ne bouge dans le temps (les repères de mots restent valables)."""
    tmp = path.with_name("voix-norm-tmp.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-i", str(path), "-af",
                    "highpass=f=70,acompressor=threshold=0.08:ratio=2.5:attack=8:release=180:makeup=1", str(tmp)], check=True)
    gain = VOIX_LUFS - niveau(tmp)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-i", str(tmp), "-af",
                    f"volume={gain:.2f}dB,alimiter=limit=0.89:attack=3:release=60:level=disabled", "-ar", "44100", "-ac", "1", str(path)], check=True)
    tmp.unlink(missing_ok=True)
    return gain


def norm(w):
    return w.replace("’", "'").strip(".,;:!?«»\"()…").lower()


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def montage(proj):
    a = proj / "assets" / "audio"
    film = json.loads((proj / "film.json").read_text(encoding="utf-8"))
    LEAD = lead_for(film)
    words = json.loads((a / "voix-mots-brut.json").read_text(encoding="utf-8"))["words"]
    raw = a / "voix.mp3"
    raw_len = duration(raw)
    # coupes : au milieu du silence après chaque phrase qui porte "pause_apres"
    cuts, i = [], 0
    for sent in film["sentences"]:
        n = len(sent["text"].split())
        i += n
        gap = float(sent.get("pause_apres", 0) or 0)
        if gap > 0 and i < len(words):
            end, nxt = words[i - 1]["end"], words[i]["start"]
            cuts.append((round((end + nxt) / 2, 3), gap))
    cuts.sort()
    bounds = [0.0] + [c for c, _ in cuts] + [raw_len]
    parts, labels = [f"anullsrc=r=44100:cl=mono,atrim=0:{LEAD:.3f}[lead]"], ["[lead]"]
    for k in range(len(bounds) - 1):
        x0, x1 = bounds[k], bounds[k + 1]
        ch = f"[0]atrim={x0:.3f}:{x1:.3f},asetpts=PTS-STARTPTS"
        if k > 0:
            ch += ",afade=t=in:d=0.005"
        ch += f",afade=t=out:st={max(0.0, x1 - x0 - 0.01):.3f}:d=0.01[v{k}]"
        parts.append(ch)
        labels.append(f"[v{k}]")
        if k < len(cuts):
            parts.append(f"anullsrc=r=44100:cl=mono,atrim=0:{cuts[k][1]:.3f}[g{k}]")
            labels.append(f"[g{k}]")

    def shift(t):
        return round(t + LEAD + sum(g for c, g in cuts if t > c), 3)

    last_end = shift(words[-1]["end"])
    total = round(last_end + TAIL + 0.05, 1)
    graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,aresample=44100,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-filter_complex", graph, "-map", "[out]", "-ar", "44100", "-ac", "1",
                    str(a / "voix-montage.wav")], check=True)
    gain = normaliser_voix(a / "voix-montage.wav")
    moved = [{"w": w["w"], "start": shift(w["start"]), "end": shift(w["end"])} for w in words]
    (a / "voix-montage-mots.json").write_text(json.dumps({"duration": total, "words": moved}, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run([sys.executable, str(HERE / "onsets.py"), str(a / "voix-montage.wav"), "--transcript", str(a / "voix-montage-mots.json"),
                    "--out", str(proj / "onsets.json")], check=True, capture_output=True)
    film["duration"] = total
    film["lead"] = LEAD
    film["audio"] = "assets/audio/mix.wav"
    film["words_file"] = "onsets.json"
    (proj / "film.json").write_text(json.dumps(film, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"montage : voix {raw_len:.2f} s, {len(cuts)} silence(s) ajouté(s), entrée {LEAD:.2f} s, voix {gain:+.1f} dB -> {VOIX_LUFS} LUFS, film {total:.1f} s")


def mix(proj):
    a = proj / "assets" / "audio"
    film = json.loads((proj / "film.json").read_text(encoding="utf-8"))
    total = float(film["duration"])
    events = json.loads((a / "sfx-events.json").read_text(encoding="utf-8")) if (a / "sfx-events.json").exists() else []
    args = ["ffmpeg", "-v", "error", "-y", "-i", str(a / "voix-montage.wav")]
    graph = ["[0]aformat=sample_rates=44100:channel_layouts=stereo[v]"]
    labels = ["[v]"]
    idx = 1
    music = a / "musique-calee.wav"
    if music.exists():
        args += ["-i", str(music)]
        graph.append(f"[{idx}]aformat=sample_rates=44100:channel_layouts=stereo,afade=t=in:d=0.4,afade=t=out:st={max(0.0, total - 3):.3f}:d=3[m]")
        labels.append("[m]")
        idx += 1
    for k, (name, at, vol) in enumerate(events):
        args += ["-i", str(SFX_DIR / f"{name}.mp3")]
        d = int(round(float(at) * 1000))
        lufs = SFX_LUFS.get(name, -20.0)
        # jamais plus fort que SFX_MAX LUFS (13 LU sous la voix), même pour la déchirure ou le clic final
        g = min(4.0, 10 ** ((SFX_REF - lufs) / 20) * float(vol) / 0.2, 10 ** ((SFX_MAX - lufs) / 20))
        graph.append(f"[{idx}]aformat=sample_rates=44100:channel_layouts=stereo,volume={g:.4f},adelay={d}|{d}[e{k}]")
        labels.append(f"[e{k}]")
        idx += 1
    graph.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.95:level=disabled[out]")
    subprocess.run(args + ["-filter_complex", ";".join(graph), "-map", "[out]", "-t", f"{total:.3f}", str(a / "mix.wav")], check=True)
    print(f"mix : {total:.1f} s, musique {'oui' if music.exists() else 'non'}, {len(events)} bruitage(s)")


if __name__ == "__main__":
    cmd, project = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
    {"montage": montage, "mix": mix}[cmd](project)
