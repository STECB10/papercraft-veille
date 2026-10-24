#!/usr/bin/env python3
"""Vérificateur du jour : refuse tout film dont un chiffre n'est pas prouvé par la source.

Usage : python3 pipeline/verifier.py        (lit jours/<date>/)  -> code 0 si tout est bon, sinon la liste des erreurs
Contrôles : fiche de l'étude, citations exactes de faits.json présentes dans source.txt, chaque chiffre affiché ou dit
présent dans faits.json, structure de film.json (stations, ancres, espacements), longueur, post LinkedIn.
"""
import copy
import difflib
import json
import re
import sys
import unicodedata

from commun import RACINE, dossier_du_jour, lire_json

sys.path.insert(0, str(RACINE / "serie" / "moteur"))
import build  # noqa: E402

NUIT = {"hook_number", "gag_waiting", "gag_clock", "steps"}
PAPIER = {"population_split", "face_to_face", "result_dots", "typo", "flow_door", "remaining_dots", "id_card", "two_groups", "result_bars", "ai_scan", "studies_stack", "metric", "key_points"}
REQUIS = {
    "hook_number": ["header", "number", "unit", "caption", "people", "lit", "lit_at", "footnote", "cam_at"],
    "gag_waiting": ["door", "chairs", "occupied", "cam_at"], "gag_clock": ["label", "cam_at"],
    "steps": ["title", "steps", "cam_at"],
    "population_split": ["total", "total_label", "dot_value", "count_at", "split_at", "groups", "cam_at"],
    "face_to_face": ["card_title", "card_value", "card_note", "label", "at", "cam_at"],
    "result_dots": ["title", "groups", "diff", "diff_at", "cam_at"], "typo": ["text", "cam_at"],
    "flow_door": ["from_label", "to_label", "at", "cam_at"], "remaining_dots": ["n", "k", "value", "label", "at", "group_label", "cam_at"],
    "id_card": ["rows", "cam_at"], "studies_stack": ["n_studies", "at", "cam_at"], "metric": ["title", "metrics", "cam_at"], "key_points": ["points", "cam_at"],
    "ai_scan": ["input_icon", "input_label", "ai_label", "output_label", "at", "cam_at"], "two_groups": ["groups", "cam_at"], "result_bars": ["title", "groups", "cam_at"],
}
HAUT = {"hook_number": 980, "gag_waiting": 660, "gag_clock": 660, "population_split": 1250, "face_to_face": 1100, "result_dots": 1270,
        "typo": 680, "flow_door": 850, "remaining_dots": 1100, "id_card": 1100, "result_bars": 1150, "ai_scan": 1180, "studies_stack": 1150, "metric": 1050}
SANS_CHIFFRE = {"y", "people", "lit", "chairs", "occupied", "dot_value", "icon", "type", "words_file", "audio", "voice", "sfx", "duration"}
NOMBRE = re.compile(r"\d+(?:[   ]\d{3})*(?:[.,]\d+)?")
PROMESSE = "Une étude par jour, vérifiée à la source."


def plat(t):
    t = unicodedata.normalize("NFKC", t).lower().replace("’", "'").replace("−", "-").replace("–", "-").replace("—", "-")
    t = re.sub(r"(?<=\d)[ ,  ](?=\d{3}\b)", "", t)
    return re.sub(r"\s+", " ", t)


def nombre(s):
    return float(re.sub(r"[   ]", "", s).replace(",", "."))


def main():
    jour = dossier_du_jour()
    err = []
    etude, source = lire_json(jour / "etude.json"), (jour / "source.txt")
    faits, film = lire_json(jour / "faits.json"), lire_json(jour / "film.json")
    post = (jour / "post.txt").read_text(encoding="utf-8") if (jour / "post.txt").exists() else ""
    if not (etude and source.exists() and faits and film and post):
        sys.exit("manquant : etude.json, source.txt, faits.json, film.json et post.txt sont tous requis")
    src = plat(source.read_text(encoding="utf-8"))

    # 1. faits : citation exacte dans la source, ou calcul à partir d'autres faits
    valeurs = {}
    for f in faits:
        fid, v = f.get("id"), f.get("valeur")
        if fid is None or not isinstance(v, (int, float)):
            err.append(f"fait mal formé : {f}")
            continue
        if f.get("citation"):
            if plat(f["citation"]) not in src:
                err.append(f"{fid} : citation introuvable mot pour mot dans source.txt : « {f['citation'][:120]} »")
            elif not any(abs(nombre(x) - v) < 1e-9 for x in NOMBRE.findall(f["citation"])):
                err.append(f"{fid} : la valeur {v} n'apparaît pas dans sa citation")
        elif f.get("calcul"):
            try:
                calc = eval(re.sub(r"\bf\d+\b", lambda m: repr(valeurs[m.group(0)]), f["calcul"]), {"__builtins__": {}, "round": round, "min": min, "max": max, "abs": abs})
                if abs(calc - v) > 0.051:
                    err.append(f"{fid} : calcul {f['calcul']} = {calc:.3f}, pas {v}")
            except Exception as e:
                err.append(f"{fid} : calcul illisible ({f['calcul']}) : {e}")
        else:
            err.append(f"{fid} : ni citation ni calcul")
        valeurs[fid] = v
    autorises = list(valeurs.values()) + [nombre(x) for x in NOMBRE.findall(f"{etude.get('date', '')} {etude.get('titre', '')}")]

    def prouve(x):
        if float(x).is_integer() and 0 <= x <= 5:
            return True
        dec = 0
        for v in autorises:
            s = f"{x}"
            dec = len(s.split(".")[1]) if "." in s and not float(x).is_integer() else 0
            if abs(round(v, dec) - x) < 1e-9 or abs(v - x) < 1e-9:
                return True
        return False

    # 2. phrases : texte dit sans chiffres, longueur, phrases imposées
    sents = film.get("sentences", [])
    mots = sum(len(s["text"].split()) for s in sents)
    if not 200 <= mots <= 290:
        err.append(f"script de {mots} mots (attendu 200 à 290)")
    for i, s in enumerate(sents):
        if re.search(r"\d", s["text"]):
            err.append(f"phrase {i} : chiffres dans le texte dit (écrire en lettres, mettre les chiffres dans display) : {s['text']}")
        if s.get("display") and s.get("mode", "sub") == "sub":
            # le sous-titre doit montrer TOUT le texte dit : seuls les chiffres et symboles peuvent remplacer des mots
            dit, vu = s["text"].split(), s["display"].split()
            sm = difflib.SequenceMatcher(None, [build.norm(w) for w in dit], [build.norm(w) for w in vu], autojunk=False)
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op != "equal" and not re.search(r"[\d%‰×±≈<>=+−]", " ".join(vu[j1:j2])):
                    err.append(f"phrase {i} : le sous-titre s'écarte du texte dit (« {' '.join(dit[i1:i2])} » / « {' '.join(vu[j1:j2])} ») : "
                               "display = texte dit mot pour mot, seuls les nombres passent en chiffres")
        for x in NOMBRE.findall(s.get("display", "")):
            if not prouve(nombre(x)):
                err.append(f"phrase {i} : « {x} » affiché sans fait correspondant dans faits.json")
        if s.get("box") and s["box"] not in s.get("display", s["text"]).split():
            err.append(f"phrase {i} : le mot-clé « {s['box']} » n'est pas un mot affiché de la phrase")
    if len(sents) < 3 or sents[-1]["text"] != "Papercraft." or sents[-2]["text"] != PROMESSE:
        err.append(f"les deux dernières phrases doivent être « {PROMESSE} » puis « Papercraft. » (mode none)")
    pv = film.get("pivot", {})
    piv = [i for i, s in enumerate(sents) if s["text"] == pv.get("text")]
    if not piv:
        err.append("pivot.text doit être exactement une des phrases")
    elif not 1.0 <= float(sents[piv[0]].get("pause_apres", 0)) <= 2.0:
        err.append("la phrase du pivot doit avoir pause_apres entre 1.0 et 2.0")

    # 3. chiffres dans les stations
    def balayer(o, cle=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in SANS_CHIFFRE or k in build.TIME_KEYS or k == "chips":
                    continue
                balayer(v, k)
        elif isinstance(o, list):
            for v in o:
                balayer(v, cle)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            if not prouve(float(o)):
                err.append(f"« {o} » ({cle}) sans fait correspondant dans faits.json")
        elif isinstance(o, str):
            for x in NOMBRE.findall(o):
                if not prouve(nombre(x)):
                    err.append(f"« {x} » dans « {o[:60]} » ({cle}) sans fait correspondant dans faits.json")
    balayer({k: film.get(k) for k in ("night", "paper", "end")})

    # 4. structure, icônes, espacements
    for zone, types in (("night", NUIT), ("paper", PAPIER)):
        sts = film.get(zone, {}).get("stations", [])
        for k, st in enumerate(sts):
            t = st.get("type")
            if t not in types:
                err.append(f"{zone} : type de station inconnu « {t} » (permis : {', '.join(sorted(types))})")
                continue
            for r in REQUIS[t]:
                if r not in st:
                    err.append(f"{zone} station {k} ({t}) : champ « {r} » manquant")
            for ic in re.findall(r"'icon': '([^']+)'", str(st)):
                if ic not in build.ICONS:
                    err.append(f"icône inconnue « {ic} » (permises : {', '.join(build.ICONS)})")
            if t == "metric" and not 1 <= len(st.get("metrics", [])) <= 3:
                err.append("metric : 1 à 3 mesures")
            if t == "key_points" and not 2 <= len(st.get("points", [])) <= 4:
                err.append("key_points : 2 à 4 constats")
            for pt in st.get("points", []) if t == "key_points" else []:
                if len(pt.get("text", "")) > 70:
                    err.append(f"key_points : constat trop long ({len(pt['text'])} caractères, 70 au plus) : {pt['text']}")
            if t == "ai_scan" and st.get("input_icon") not in build.ICONS:
                err.append(f"ai_scan : input_icon « {st.get('input_icon')} » inconnue (permises : {', '.join(build.ICONS)})")
            for g in st.get("groups", []) if t in ("population_split", "result_dots", "result_bars", "two_groups") else []:
                if len(str(g.get("label", ""))) > 22:
                    err.append(f"{t} : nom de groupe trop long « {g.get('label')} » (22 caractères au plus, ex. « Sans IA » / « Avec IA »)")
            if k + 1 < len(sts):
                h = HAUT.get(t, 1100)
                if t == "steps":
                    h = 170 + 330 * len(st.get("steps", [])) + 200
                if t == "key_points":
                    h = 260 + 226 * len(st.get("points", []))
                if t == "two_groups":
                    h = max(1100, 170 + 196 * max(len(g.get("steps", [])) for g in st.get("groups", [{}])) + 300)
                if sts[k + 1].get("y", 0) < st.get("y", 0) + h:
                    err.append(f"{zone} : la station {k + 1} doit être à y ≥ {st.get('y', 0) + h} (sinon elle chevauche la précédente)")
        if zone == "paper" and not any(st.get("type") == "ai_scan" for st in sts):
            err.append("paper : une station ai_scan (ce que fait l'IA) est obligatoire, juste après id_card")
        if zone == "night" and sts and sts[-1].get("type") == "steps" and len(sts[-1]["steps"]) > 4:
            err.append("steps : 4 étapes au plus")

    # 5. ancres : résolues sur une voix fictive (un mot par seconde)
    try:
        faux = []
        for s in sents:
            for w in s["text"].split():
                faux.append({"w": w, "s": len(faux) * 1.0, "e": len(faux) * 1.0 + 0.5})
        f2 = copy.deepcopy(film)
        build.resolve(f2, build.Clock(f2, faux))
    except SystemExit as e:
        err.append(f"ancres : {e}")
    except Exception as e:
        err.append(f"film.json illisible par le moteur : {type(e).__name__} {e}")

    # 6. post LinkedIn
    lignes = [l for l in post.strip().splitlines() if l.strip()]
    if etude.get("lien", "") not in post:
        err.append(f"post.txt doit contenir le lien de l'article : {etude.get('lien')}")
    if not lignes or len(lignes[0]) > 160:
        err.append("post.txt : la première ligne (accroche) doit faire 160 caractères au plus")
    if len(post) > 1500:
        err.append(f"post.txt trop long ({len(post)} caractères, 1500 au plus)")
    for x in NOMBRE.findall(post.replace(etude.get("lien", ""), "")):
        if not prouve(nombre(x)):
            err.append(f"post.txt : « {x} » sans fait correspondant")

    if err:
        print("REFUSÉ :\n- " + "\n- ".join(dict.fromkeys(err)))
        sys.exit(1)
    print(f"VALIDÉ : {len(faits)} faits prouvés, {mots} mots, {len(film['night']['stations'])} + {len(film['paper']['stations'])} stations")


if __name__ == "__main__":
    main()
