#!/usr/bin/env python3
"""Veille : cherche dans Europe PMC les études IA & santé des 21 derniers jours, les note, garde les 6 meilleures.

Usage : python3 pipeline/veille.py            -> jours/<date>/candidats.json

Depuis le 11 novembre 2026 (« process v4 ») :
  - le type d'étude se lit d'abord dans le titre et les types déclarés, plus dans une simple mention du résumé
    (une revue de portée qui citait « meta-analysis » était classée méta-analyse) ;
  - une « revue majeure » est reconnue par son nom, plus par un bout de mot (« radiology » faisait passer
    Journal of Neuroradiology et Pediatric Radiology pour Radiology) ;
  - les études vétérinaires, animales ou de laboratoire sont écartées ; « prospectif » demande un vrai plan prospectif ;
  - la série ne tourne plus en rond : chaque candidat porte ses thèmes, un thème traité les jours précédents est
    pénalisé, et les 6 retenus ne sont jamais tous du même type ni du même thème.
"""
import datetime as dt
import html
import re
import sys
import urllib.parse

from commun import HISTORIQUE, JOURS, dossier_du_jour, ecrire_json, http, lire_json

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
SUJET = ('("artificial intelligence" OR "machine learning" OR "deep learning" OR "large language model" OR '
         '"neural network" OR "computer vision" OR "natural language processing")')
SANTE = '(patient OR patients OR clinical OR hospital OR health OR physiotherapy OR rehabilitation OR nursing)'
# le nom de la revue, en minuscules, sans « the » : égalité ou début, jamais « contient »
REVUES = re.compile(r"^(?:the )?(?:lancet\b.*|new england journal of medicine|jama\b.*|bmj\b.*|nature medicine|nature communications|"
                    r"npj digital medicine|radiology|annals of internal medicine|plos medicine|eclinicalmedicine|nature|science|"
                    r"journal of medical internet research|jmir\b.*|british journal of sports medicine|physical therapy|"
                    r"journal of physiotherapy|european heart journal\b.*|circulation\b.*|gastroenterology|ophthalmology|diabetes care|"
                    r"journal of clinical oncology|cell|annals of oncology|gut|chest|pain|stroke|jacc\b.*|"
                    r"journal of the american college of cardiology|american journal of respiratory and critical care medicine|"
                    r"intensive care medicine|annals of the rheumatic diseases|journal of orthopaedic (?:&|and) sports physical therapy)$")
IA = re.compile(r"\b(artificial intelligence|machine learning|deep learning|large language models?|llms?|neural networks?|"
                r"computer vision|natural language processing|chatgpt|gpt-?4o?|chatbots?|algorithms?-based|ai)\b", re.I)
EXCLURE = re.compile(r"\b(protocol|editorial|comment|letter|erratum|correction|retracted)\b", re.I)
# pas des patients : médecine vétérinaire, modèles animaux, paillasse
HORS_SOIN = re.compile(r"\b(veterinar\w*|canine|feline|bovine|equine|porcine|livestock|poultry|zebrafish|murine|mice|mouse model|"
                       r"rat model|rats|in vitro|cell lines?|animal models?)\b", re.I)
PROSPECTIF = re.compile(r"prospective(?:ly)?[ ,-]+(?:\w+[ ,-]+){0,3}?(?:cohort|study|trial|multi-?cent\w+|observational|validation|"
                        r"enrol\w*|recruit\w*|field|evaluation|clinical|diagnostic|registry|collected|included)", re.I)
# ce dont parle l'étude : pour ne pas faire trois vidéos de cardiologie d'affilée (les clés servent aussi d'étiquettes)
THEMES = {
    "cœur": r"cardi|heart|ecg\b|electrocardiogra|echocardiogra|atrial|coronary|ejection fraction|hypertens",
    "cancer": r"cancer|oncolog|tumou?r|carcinoma|mammogra|melanoma|malignan|lymphoma|leukemi",
    "cerveau": r"stroke|dementia|alzheimer|parkinson|epilep|neuro|aneurysm|spastic|brain",
    "santé mentale": r"depress|anxiety|bipolar|psychiatr|mental health|schizo|suicid|psycholog",
    "imagerie": r"radiolog|imaging|\bct\b|computed tomography|\bmri\b|x-ray|radiograph|ultrasound|ultrasonograph",
    "yeux": r"ophthalm|retin|cataract|glaucoma|fundus|ocular",
    "diabète et poids": r"diabet|glyc[ae]mi|insulin|obesity|metabolic",
    "poumons": r"lung|pulmon|respirat|asthma|copd|pneumon",
    "rééducation et mouvement": r"rehabilitat|physiotherap|physical therap|exercise|musculoskeletal|low back|back pain|gait|"
                                r"kinemat|orthop|fracture|arthr|sports?\b",
    "urgences et réanimation": r"emergency|triage|intensive care|\bicu\b|sepsis|critical care",
    "grossesse et enfants": r"pregnan|maternal|postpartum|obstetric|neonat|pediatric|paediatric|child|infant",
    "IA conversationnelle": r"large language model|\bllms?\b|chatgpt|gpt-|chatbot|generative|conversational",
    "formation des soignants": r"medical education|nursing education|students?\b|residents?\b|curricul|simulation",
    "peau": r"dermatolog|skin\b|wound",
    "infections": r"infect|covid|sars-cov|antibiotic|antimicrobial|vaccin|tubercul",
    "digestif": r"gastro|colonoscop|endoscop|liver|hepat|bowel|colorectal",
    "bouche et dents": r"dental|dentist|oral\b|periodont|caries",
    "chirurgie": r"surg|operative|anesth|anaesth",
    "reins et sang": r"kidney|renal|dialys|an[ae]mia|h[ae]matolog|transfus",
    "soins de ville": r"primary care|general practi|family medicine|community health|pharmac|nurs",
}
THEMES = {k: re.compile(v, re.I) for k, v in THEMES.items()}
LARGES = {"IA conversationnelle", "imagerie"}       # des façons de faire plus que des sujets : pénalité légère
TERRAIN = re.compile(r"rehabilitat|physiotherap|physical therap|exercise|nurs|primary care|general practi|community|home-based|"
                     r"self-management|patient education", re.I)


def type_etude(titre, resume, types):
    """Le type d'étude décide de la trame de la vidéo (voir serie/REGLES-CONTENU.md). Le titre d'abord, puis les types
    déclarés par la base, puis la façon dont le résumé décrit sa méthode (pas une simple mention)."""
    t, r = titre.lower(), resume.lower()
    if re.search(r"meta-?analys", t) or "meta-analysis" in types:
        return "méta-analyse"
    if re.search(r"systematic review|scoping review|umbrella review", t) or "systematic review" in types:
        return "revue systématique"
    if re.search(r"\breview\b", t) or re.search(r"\breview\b", types):
        return "revue de littérature"
    if "randomized controlled trial" in types or re.search(r"randomi[sz]ed", t):
        return "essai tiré au sort"
    if re.search(r"(?:we|this study) (?:conducted|performed|undertook) an? (?:systematic review and )?meta-?analys|were pooled|pooled (?:sensitivity|estimate|analysis)", r):
        return "méta-analyse"
    if re.search(r"(?:we|this study) (?:conducted|performed|undertook) an? (?:systematic|scoping) review|databases were searched|prisma", r):
        return "revue systématique"
    if re.search(r"randomly (?:assigned|allocated)|were randomi[sz]ed|randomi[sz]ed (?:controlled |clinical )?trial", r):
        return "essai tiré au sort"
    if re.search(r"sensitivity|specificity|\bauc\b|\bauroc\b|area under|diagnostic accuracy|accuracy of", t + " " + r):
        return "performance diagnostique"
    if re.search(r"\bcohort\b|predict", t + " " + r):
        return "cohorte / prédiction"
    return "autre"


def themes_de(titre, resume=""):
    """Les thèmes d'une étude : ceux de son titre, sinon ceux qui reviennent au moins deux fois dans son résumé."""
    dans_titre = [k for k, rx in THEMES.items() if rx.search(titre)]
    if dans_titre:
        return dans_titre
    return [k for k, rx in THEMES.items() if len(rx.findall(resume)) >= 2][:3]


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


def deja_vues(jour):
    """DOI des études déjà traitées : l'historique (étude retenue et études remplacées le même jour)
    et, par sécurité, l'etude.json de chaque autre jour, au cas où l'historique aurait manqué un run."""
    deja = set()
    for e in lire_json(HISTORIQUE, []):
        deja.update(d.lower() for d in [e.get("doi")] + e.get("doi_ecartes", []) if d)
    for f in JOURS.glob("*/etude.json"):
        if f.parent != jour and (d := (lire_json(f, {}).get("doi") or "").lower()):
            deja.add(d)
    return deja


def recents(jour, n=3):
    """Les n dernières études traitées avant ce jour, de la plus récente à la plus ancienne : [(thèmes, type d'étude)]."""
    out = []
    for d in sorted((p for p in JOURS.iterdir() if p.is_dir() and p.name < jour.name and (p / "etude.json").exists()), reverse=True)[:n]:
        titre = lire_json(d / "etude.json", {}).get("titre", "")
        doi = (lire_json(d / "etude.json", {}).get("doi") or "").lower()
        te = next((c.get("type_etude") for c in lire_json(d / "candidats.json", []) if (c.get("doi") or "").lower() == doi), None)
        out.append((set(themes_de(titre)), te))
    return out


def evaluer(titre, resume, types, revue, preprint=False, acces_libre=False):
    """Note une étude (0 = écartée). Renvoie None ou {score, raisons, type_etude, themes}."""
    if len(resume) < 900 or EXCLURE.search(titre) or EXCLURE.search(types):
        return None
    if HORS_SOIN.search(titre) or len(HORS_SOIN.findall(resume)) >= 2 or HORS_SOIN.search(revue):
        return None
    # l'IA doit être le sujet de l'étude, pas une mention en passant : dans le titre, ou citée au moins 3 fois dans le résumé
    ia_titre, ia_resume = bool(IA.search(titre)), len(IA.findall(resume))
    if not ia_titre and ia_resume < 3:
        return None
    s, raisons = 0, []
    if ia_titre:
        s += 4; raisons.append("IA dans le titre")
    texte = (titre + " " + resume).lower()
    te = type_etude(titre, resume, types)
    if te == "essai tiré au sort":
        s += 6; raisons.append("essai tiré au sort")
    elif te in ("méta-analyse", "revue systématique"):
        s += 5; raisons.append(te)
    if te not in ("méta-analyse", "revue systématique", "revue de littérature") and (re.search(r"prospective", titre, re.I) or PROSPECTIF.search(resume)):
        s += 3; raisons.append("prospectif")
    if re.search(r"multi-?cent(er|re)|multi-?site|nationwide", texte) and te not in ("revue systématique", "revue de littérature"):
        s += 2; raisons.append("multicentrique")
    ns = [int(x.replace(",", "").replace(" ", "")) for x in re.findall(r"(\d{1,3}(?:[ ,]\d{3})+|\d{3,6})\s+(?:patients|participants|adults|children|women|men|individuals)", texte)]
    if ns and max(ns) >= 300:
        s += 2; raisons.append(f"n = {max(ns)}")
    if REVUES.match(re.sub(r"^the ", "", revue.lower().strip())):
        s += 3; raisons.append("revue majeure")
    if acces_libre:
        s += 2; raisons.append("texte intégral libre")
    if re.search(r"95\s?% (?:ci|confidence)|confidence interval", texte):
        s += 1; raisons.append("intervalle de confiance")
    if TERRAIN.search(titre):
        s += 1; raisons.append("soin de terrain")
    if preprint:
        s -= 4; raisons.append("préprint non relu")
    if re.search(r"\b(retrospective)\b", texte):
        s -= 1
    return {"score": s, "raisons": raisons, "type_etude": te, "themes": themes_de(titre, resume)}


def noter(r, deja):
    titre, resume = propre(r.get("title")), propre(r.get("abstractText"))
    types = " ".join(r.get("pubTypeList", {}).get("pubType", [])).lower()
    revue = (r.get("journalInfo", {}).get("journal", {}).get("title") or r.get("bookOrReportDetails", {}).get("publisher") or "")
    doi = (r.get("doi") or "").lower()
    if not doi or doi in deja:
        return None
    acces = bool(r.get("pmcid")) or r.get("isOpenAccess") == "Y"
    ev = evaluer(titre, resume, types, revue, preprint=r.get("source") == "PPR", acces_libre=acces)
    if not ev:
        return None
    return {**ev, "id": f'{r.get("source")}:{r.get("id")}', "pmid": r.get("pmid"), "pmcid": r.get("pmcid"),
            "doi": r.get("doi"), "titre": titre, "revue": r.get("journalInfo", {}).get("journal", {}).get("title") or "préprint",
            "date": r.get("firstPublicationDate"), "auteurs": r.get("authorString", "")[:200], "types": types,
            "acces_libre": acces, "resume": resume}


def varier(notes, passes):
    """La série ne tourne pas en rond. passes : [(thèmes, type)] des dernières vidéos, la plus récente d'abord.
    Un thème déjà traité hier coûte 3 points, avant-hier 2, il y a trois jours 1 (1 seul point pour une façon de faire :
    IA conversationnelle, imagerie) ; le même type d'étude qu'hier coûte 1 point."""
    for n in notes:
        th = set(n.get("themes") or [])
        for age, (vus, te) in enumerate(passes[:3]):
            communs = th & vus
            if communs:
                precis = communs - LARGES
                cout = (3 - age) if precis else 1
                n["score"] -= cout
                quand = ["hier", "avant-hier", "il y a trois jours"][age]
                n["raisons"].append(f"thème déjà traité {quand} ({', '.join(sorted(precis or communs))}) : −{cout}")
                break
        if passes and passes[0][1] and n.get("type_etude") == passes[0][1]:
            n["score"] -= 1
            n["raisons"].append("même type d'étude qu'hier : −1")
    return notes


def choisir(notes, k=6):
    """Les k meilleures, sans que la liste soit d'un seul bloc : 3 au plus du même type d'étude, 2 au plus du même thème
    précis. S'il manque des candidats, on complète par la note."""
    tri = sorted(notes, key=lambda n: (-n["score"], n.get("date") or ""))
    top, types, themes = [], {}, {}
    for n in tri:
        te = n.get("type_etude")
        th = [t for t in (n.get("themes") or []) if t not in LARGES][:1]
        if types.get(te, 0) >= 3 or any(themes.get(t, 0) >= 2 for t in th):
            continue
        top.append(n)
        types[te] = types.get(te, 0) + 1
        for t in th:
            themes[t] = themes.get(t, 0) + 1
        if len(top) == k:
            break
    for n in tri:
        if len(top) >= k:
            break
        if n not in top:
            top.append(n)
    return sorted(top, key=lambda n: (-n["score"], n.get("date") or ""))


def main():
    jour = dossier_du_jour()
    jour.mkdir(parents=True, exist_ok=True)
    fin = dt.date.today()
    deja = deja_vues(jour)
    res = chercher((fin - dt.timedelta(days=21)).isoformat(), fin.isoformat())
    notes = [n for n in (noter(r, deja) for r in res) if n]
    top = choisir(varier(notes, recents(jour)))
    if not top:
        sys.exit("veille : aucune étude candidate")
    ecrire_json(jour / "candidats.json", top)
    print(f"veille : {len(res)} résultats, {len(notes)} retenus, top {len(top)} -> {jour / 'candidats.json'}")
    for n in top:
        print(f"  {n['score']:>3}  {n['type_etude'][:20]:20}  {n['revue'][:26]:26}  {n['titre'][:70]}  [{', '.join(n['themes'][:2])}]")


if __name__ == "__main__":
    main()
