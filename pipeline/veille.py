#!/usr/bin/env python3
"""Veille : cherche dans Europe PMC les études IA & santé des 21 derniers jours, les note, garde les 6 meilleures.

Usage : python3 pipeline/veille.py            -> jours/<date>/candidats.json
"""
import datetime as dt
import html
import re
import sys
import urllib.parse

from commun import HISTORIQUE, dossier_du_jour, ecrire_json, http, lire_json

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
SUJET = ('("artificial intelligence" OR "machine learning" OR "deep learning" OR "large language model" OR '
         '"neural network" OR "computer vision" OR "natural language processing")')
SANTE = '(patient OR patients OR clinical OR hospital OR health OR physiotherapy OR rehabilitation OR nursing)'
REVUES = ["lancet", "new england journal", "jama", "bmj", "nature medicine", "nature communications", "npj digital medicine",
          "radiology", "annals of internal medicine", "plos medicine", "eclinicalmedicine", "nature", "science",
          "journal of medical internet research", "jmir", "british journal of sports medicine", "physical therapy",
          "journal of physiotherapy", "european heart journal", "circulation", "gastroenterology", "ophthalmology",
          "diabetes care", "journal of clinical oncology", "cell"]
EXCLURE = re.compile(r"\b(review|meta-analys|protocol|editorial|comment|letter|erratum|correction|retracted|scoping)\b", re.I)


def chercher(depuis, jusqua):
    q = f'{SUJET} AND {SANTE} AND FIRST_PDATE:[{depuis} TO {jusqua}] AND HAS_ABSTRACT:Y AND LANG:eng'
    out, curseur = [], "*"
    for _ in range(4):
        url = API + "?" + urllib.parse.urlencode({"query": q, "format": "json", "resultType": "core", "pageSize": 200,
                                                  "cursorMark": curseur, "sort": "P_PDATE_D desc"})
        r = http(url, timeout=90)
        out += r.get("resultList", {}).get("result", [])
        nxt = r.get("nextCursorMark")
        if not nxt or nxt == curseur:
            break
        curseur = nxt
    return out


def propre(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t or ""))).strip()


def noter(r, deja):
    titre, resume = propre(r.get("title")), propre(r.get("abstractText"))
    types = " ".join(r.get("pubTypeList", {}).get("pubType", [])).lower()
    revue = (r.get("journalInfo", {}).get("journal", {}).get("title") or r.get("bookOrReportDetails", {}).get("publisher") or "").lower()
    doi = (r.get("doi") or "").lower()
    if not doi or doi in deja or len(resume) < 900:
        return None
    if EXCLURE.search(titre) or EXCLURE.search(types):
        return None
    s, raisons = 0, []
    texte = (titre + " " + resume).lower()
    if "randomized controlled trial" in types or re.search(r"randomi[sz]ed", texte):
        s += 6; raisons.append("essai tiré au sort")
    if "prospective" in texte:
        s += 3; raisons.append("prospectif")
    if re.search(r"multi-?cent(er|re)|multi-?site|nationwide", texte):
        s += 2; raisons.append("multicentrique")
    ns = [int(x.replace(",", "").replace(" ", "")) for x in re.findall(r"(\d{1,3}(?:[ ,]\d{3})+|\d{3,6})\s+(?:patients|participants|adults|children|women|men|individuals)", texte)]
    if ns and max(ns) >= 300:
        s += 2; raisons.append(f"n = {max(ns)}")
    if any(v in revue for v in REVUES):
        s += 3; raisons.append("revue majeure")
    if r.get("isOpenAccess") == "Y" or r.get("pmcid"):
        s += 2; raisons.append("texte intégral libre")
    if r.get("source") == "PPR":
        s -= 4; raisons.append("préprint non relu")
    if re.search(r"\b(retrospective)\b", texte):
        s -= 1
    return {"score": s, "raisons": raisons, "id": f'{r.get("source")}:{r.get("id")}', "pmid": r.get("pmid"), "pmcid": r.get("pmcid"),
            "doi": r.get("doi"), "titre": titre, "revue": r.get("journalInfo", {}).get("journal", {}).get("title") or "préprint",
            "date": r.get("firstPublicationDate"), "auteurs": r.get("authorString", "")[:200], "types": types,
            "acces_libre": bool(r.get("pmcid")) or r.get("isOpenAccess") == "Y", "resume": resume}


def main():
    jour = dossier_du_jour()
    jour.mkdir(parents=True, exist_ok=True)
    fin = dt.date.today()
    deja = {e["doi"].lower() for e in lire_json(HISTORIQUE, [])}
    res = chercher((fin - dt.timedelta(days=21)).isoformat(), fin.isoformat())
    notes = [n for n in (noter(r, deja) for r in res) if n]
    notes.sort(key=lambda n: (-n["score"], n["date"] or ""), reverse=False)
    top = notes[:6]
    if not top:
        sys.exit("veille : aucune étude candidate")
    ecrire_json(jour / "candidats.json", top)
    print(f"veille : {len(res)} résultats, {len(notes)} retenus, top {len(top)} -> {jour / 'candidats.json'}")
    for n in top:
        print(f"  {n['score']:>3}  {n['revue'][:30]:30}  {n['titre'][:90]}")


if __name__ == "__main__":
    main()
