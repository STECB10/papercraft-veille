#!/usr/bin/env python3
"""Filet de sécurité de la relecture indépendante (skill .claude/skills/relecture) : le second agent relit le film contre
la source et peut le corriger ; ce script garantit qu'il ne peut pas casser la vidéo du jour.

  python3 pipeline/relecture.py sauver    avant la relecture : copie film.json, post.txt, faits.json et SCRIPT.md dans
                                          jours/<date>/.avant-relecture/
  python3 pipeline/relecture.py filet     après : si le film relu ne passe plus le vérificateur, la version d'origine est
                                          remise ; relecture.json dit ce qui s'est passé (repris dans le message Telegram)

Ne sort jamais en erreur : une relecture ratée ne doit pas empêcher la vidéo. La vérification des chiffres, elle, reste
bloquante, à l'étape suivante de la chaîne.
"""
import json
import shutil
import subprocess
import sys

from commun import RACINE, dossier_du_jour, ecrire_json, lire_json

FICHIERS = ("film.json", "post.txt", "faits.json", "SCRIPT.md")


def valide():
    for script in ("nombres.py", "verifier.py"):
        r = subprocess.run([sys.executable, str(RACINE / "pipeline" / script)], capture_output=True, text=True)
        if r.returncode:
            return False, (r.stdout + r.stderr).strip()[-600:]
    return True, ""


def sauver():
    jour = dossier_du_jour()
    dest = jour / ".avant-relecture"
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    for n in FICHIERS:
        if (jour / n).exists():
            shutil.copy2(jour / n, dest / n)
    (jour / "relecture.json").unlink(missing_ok=True)
    print(f"sauvegarde avant relecture : {dest}")


def phrases_modifiees(jour):
    avant = lire_json(jour / ".avant-relecture" / "film.json", {})
    apres = lire_json(jour / "film.json", {})
    a = [s.get("text") for s in avant.get("sentences", [])]
    b = [s.get("text") for s in apres.get("sentences", [])]
    return sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))


def filet():
    jour = dossier_du_jour()
    dest = jour / ".avant-relecture"
    rel = lire_json(jour / "relecture.json", None)
    if not dest.exists():
        print("filet : pas de sauvegarde (relecture non lancée), rien à faire")
        return
    if not isinstance(rel, dict):
        rel = {"verdict": "non faite", "resume": "la relecture indépendante n'a pas abouti : film d'origine, vérifié par le programme seul", "points": []}
        for n in FICHIERS:      # un passage interrompu peut avoir laissé un fichier à moitié modifié
            if (dest / n).exists():
                shutil.copy2(dest / n, jour / n)
    ok, journal = valide()
    if not ok:
        for n in FICHIERS:
            if (dest / n).exists():
                shutil.copy2(dest / n, jour / n)
        rel["verdict"] = "abandonnée"
        rel["resume"] = "le film relu ne passait plus le vérificateur : la version d'origine est gardée"
        rel["journal"] = journal
        print("filet : le film relu est refusé par le vérificateur, version d'origine remise")
    rel["phrases_modifiees"] = phrases_modifiees(jour)
    ecrire_json(jour / "relecture.json", rel)
    shutil.rmtree(dest, ignore_errors=True)
    print(f"relecture : {rel.get('verdict')} · {rel.get('phrases_modifiees')} phrase(s) modifiée(s) · {rel.get('resume', '')}")


if __name__ == "__main__":
    try:
        {"sauver": sauver, "filet": filet}[sys.argv[1]]()
    except Exception as e:      # jamais bloquant
        print(f"relecture.py {sys.argv[1:]} : {e}")
