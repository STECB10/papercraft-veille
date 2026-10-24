#!/usr/bin/env python3
"""Prépare la source de l'étude choisie : résumé + texte intégral libre s'il existe (Europe PMC).

Usage : python3 pipeline/texte_integral.py <rang>      (rang dans candidats.json, à partir de 1)
Écrit jours/<date>/source.txt (le seul texte dont on peut tirer des chiffres) et jours/<date>/etude.json (fiche).
"""
import re
import sys

from commun import dossier_du_jour, ecrire_json, http, lire_json


def xml_en_texte(x):
    x = re.sub(r"<(xref|sup|sub)[^>]*>.*?</\1>", lambda m: m.group(0) if m.group(1) != "xref" else "", x, flags=re.S)
    x = re.sub(r"</(p|title|tr|caption|sec|table-wrap|fig|label)>", "\n", x)
    x = re.sub(r"</t[dh]>", " | ", x)
    x = re.sub(r"<[^>]+>", " ", x)
    x = re.sub(r"[ \t]+", " ", x)
    return re.sub(r"\n\s*\n+", "\n", x).strip()


def main():
    rang = int(sys.argv[1])
    jour = dossier_du_jour()
    c = lire_json(jour / "candidats.json")[rang - 1]
    parties = [f"TITRE : {c['titre']}", f"REVUE : {c['revue']} · {c['date']}", f"DOI : {c['doi']}", "", "RÉSUMÉ :", c["resume"]]
    integral = False
    if c.get("pmcid"):
        try:
            x = http(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{c['pmcid']}/fullTextXML", brut=True, timeout=90).decode("utf-8", "replace")
            corps = x.split("<body", 1)[1] if "<body" in x else x
            t = xml_en_texte(corps)
            if len(t) > 3000:
                parties += ["", "TEXTE INTÉGRAL :", t[:150000]]
                integral = True
        except Exception as e:
            print(f"texte intégral indisponible : {e}")
    (jour / "source.txt").write_text("\n".join(parties), encoding="utf-8")
    ecrire_json(jour / "etude.json", {"titre": c["titre"], "revue": c["revue"], "date": c["date"], "doi": c["doi"],
                                      "lien": f"https://doi.org/{c['doi']}", "pmid": c.get("pmid"), "pmcid": c.get("pmcid"),
                                      "auteurs": c["auteurs"], "texte_integral": integral, "preprint": c["revue"] == "préprint"})
    print(f"source : {'texte intégral' if integral else 'résumé seul'} ({len(chr(10).join(parties))} caractères)")


if __name__ == "__main__":
    main()
