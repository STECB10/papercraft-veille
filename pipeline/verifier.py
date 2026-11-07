#!/usr/bin/env python3
"""Vérificateur du jour : refuse tout film dont un chiffre n'est pas prouvé par la source.

Usage : python3 pipeline/verifier.py        (lit jours/<date>/)  -> code 0 si tout est bon, sinon la liste des erreurs
Contrôles : fiche de l'étude, citations exactes de faits.json présentes dans source.txt, chaque chiffre affiché ou dit
présent dans faits.json, structure de film.json (planches de la charte serie/frame.md, ancres), longueur, post LinkedIn.
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

NUIT = set(build.HOOKS) | set(build.GAGS) | {"steps"}
PAPIER = {"population_split", "face_to_face", "result_dots", "typo", "flow_door", "remaining_dots", "id_card", "two_groups", "result_bars", "ai_scan", "studies_stack", "metric", "key_points",
          "result_strips", "forest_plot", "roc_curve", "diagnostic_grid", "survival_curves", "chat", "image_scan"} | set(build.planches.TYPES)
REQUIS = {
    "hook_number": ["header", "number", "caption", "caption_at", "cam_at"],
    "hook_question": ["header", "text", "italic", "cam_at"],
    "hook_image": ["header", "image", "title", "title_at", "cam_at"],
    "hook_versus": ["header", "left", "right", "cam_at"],
    "hook_headline": ["header", "headline", "mark", "mark_at", "cam_at"],
    "gag_waiting": ["door", "chairs", "occupied", "cam_at"], "gag_clock": ["label", "cam_at"],
    "gag_calendar": ["label", "cam_at"], "gag_pile": ["label", "cam_at"],
    "steps": ["title", "steps", "cam_at"],
    "population_split": ["total", "total_label", "dot_value", "count_at", "split_at", "groups", "cam_at"],
    "face_to_face": ["card_title", "card_value", "card_note", "label", "at", "cam_at"],
    "result_dots": ["title", "groups", "cam_at"], "typo": ["text", "cam_at"],
    "flow_door": ["from_label", "to_label", "at", "cam_at"], "remaining_dots": ["n", "k", "value", "label", "at", "group_label", "cam_at"],
    "id_card": ["rows", "cam_at"], "studies_stack": ["n_studies", "at", "cam_at"], "metric": ["title", "metrics", "cam_at"], "key_points": ["points", "cam_at"],
    "ai_scan": ["input_icon", "input_label", "ai_label", "output_label", "at", "cam_at"], "two_groups": ["groups", "cam_at"], "result_bars": ["title", "groups", "cam_at"],
    "result_strips": ["title", "groups", "cam_at"], "forest_plot": ["studies", "pooled", "cam_at"], "roc_curve": ["auc", "cam_at"],
    "diagnostic_grid": ["total", "sick", "found", "at", "cam_at"], "survival_curves": ["times", "groups", "cam_at"],
    "chat": ["messages", "cam_at"], "image_scan": ["image", "at", "cam_at"],
    "flow_chart": ["stages", "cam_at"], "big_stat": ["value", "label", "at", "cam_at"], "timeline": ["events", "cam_at"],
}
SANS_CHIFFRE = {"y", "people", "lit", "chairs", "occupied", "dot_value", "icon", "type", "words_file", "audio", "voice", "sfx", "duration", "lead",
                "max", "lines", "null", "log", "from", "image", "modality", "tear", "visual", "edition", "italic", "roll", "after"}
# connecteurs et tournures de l'oral qui relient une phrase à la précédente (début de phrase, minuscules)
LIAISONS = ("et ", "et,", "mais", "or ", "or,", "donc", "alors", "pourtant", "cependant", "toutefois", "en effet", "en revanche", "autrement dit",
            "concrètement", "résultat", "pour le savoir", "pour ", "ainsi", "puis", "ensuite", "enfin", "d'abord", "d'ailleurs", "par exemple",
            "en clair", "bref", "surtout", "car ", "c'est là", "c'est pour", "c'est ", "au final", "au départ", "au bout", "côté ", "quant ",
            "du côté", "de leur côté", "de son côté", "à l'inverse", "à l'arrivée", "en pratique", "en somme", "reste ", "attention", "bonne nouvelle",
            "le hic", "le problème", "petit bémol", "seul bémol", "et là", "là,", "ici,", "cette fois", "en moyenne", "au total", "même ", "aussi",
            "si ", "quand ", "lorsque", "comme ", "parce qu", "grâce à", "sans ", "avec ", "dans ", "chez ", "sur ", "à ", "en ", "plus ", "moins ",
            "autre ", "autrement", "deuxième", "troisième", "premier", "première", "dernier", "dernière", "voilà", "imaginez", "prenons", "retenez",
            "ce qu'il faut", "ce que", "la question", "la réponse", "l'idée", "le principe", "le but", "le résultat", "la bonne", "la limite",
            "une limite", "à noter", "et pour", "et surtout", "mieux", "pire", "en plus", "de plus", "par ailleurs", "néanmoins", "malgré")
CONNECTEURS_FORTS = ("et ", "mais", "or ", "donc", "alors", "pourtant", "cependant", "toutefois", "en effet", "en revanche", "autrement dit",
                     "concrètement", "résultat", "ainsi", "puis", "ensuite", "enfin", "d'abord", "d'ailleurs", "au final", "attention", "surtout")
NOMBRE = re.compile(r"\d+(?:[   ]\d{3})*(?:[.,]\d+)?")
PROMESSE = "Une étude par jour, vérifiée à la source."


def plat(t):
    t = unicodedata.normalize("NFKC", t).lower().replace("’", "'").replace("−", "-").replace("–", "-").replace("—", "-")
    t = re.sub(r"(?<=\d)[ ,  ](?=\d{3}\b)", "", t)
    return re.sub(r"\s+", " ", t)


def nombre(s):
    return float(re.sub(r"[   ]", "", s).replace(",", "."))


def film_precedent(jour):
    """film.json du dernier jour publié avant celui-ci (pour ne jamais ouvrir deux vidéos de suite de la même façon)."""
    for d in sorted((p for p in jour.parent.iterdir() if p.is_dir() and p.name < jour.name), reverse=True):
        f = lire_json(d / "film.json")
        if f and f.get("night", {}).get("stations"):
            return d.name, f
    return None, None


def controle_accroche(sts, film, jour):
    err = []
    if not sts or sts[0].get("type") not in build.HOOKS:
        return [f"night : la première station est une accroche ({', '.join(build.HOOKS)})"]
    h = sts[0]
    t = h["type"]
    if len(h.get("header", "")) > 60:
        err.append(f"{t} : header trop long ({len(h['header'])} caractères, 60 au plus) : « {h['header']} »")
    if len(h.get("footnote", "") or "") > 60:
        err.append(f"{t} : footnote trop long (60 caractères au plus)")
    if t == "hook_number":
        if len(str(h.get("number", ""))) > 7:
            err.append(f"hook_number : « {h.get('number')} » trop long pour un chiffre clé (7 caractères au plus)")
        if len(h.get("caption", "")) > 75:
            err.append(f"hook_number : caption trop longue ({len(h['caption'])} caractères, 75 au plus) : « {h['caption']} »")
        if len(h.get("unit", "") or "") > 14:
            err.append("hook_number : unit en un ou deux mots (14 caractères au plus)")
        if h.get("visual") and h["visual"] not in build.accroches.VISUALS:
            err.append(f"hook_number : visual « {h['visual']} » inconnu ({', '.join(build.accroches.VISUALS)})")
        if build.accroches.visual_kind(h) == "grid" and (h.get("unit") or "").strip() != "%":
            err.append("hook_number : la grille de 100 ne sert qu'à un pourcentage (unit « % »)")
        if h.get("ratio") and not (isinstance(h["ratio"], dict) and 0 < int(h["ratio"].get("k", 0)) <= int(h["ratio"].get("n", 0)) <= 30):
            err.append("hook_number : ratio = {\"k\": …, \"n\": …} avec 0 < k ≤ n ≤ 30 (« k sur n », deux faits)")
    if t == "hook_question":
        dites = [s["text"] for s in film.get("sentences", [])]
        if h.get("text") not in dites:
            err.append("hook_question : text = une phrase de sentences, mot pour mot (en général la première)")
        elif len(h["text"]) > 95:
            err.append("hook_question : la question doit tenir en 95 caractères")
        if h.get("italic") and build.norm(h["italic"]) not in [build.norm(w) for w in h.get("text", "").split()]:
            err.append("hook_question : italic = un mot de la question")
    if t == "hook_image" and h.get("image") not in build.IMAGES + ["ecg"] + build.ICONS:
        err.append(f"hook_image : image « {h.get('image')} » inconnue ({', '.join(build.IMAGES + ['ecg'])} ou une icône)")
    if t == "hook_image" and len(h.get("title", "")) > 60:
        err.append("hook_image : title de 60 caractères au plus")
    if t == "hook_versus":
        for c in ("left", "right"):
            if not isinstance(h.get(c), dict) or not h[c].get("label"):
                err.append(f"hook_versus : {c} = {{label, number?, unit?, at, note?}}")
            elif len(h[c]["label"]) > 24:
                err.append(f"hook_versus : label trop long « {h[c]['label']} » (24 caractères au plus)")
        if not (h.get("left") or {}).get("number"):
            err.append("hook_versus : le côté gauche porte un chiffre (le droit peut rester « ? »)")
        if len(h.get("caption", "") or "") > 90:
            err.append("hook_versus : caption de 90 caractères au plus")
    if t == "hook_headline":
        if len(h.get("headline", "")) > 120:
            err.append("hook_headline : headline de 120 caractères au plus")
        mk = [build.norm(w) for w in (h.get("mark") or "").split()]
        dn = [build.norm(w) for w in h.get("headline", "").split()]
        if not mk or not any(dn[j:j + len(mk)] == mk for j in range(len(dn))):
            err.append("hook_headline : mark = des mots qui se suivent dans headline")
    # l'accroche se remplit tout de suite : ses éléments arrivent pendant les trois premières phrases, pas sur un écran vide
    def phrase_de(ancre):
        m = re.match(r"^s(\d+)", str(ancre or "s0"))
        return int(m.group(1)) if m else 0
    ancres = {"hook_number": [h.get("caption_at"), h.get("lit_at")], "hook_versus": [(h.get("left") or {}).get("at"), (h.get("right") or {}).get("at")],
              "hook_image": [h.get("title_at"), h.get("lock_at")], "hook_headline": [h.get("mark_at")]}.get(t, [])
    for a in ancres:
        if a is not None and phrase_de(a) > 2:
            err.append(f"{t} : « {a} » arrive trop tard (phrase {phrase_de(a)}) : les éléments de l'accroche apparaissent pendant les phrases 0 à 2")
    # jamais deux vidéos de suite qui s'ouvrent pareil
    veille, fv = film_precedent(jour)
    if fv:
        av = fv["night"]["stations"]
        if av[0].get("type") == t:
            err.append(f"accroche « {t} » déjà utilisée la veille ({veille}) : choisir une autre accroche ({', '.join(x for x in build.HOOKS if x != t)})")
        hier = [s.get("type") for s in fv.get("paper", {}).get("stations", [])]
        auj = [s.get("type") for s in film.get("paper", {}).get("stations", [])]
        if hier and auj == hier:
            err.append(f"les planches de l'étude reprennent exactement la suite de la veille ({veille}) : {', '.join(auj)}. "
                       "Varier au moins une planche (flow_chart, big_stat, timeline, result_strips, key_points…)")
        gv = next((s.get("type") for s in av if s.get("type", "").startswith("gag_")), None)
        g = next((s.get("type") for s in sts if s.get("type", "").startswith("gag_")), None)
        if g and g == gv:
            err.append(f"moment muet « {g} » déjà utilisé la veille ({veille}) : en prendre un autre ({', '.join(x for x in build.GAGS if x != g)}) ou aucun")
    return err


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
    if not 210 <= mots <= 300:
        err.append(f"script de {mots} mots (attendu 210 à 300) : des connecteurs courts (« Et », « Mais », « Or », « Alors »), pas de phrases en plus")
    corps = [s for s in sents if s.get("mode", "sub") == "sub"]
    courtes = [s["text"] for s in corps if len(s["text"].split()) < 6]
    if len(courtes) > 2:
        err.append(f"trop de phrases hachées (moins de 6 mots) : {courtes} ; faire des phrases complètes avec connecteurs")
    if corps and sum(len(s["text"].split()) for s in corps) / len(corps) < 9:
        err.append("phrases trop courtes en moyenne (9 mots au moins) : relier les idées avec des connecteurs logiques")
    respir = [s for s in corps if 0.2 <= float(s.get("pause_apres", 0) or 0) <= 0.8]
    if len(respir) < 2:
        err.append("ajouter des respirations : pause_apres de 0,3 à 0,5 s aux changements de partie (2 au moins)")
    if len(respir) > 7:
        err.append(f"trop de silences ajoutés ({len(respir)} phrases avec pause_apres) : la voix devient hachée. 7 au plus, "
                   "aux seuls changements de partie (après le contexte, après la méthode, après le résultat principal…)")
    # 2 bis. un humain qui parle : les phrases s'enchaînent avec des connecteurs, pas une liste de constats
    def liaison(txt):
        t = txt.lower().replace("’", "'").lstrip("«  ")
        return t.startswith(LIAISONS) or any(c in " " + " ".join(t.split()[:6]) + " " for c in (" donc ", " alors ", " pourtant ", " aussi ", " ainsi ", " en effet ", " cependant "))
    typos = {st.get("text") for st in film.get("paper", {}).get("stations", []) if st.get("type") == "typo"} | {film.get("pivot", {}).get("text")}
    suite = [s["text"] for s in corps[1:] if s["text"] not in typos]
    if suite:
        lies = [liaison(t) for t in suite]
        if sum(lies) < 0.6 * len(lies):
            err.append(f"le texte ressemble à une liste de constats : {sum(lies)} phrase(s) sur {len(lies)} seulement s'enchaînent avec la "
                       "précédente. Relier au moins 60 % des phrases par un connecteur ou une tournure orale (« Et », « Mais », « Alors », "
                       "« Concrètement », « Résultat : », « Autrement dit », « Le problème, c'est que… », « Pour le savoir »…)")
        for k in range(len(lies) - 2):
            if not any(lies[k:k + 3]):
                err.append(f"trois phrases de suite sans lien entre elles : « {suite[k][:50]}… » / « {suite[k+1][:50]}… » / « {suite[k+2][:50]}… »")
                break
        forts = [next((c for c in CONNECTEURS_FORTS if t.lower().startswith(c)), None) for t in suite]
        for c in set(f for f in forts if f):
            if forts.count(c) > 2:
                err.append(f"« {c.strip().capitalize()} » ouvre {forts.count(c)} phrases : varier les connecteurs (2 fois au plus chacun)")
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
            for g in st.get("groups", []) if t in ("population_split", "result_dots", "result_bars", "result_strips", "two_groups", "survival_curves") else []:
                if len(str(g.get("label", ""))) > 22:
                    err.append(f"{t} : nom de groupe trop long « {g.get('label')} » (22 caractères au plus, ex. « Sans IA » / « Avec IA »)")
            for g in st.get("groups", []) if t in ("result_bars", "result_strips", "result_dots") else []:
                if "num" not in g and t != "result_dots":
                    err.append(f"{t} : chaque groupe a « value » (texte affiché) et « num » (nombre)")
            if t == "result_dots" and not (st.get("diff") or st.get("ci")):
                err.append("result_dots : il faut « ci » (écart et intervalle) ou « diff »")
            ci = st.get("ci")
            if isinstance(ci, dict):
                if not all(x in ci for x in ("num", "low", "high")):
                    err.append(f"{t} : ci doit avoir num, low et high (et value, le texte affiché, ex. « +0,09 »)")
                elif not float(ci["low"]) <= float(ci["num"]) <= float(ci["high"]):
                    err.append(f"{t} : ci incohérent (low ≤ num ≤ high)")
            if t == "ai_scan" and st.get("modality") and st["modality"] not in build.MODALITIES:
                err.append(f"ai_scan : modality « {st['modality']} » inconnue (permises : {', '.join(build.MODALITIES)})")
            if t == "image_scan" and st.get("image") not in build.IMAGES:
                err.append(f"image_scan : image « {st.get('image')} » inconnue (permises : {', '.join(build.IMAGES)})")
            if t == "roc_curve" and not all(x in st.get("auc", {}) for x in ("value", "num", "at")):
                err.append("roc_curve : auc doit avoir value, num et at")
            if t == "diagnostic_grid":
                tot, sk, fd, fa = (int(st.get(x, 0) or 0) for x in ("total", "sick", "found", "false_alarms"))
                if not (0 < fd <= sk <= tot <= 100 and fa <= tot - sk):
                    err.append("diagnostic_grid : il faut found ≤ sick ≤ total ≤ 100 et false_alarms ≤ total − sick (représentation pour 100 patients au besoin)")
            if t == "survival_curves":
                for g in st.get("groups", []):
                    if len(g.get("values", [])) != len(st.get("times", [])):
                        err.append("survival_curves : chaque groupe a une valeur par temps de « times »")
            if t == "forest_plot":
                if not 2 <= len(st.get("studies", [])) <= 12:
                    err.append("forest_plot : 2 à 12 études (au-delà, studies_stack et l'intervalle de l'effet regroupé)")
                for s in st.get("studies", []) + ([st["pooled"]] if st.get("pooled") else []):
                    if not float(s.get("low", 0)) <= float(s.get("value", 0)) <= float(s.get("high", 0)):
                        err.append(f"forest_plot : « {s.get('label')} » incohérent (low ≤ value ≤ high)")
            if t == "flow_chart":
                sg = st.get("stages", [])
                if not 2 <= len(sg) <= 5:
                    err.append("flow_chart : 2 à 5 étapes")
                for x in sg:
                    if len(x.get("label", "")) > 40:
                        err.append(f"flow_chart : étiquette trop longue « {x.get('label')} » (40 caractères au plus)")
                    if not re.search(r"\d", str(x.get("n", ""))):
                        err.append(f"flow_chart : chaque étape a son effectif « n » (texte affiché, ex. « 2 378 »)")
                for e in st.get("excluded", []):
                    if not 0 <= int(e.get("after", -1)) < len(sg) - 1:
                        err.append("flow_chart : excluded.after = l'index de l'étape après laquelle on sort (0 = entre la 1re et la 2e)")
                    if len(e.get("label", "")) > 26:
                        err.append(f"flow_chart : exclusion trop longue « {e.get('label')} » (26 caractères au plus)")
            if t == "big_stat":
                if len(str(st.get("value", ""))) > 9:
                    err.append("big_stat : value de 9 caractères au plus (« 35,9 », « 6 sur 10 »)")
                if len(st.get("label", "")) > 90:
                    err.append("big_stat : label de 90 caractères au plus")
                if st.get("compare") and not isinstance(st["compare"], dict):
                    err.append("big_stat : compare = {value, unit?, label, at}")
            if t == "timeline":
                ev = st.get("events", [])
                if not 2 <= len(ev) <= 5:
                    err.append("timeline : 2 à 5 étapes")
                for e in ev:
                    if len(str(e.get("when", ""))) > 16 or len(e.get("label", "")) > 60:
                        err.append(f"timeline : « when » 16 caractères au plus, « label » 60 au plus ({e.get('when')})")
            if t == "chat":
                ms = st.get("messages", [])
                if not 1 <= len(ms) <= 4:
                    err.append("chat : 1 à 4 messages")
                for m in ms:
                    if m.get("text"):
                        err.append("chat : pas de texte dans les bulles (jamais de dialogue inventé) : « lines » donne le nombre de lignes muettes")
                    if m.get("from", "ia") not in ("patient", "ia", "soignant", "question"):
                        err.append(f"chat : from « {m.get('from')} » inconnu (patient, ia, soignant, question)")
        if zone == "paper" and not any(st.get("type") == "ai_scan" for st in sts):
            err.append("paper : une station ai_scan (ce que fait l'IA) est obligatoire, juste après id_card")
        if zone == "paper" and sum(1 for s in sts if s.get("type") == "typo") > 2:
            err.append("paper : 2 planches typo au plus (la nuance, puis la phrase à retenir)")
        if zone == "night" and sts and sts[-1].get("type") == "steps" and len(sts[-1]["steps"]) > 4:
            err.append("steps : 4 étapes au plus")
        if zone == "night":
            err += controle_accroche(sts, film, jour)

    # textes que le moteur retrouve mot pour mot parmi les phrases dites (sinon « phrase introuvable » au rendu)
    dites = {s.get("text") for s in sents}
    for nom, txt in [("paper station typo", st.get("text")) for st in film.get("paper", {}).get("stations", []) if st.get("type") == "typo"] \
            + [("pivot.text", film.get("pivot", {}).get("text")), ("end.promise", film.get("end", {}).get("promise"))]:
        if txt not in dites:
            err.append(f"{nom} : « {txt} » doit reprendre exactement une phrase de sentences (même ponctuation, rien en plus)")

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
    corps_post = [l for l in lignes[1:] if not l.lower().startswith("source") and not l.strip().startswith("#")]
    if not any(l.rstrip().endswith("?") for l in corps_post):
        err.append("post.txt : ajouter une question ouverte d'une ligne aux soignants, avant la source (elle lance les commentaires)")
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
