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
    "findings": ["items", "cam_at"], "ratio": ["value", "num", "low", "high", "at", "cam_at"],
}
SANS_CHIFFRE = {"y", "people", "lit", "chairs", "occupied", "dot_value", "icon", "type", "words_file", "audio", "voice", "sfx", "duration", "lead",
                "max", "lines", "null", "log", "from", "image", "modality", "tear", "visual", "edition", "italic", "roll", "after", "partie", "source", "tendance"}
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


# le fil du récit (retour du 8 novembre 2026 : « décousu », « on revient sur le premier truc ») : chaque phrase dit à
# quelle partie elle appartient ; les parties se suivent dans cet ordre, sans jamais revenir en arrière
PARTIES = ["accroche", "contexte", "probleme", "ia", "question", "etude", "methode", "resultat", "concret", "limite", "retenir", "fin"]
RANG = {p: i for i, p in enumerate(PARTIES)}
RANG["concret"] = RANG["resultat"]          # un résultat et ce qu'il veut dire concrètement peuvent alterner
CAUSE = (" donc", " car ", " parce qu", "résultat", " ce qui ", " si bien que", " faute d", "conséquence", " alors que", " sans ", " pour ",
         " ainsi", " du coup", " au point de", " d'où", " c'est pourquoi", " retard", " erreur", " risque")


def controle_recit(film, src, script_md):
    """Le récit se tient : parties dans l'ordre, problème expliqué, résultats concrets prouvés, connecteurs vrais,
    chiffres compréhensibles, relecture faite."""
    err = []
    sents = film.get("sentences", [])
    parts = [s.get("partie") for s in sents]
    manquants = [i for i, p in enumerate(parts) if p not in RANG]
    if manquants:
        return [f"chaque phrase a un champ « partie » ({', '.join(PARTIES)}) ; manquant ou inconnu aux phrases {manquants[:8]}"]
    for i in range(1, len(parts)):
        if RANG[parts[i]] < RANG[parts[i - 1]]:
            err.append(f"le récit revient en arrière à la phrase {i} (« {parts[i - 1]} » puis « {parts[i]} ») : chaque partie est dite une seule "
                       f"fois, dans l'ordre {' → '.join(PARTIES)}. Déplacer ou fusionner la phrase : « {sents[i]['text'][:70]} »")
            break
    for p_, (mn, mx) in {"accroche": (1, 1), "probleme": (1, 4), "question": (1, 1), "resultat": (1, 6), "concret": (2, 5), "limite": (1, 2), "retenir": (1, 1)}.items():
        n = parts.count(p_)
        if not mn <= n <= mx:
            err.append(f"partie « {p_} » : {n} phrase(s), attendu {mn} à {mx}"
                       + (" — ajouter ce que l'étude montre concrètement (ce que l'IA repère, des exemples, ce que ça change sur le terrain), "
                          "tiré du texte intégral, pas seulement des performances" if p_ == "concret" and n < mn else ""))
    pv = film.get("pivot", {}).get("text")
    for i, s in enumerate(sents):
        if s.get("text") == pv and parts[i] != "question":
            err.append("la phrase du pivot a la partie « question »")
    # un problème annoncé est un problème expliqué : pourquoi c'en est un, avec sa conséquence
    pb = [s["text"] for s in sents if s.get("partie") == "probleme"]
    if pb and len(pb) < 2 and not any(c in " " + t.lower() for t in pb for c in CAUSE):
        err.append(f"le problème n'est pas expliqué : « {pb[0][:80]} ». Dire POURQUOI c'en est un (sa cause ou sa conséquence pour les "
                   "patients : erreur, retard, risque…), dans la même phrase ou la suivante")
    # problème et résultats concrets : chaque phrase cite sa preuve, mot pour mot dans source.txt
    for i, s in enumerate(sents):
        if s.get("partie") in ("probleme", "concret"):
            q = s.get("source", "")
            if len(q) < 25:
                err.append(f"phrase {i} ({s['partie']}) : champ « source » = l'extrait de source.txt (25 caractères au moins) qui prouve ce qu'elle dit")
            elif plat(q) not in src:
                err.append(f"phrase {i} : « source » introuvable mot pour mot dans source.txt : « {q[:90]} »")
    # des connecteurs qui disent vrai
    for i, s in enumerate(sents):
        t = s["text"].lower().replace("’", "'")
        if t.startswith(("en prime", "cerise sur le gâteau", "bonus")) and any(k in t for k in ("intervalle", "confiance")):
            err.append(f"phrase {i} : « En prime » devant un intervalle de confiance ne veut rien dire ; l'intervalle précise le chiffre "
                       "(« avec une marge d'incertitude de… à… »)")
        if t.startswith(("le problème", "le hic", "le souci")) and s.get("partie") != "probleme":
            err.append(f"phrase {i} : « {s['text'][:30]}… » annonce un problème mais n'est pas dans la partie « probleme »")
        if t.startswith(("autrement dit", "en clair")) and i and parts[i] != parts[i - 1]:
            err.append(f"phrase {i} : « Autrement dit » reformule la phrase d'avant ; elle doit rester dans la même partie qu'elle")
        if any(k in t for k in ("sensibilité", "spécificité")) and "zéro virgule" in t:
            err.append(f"phrase {i} : sensibilité et spécificité se disent en pour cent ou en « x sur y » (« elle repère quatre-vingt-treize "
                       "pour cent des malades »), jamais en « zéro virgule »")
    # la phrase à retenir dit ce que ça change, sans redire un chiffre
    ret = [s for s in sents if s.get("partie") == "retenir"]
    if ret and NOMBRE.search(ret[0].get("display", "")) :
        err.append("la phrase à retenir ne redit pas un chiffre : elle dit ce que l'étude change ou pourrait changer en pratique")
    # la relecture de l'auditeur, écrite dans SCRIPT.md
    rel = script_md.split("## Relecture", 1)[1] if "## Relecture" in script_md else ""
    if sum(1 for l in rel.splitlines() if l.strip().startswith(("-", "*"))) < 6:
        err.append("SCRIPT.md : section « ## Relecture » avec les 6 questions de la skill (étape 6) et tes réponses, une puce chacune")
    return err


# --------------------------------------------------------------------------------------------- les planches suivent la voix
# Retour du 8 novembre 2026 (« des animations qui ne suivent pas le récit ») : sur l'essai du jour, la question de
# l'accroche restait 12 s à l'écran pendant que la voix parlait d'autre chose, des étapes s'allumaient sur des phrases
# qui n'en parlaient pas, une ligne de la fiche apparaissait après le départ de la caméra, « ce qui entre » dans l'IA
# arrivait après « l'IA », un rapport de cotes était dessiné comme une jauge remplie à 59 %.
MOTS_VIDES = {"avec", "dans", "pour", "sans", "sous", "leur", "leurs", "plus", "moins", "mais", "cette", "entre", "chez", "comme",
              "tout", "tous", "toute", "être", "avoir", "fait", "sont", "était", "elle", "elles", "nous", "vous", "ceux", "celle",
              "aussi", "très", "même", "encore", "alors", "donc", "ainsi", "puis", "après", "avant", "leurs", "selon", "quand"}


def _racines(txt):
    t = unicodedata.normalize("NFKD", txt.lower().replace("’", "'"))
    t = "".join(c for c in t if not unicodedata.combining(c))
    mots = re.findall(r"[a-z]{4,}", t.replace("l'", " ").replace("d'", " ").replace("qu'", " "))
    sigles = {m.lower() for m in re.findall(r"\b[A-Z]{2,4}\b", txt)}
    return {m[:5] for m in mots if m not in MOTS_VIDES} | sigles


def temps_simules(film):
    """La voix simulée au débit de la vraie (serie/moteur/essai.py) : les ancres en secondes, comme à l'écran."""
    import audio
    import essai
    lead = audio.lead_for(film)
    mots, _ = essai.faux_mots(film)
    f2 = copy.deepcopy(film)
    f2["lead"] = lead
    build.resolve(f2, build.Clock(f2, mots))
    # comme à l'écran : le moteur retarde la caméra d'une planche dont le premier élément tarde (DA v4, « la caméra coupe
    # sur l'action »), et la première planche de la feuille est révélée par le pli
    for zone in ("night", "paper"):
        for st in f2.get(zone, {}).get("stations", []):
            st["_cam_ecrit"] = st.get("cam_at")
    build.couper_sur_action(f2)
    pst = f2.get("paper", {}).get("stations") or []
    if pst and isinstance(f2.get("pivot", {}).get("fold_at"), (int, float)):
        pst[0]["cam_at"] = round(min(float(pst[0]["cam_at"]), f2["pivot"]["fold_at"] + 0.45), 3)
    return f2, mots


def controle_planches(film):
    err = []
    try:
        f2, mots = temps_simules(film)
    except (Exception, SystemExit):      # les ancres illisibles sont déjà signalées ailleurs
        return []
    sents = film["sentences"]
    bornes, i = [], 0
    for s_ in sents:
        n = len(s_["text"].split())
        bornes.append((mots[i]["s"], mots[i + n - 1]["e"]))
        i += n

    def phrase_a(t):
        for k, (a, b) in enumerate(bornes):
            if t <= b + 0.35:
                return k
        return len(bornes) - 1

    def dit(k):
        return sents[k]["text"][:70]

    def temps(o_res, o_org, chemin=""):
        out = []
        if isinstance(o_res, dict):
            for k, v in o_res.items():
                if k in build.TIME_KEYS and k != "cam_at" and isinstance(v, (int, float)):
                    out.append((v, f"{chemin}{k}", o_org.get(k) if isinstance(o_org, dict) else v))
                elif isinstance(v, (dict, list)):
                    out += temps(v, o_org.get(k) if isinstance(o_org, dict) else None, f"{chemin}{k}.")
        elif isinstance(o_res, list):
            for j, v in enumerate(o_res):
                out += temps(v, o_org[j] if isinstance(o_org, list) and j < len(o_org) else None, f"{chemin}{j}.")
        return out

    for zone, fin in (("night", f2["night"]["end"]), ("paper", f2["end"]["fold_at"])):
        sts_r, sts_o = f2[zone]["stations"], film[zone]["stations"]
        for j, (sr, so) in enumerate(zip(sts_r, sts_o)):
            t = sr["type"]
            cam = float(sr["cam_at"])
            end = float(sts_r[j + 1]["cam_at"]) if j + 1 < len(sts_r) else float(fin)
            nom = f"{zone} {j} ({t})"
            # l'accroche est déjà sur la couverture, un moment muet est un clin d'œil : plus courts permis
            mini = 2.0 if t.startswith("gag_") else 2.5 if t == "typo" or t.startswith("hook_") else 3.5
            # la durée écrite (d'un cam_at au suivant), puis la durée réelle une fois la caméra retardée par le moteur
            ecrit = float(sr.get("_cam_ecrit", cam))
            fin_ecrite = float(sts_r[j + 1].get("_cam_ecrit", end)) if j + 1 < len(sts_r) else float(fin)
            if fin_ecrite - ecrit < mini:
                err.append(f"{nom} ne reste que {fin_ecrite - ecrit:.1f} s à l'écran : trop court pour la lire ({mini} s au moins ; laisser la planche "
                           "sur deux phrases ou la regrouper avec la suivante)")
            elif end - cam < mini - 0.9:
                err.append(f"{nom} ne reste que {end - cam:.1f} s à l'écran une fois posée (le moteur fait arriver une planche juste avant son premier "
                           f"élément) : ancrer son premier élément plus tôt, ou la laisser sur deux phrases ({mini - 0.9:.1f} s au moins)")
            ev = temps(sr, so)
            # A. chaque élément apparaît pendant que la planche est à l'écran
            for tt, cle, org in ev:
                if tt < cam - 0.25 or tt > end - 0.15:
                    quand = "avant que la planche arrive" if tt < cam else "après que la caméra est partie"
                    err.append(f"{nom} : « {cle} » = « {org} » tombe {quand} (la planche est à l'écran de la phrase {phrase_a(cam)} à la "
                               f"phrase {phrase_a(max(cam, end - 0.3))}) : l'ancrer sur un mot dit pendant qu'elle est visible")
            # B. l'ordre des gestes suit l'ordre du schéma
            if t == "ai_scan":
                a_, c_, o_ = sr.get("at"), sr.get("core_at"), sr.get("out_at")
                seq = [x for x in (a_, c_, o_) if isinstance(x, (int, float))]
                if seq != sorted(seq):
                    err.append(f"{nom} : « ce qui entre » (at), « l'IA » (core_at) et « ce qui sort » (out_at) doivent apparaître dans cet ordre ; "
                               f"ici at={so.get('at')}, core_at={so.get('core_at')}, out_at={so.get('out_at')}")
            if t == "ratio":
                seq = [x for x in (sr.get("at"), sr.get("ci_at"), sr.get("null_at")) if isinstance(x, (int, float))]
                if seq != sorted(seq):
                    err.append(f"{nom} : le chiffre (at), puis son intervalle (ci_at), puis la ligne à 1 (null_at), dans cet ordre")
            for liste, champ in (("steps", "at"), ("points", "at"), ("items", "at"), ("rows", "at"), ("stages", "at"), ("events", "at")):
                ts = [x.get(champ) for x in sr.get(liste, []) if isinstance(x.get(champ), (int, float))]
                if ts != sorted(ts):
                    err.append(f"{nom} : les éléments de « {liste} » doivent apparaître dans l'ordre où ils sont dessinés")
            # C. jamais de planche vide ni figée pendant que la voix avance
            evt = sorted(x[0] for x in ev if cam - 0.25 <= x[0] <= end)
            if t == "hook_question":
                k = sr.get("_sentence", 0) if "_sentence" in sr else next((q for q, s_ in enumerate(sents) if s_["text"] == so.get("text")), 0)
                deb = sum(len(sents[q]["text"].split()) for q in range(k))
                evt += [w["s"] for w in mots[deb:deb + len(sents[k]["text"].split())]]
            if t == "typo":
                k = next((q for q, s_ in enumerate(sents) if s_["text"] == so.get("text")), None)
                if k is not None:
                    evt += [bornes[k][0], bornes[k][1]]
            if t.startswith("gag_"):
                evt += [cam + 0.5, cam + 1.5, cam + 2.8]      # l'horloge tourne, les jours se barrent, les dossiers tombent
            if t in ("hook_number", "hook_image", "hook_versus", "hook_headline"):
                evt += [cam + 0.3, cam + 1.0]                  # l'en-tête et le chiffre (ou le dessin) arrivent tout de suite
            evt = sorted(set(round(x, 2) for x in evt))
            if not evt:
                evt = [cam + 0.5]
            # la première planche de la feuille est révélée par le pli : le moteur ne peut pas la retarder. Si elle n'arrive pas
            # habillée (fiche, titre, axes), son premier élément est dit dans les 2 premières secondes.
            vide_max = 2.0 if zone == "paper" and j == 0 and t not in build.HABILLEES else 3.5
            if evt[0] - cam > vide_max and t != "typo":
                err.append(f"{nom} : la planche reste vide {evt[0] - cam:.1f} s à son arrivée (la voix dit « {dit(phrase_a(cam + 0.1))}… ») : "
                           "faire apparaître un premier élément sur un mot de cette phrase"
                           + (", ou commencer la feuille par « L'étude en bref » (id_card), qui arrive habillée" if vide_max < 3 else ", ou faire arriver la planche plus tard"))
            pts = [cam] + evt + [end]
            for a_, b_ in zip(pts, pts[1:]):
                if b_ - a_ > 8.0:
                    k = phrase_a(a_ + 0.5)
                    err.append(f"{nom} : rien de nouveau pendant {b_ - a_:.1f} s alors que la voix avance (« {dit(k)}… ») : chaque phrase "
                               "importante a son geste ; ajouter un élément ancré sur cette phrase, un moment muet ou une planche")
                    break
            # D. ce qui s'affiche est ce que la voix dit à ce moment-là
            items = []
            for st_ in sr.get("steps", []) if t in ("steps",) else []:
                items.append((re.sub(r"^\d+\s*·\s*", "", st_.get("label", "")) + " " + st_.get("note", ""), st_.get("at")))
            for pt in sr.get("points", []) if t == "key_points" else []:
                items.append((pt.get("text", ""), pt.get("at")))
            for it in sr.get("items", []) if t == "findings" else []:
                items.append((it.get("label", "") + " " + it.get("detail", ""), it.get("at")))
            for txt, at in items:
                if not isinstance(at, (int, float)):
                    continue
                k = phrase_a(at)
                ctx = " ".join(sents[q].get("display", sents[q]["text"]) + " " + sents[q]["text"] for q in range(max(0, k - 1), min(len(sents), k + 2)))
                if _racines(txt) and not (_racines(txt) & _racines(ctx)) and not (set(re.findall(r"\d+", txt)) & set(re.findall(r"\d+", ctx))):
                    err.append(f"{nom} : « {txt.strip()[:50]} » s'affiche pendant « {dit(k)}… », qui n'en parle pas : un élément apparaît "
                               "au moment où la voix le nomme")
            # E. un rapport (de cotes, de risques…) n'est pas une jauge
            if t == "metric":
                blob = " ".join(str(x) for x in [sr.get("title", ""), sr.get("caption", "")] + [m.get("label", "") + " " + str(m.get("note", "")) for m in sr.get("metrics", [])]).lower()
                if re.search(r"rapport de|odds|\bor\b|\bhr\b|\brr\b|risque relatif|hazard|repère : 1", blob):
                    err.append(f"{nom} : un rapport (de cotes, de risques…) n'est pas une jauge remplie : utiliser la planche « ratio » "
                               "(la valeur, son intervalle et la ligne « aucune différence » à 1)")
    return err


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
    script_md = (jour / "SCRIPT.md").read_text(encoding="utf-8") if (jour / "SCRIPT.md").exists() else ""
    err += controle_recit(film, src, script_md)
    err += controle_planches(film)
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
            if t == "findings":
                its = st.get("items", [])
                if not 2 <= len(its) <= 4:
                    err.append("findings : 2 à 4 constats")
                for it in its:
                    if len(it.get("label", "")) > 34 or len(it.get("detail", "")) > 80:
                        err.append(f"findings : « label » 34 caractères au plus, « detail » 80 au plus ({it.get('label')})")
                    if it.get("tendance") and it["tendance"] not in ("plus", "moins", "pareil"):
                        err.append("findings : tendance = plus, moins ou pareil")
                    if it.get("icon") and it["icon"] not in build.ICONS:
                        err.append(f"findings : icône « {it['icon']} » inconnue")
            if t == "ratio":
                try:
                    lo_, v_, hi_ = float(st.get("low")), float(st.get("num")), float(st.get("high"))
                    if not lo_ <= v_ <= hi_:
                        err.append("ratio : low ≤ num ≤ high (la valeur est dans son intervalle)")
                    if min(lo_, v_, hi_) <= 0:
                        err.append("ratio : un rapport est toujours positif (échelle logarithmique)")
                    if not any(abs(nombre(x) - v_) < 1e-9 for x in NOMBRE.findall(str(st.get("value", "")))):
                        err.append("ratio : « value » (texte affiché) et « num » donnent le même nombre")
                except (TypeError, ValueError):
                    err.append("ratio : low, num et high sont des nombres")
                if len(str(st.get("value", ""))) > 7:
                    err.append("ratio : value de 7 caractères au plus (« 0,59 », « 1,8 »)")
                if len(st.get("label", "")) > 70 or len(st.get("caption", "")) > 46:
                    err.append("ratio : « label » 70 caractères au plus, « caption » 46 au plus")
                if len(st.get("left", "")) > 26 or len(st.get("right", "")) > 26:
                    err.append("ratio : « left » et « right » 26 caractères au plus (« moins de confiance »)")
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
