#!/usr/bin/env python3
"""Normalise le mixage final à -16 LUFS intégré (cible web de la méthode), crête vraie -1,5 dBTP (loudnorm en deux passes, gain linéaire).

Usage : python3 serie/moteur/normaliser.py <projet>   (remplace <projet>/assets/audio/mix.wav)
"""
import json
import pathlib
import subprocess
import sys

I, TP, LRA = -16.0, -1.5, 11.0


def main(project):
    mix = pathlib.Path(project).resolve() / "assets" / "audio" / "mix.wav"
    tmp = mix.with_name("mix-norm.wav")
    p1 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mix), "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json",
                         "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(p1[p1.rindex("{"):p1.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mix), "-af", af, "-ar", "44100", str(tmp)], check=True)
    tmp.replace(mix)
    print(f"mix normalisé : {m['input_i']} LUFS -> {I} LUFS (crête vraie max {TP} dBTP)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
