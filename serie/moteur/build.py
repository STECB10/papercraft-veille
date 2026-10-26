#!/usr/bin/env python3
"""Moteur de la série Papercraft.AI : film.json + onsets.json -> index.html HyperFrames (1080 x 1350, 30 i/s).

Charte : serie/frame.md (v2, « La Revue papier »). Référence animée des planches : serie/reference/planches.html.

Usage : python3 serie/moteur/build.py <projet>
  lit  <projet>/film.json et <projet>/<words_file> (onsets.json de la voix montée)
  écrit <projet>/index.html : une composition, DOM statique, une timeline GSAP en pause (moteur.js)

Les temps de film.json sont des nombres (secondes) ou des ancres sur la voix, résolues ici :
  "s7"              début de la phrase 7 (index dans "sentences", à partir de 0)
  "s7.e"            fin de la phrase 7
  "s7:patients"     début du premier mot « patients » de la phrase 7 (casse et ponctuation ignorées)
  "s7:patients.e"   fin de ce mot
  "s7.w3"           début du 4e mot dit de la phrase 7
  "@IA"             premier mot « IA » du film ; "@IA#2" le deuxième
  + ou - un décalage en secondes : "s7-0.1", "s14:venir+0.2"
Ainsi, quand la voix change, toute l'animation se recale seule.

Les positions ne sont plus écrites dans film.json : le moteur place lui-même les planches (une par cadre sur la
feuille, une par écran dans le papier), le champ « y » éventuel est ignoré.
"""
import difflib
import html
import json
import math
import pathlib
import random
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1350
FOLD_DUR = 1.0      # durée d'un pli (pivot et fin)
PLATE = 1500        # écart entre deux planches du papier (plus qu'un écran : jamais deux planches dans le cadre)
NIGHT_GAP = 520     # air entre deux planches de la feuille posée sur la table
STEP_DY = 360
ML = 72             # marges latérales
CW = W - 2 * ML     # largeur utile

# couleurs (identiques à moteur.css) pour le SVG
INK, INKD, AC, ACD, ACS = "#16171C", "#57544E", "#5D68FF", "#3A44D6", "#A3A9FF"
PAPER, PAPER2, PAPER3, LIFT, PHI = "#ECE6DA", "#DCD4C4", "#C7BDA9", "#F4EFE6", "#F7F3EC"
FAINT = "rgba(22,23,28,.16)"


def esc(s):
    return html.escape(str(s), quote=True)


def fmt_int(n):
    return f"{n:,}".replace(",", " ")


def norm(w):
    return w.replace("’", "'").strip(".,;:!?«»\"()…").lower()


def fr(v, dec):
    s = f"{abs(v):.{dec}f}".replace(".", ",")
    return ("−" if v < 0 else "") + s


def decs(txt):
    """Nombre de décimales d'un nombre écrit à la française (« 0,15 » -> 2)."""
    m = re.search(r",(\d+)", str(txt))
    return len(m.group(1)) if m else 0


def frnum(txt):
    """« −0,09 », « +1,5 », « 12 » -> float."""
    s = str(txt).replace("−", "-").replace(" ", "").replace(" ", "").replace(",", ".")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def parse_ci(txt):
    """Retrouve écart et IC 95 % dans un texte du type « +0,09 · IC 95 % : 0,04 à 0,14 » (anciens film.json)."""
    if not txt or "IC" not in str(txt):
        return None
    s = str(txt)
    num = r"[+−-]?\d+(?:,\d+)?"
    m = re.search(rf"IC\s*(?:à\s*)?95\s*%\s*[:,]?\s*(?:de\s*)?({num})\s*(?:à|–|-|;)\s*({num})", s)
    if not m:
        return None
    head = s[:m.start()]
    v = re.findall(num, head)
    ratio = bool(re.search(r"\b(RR|OR|HR|rapport|odds|risque relatif)\b", s, re.I))
    out = {"low": frnum(m.group(1)), "high": frnum(m.group(2)), "dec": max(decs(m.group(1)), decs(m.group(2))), "null": 1 if ratio else 0}
    if v:
        out["value"] = v[0]
        out["num"] = frnum(v[0])
    else:
        out["value"] = None
        out["num"] = (out["low"] + out["high"]) / 2
    return out


def ci_of(obj):
    """L'écart et son intervalle d'une planche : champ « ci » (nouveau format) ou texte « diff » (ancien format)."""
    ci = obj.get("ci")
    if isinstance(ci, dict) and ci.get("low") is not None and ci.get("high") is not None:
        val = ci.get("value")
        num = float(ci["num"]) if ci.get("num") is not None else frnum(val)
        dec = max(decs(val or ""), decs(str(ci.get("low_label", ""))), 2 if abs(float(ci["high"]) - float(ci["low"])) < 1 else 1)
        return {"value": val, "num": num, "low": float(ci["low"]), "high": float(ci["high"]), "dec": dec,
                "null": float(ci.get("null", 0)), "at": ci.get("at", obj.get("diff_at")), "label": ci.get("label", "Écart"),
                "unit": ci.get("unit", "")}
    p = parse_ci(obj.get("diff"))
    if p:
        p["at"] = obj.get("diff_at")
        p["label"] = "Écart"
        p["unit"] = ""
    return p


# --------------------------------------------------------------------------------------------- ancres
class Clock:
    def __init__(self, film, words):
        self.words = words
        self.sent = []
        i = 0
        for sent in film["sentences"]:
            spoken = sent["text"].split()
            ws = words[i:i + len(spoken)]
            if len(ws) != len(spoken):
                raise SystemExit(f"la voix a moins de mots que le texte (phrase : {sent['text']})")
            for a, b in zip(spoken, ws):
                if norm(a) != norm(b["w"]):
                    raise SystemExit(f"désaccord texte/voix : « {a} » contre « {b['w']} » (phrase : {sent['text']})")
            i += len(spoken)
            sent["_ws"] = ws
            self.sent.append(ws)
        if i != len(words):
            raise SystemExit(f"la voix a {len(words) - i} mot(s) de plus que le texte")

    def t(self, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        m = re.match(r"^(.*?)\s*([+-]\s*\d+(?:\.\d+)?)?$", s)
        base, off = m.group(1), m.group(2)
        off = float(off.replace(" ", "")) if off else 0.0
        if re.match(r"^-?\d+(\.\d+)?$", base):
            return float(base) + off
        end = False
        if base.endswith(".e"):
            base, end = base[:-2], True
        key = "e" if end else "s"
        m = re.match(r"^s(\d+)$", base)
        if m:
            ws = self.sent[int(m.group(1))]
            return (ws[-1]["e"] if end else ws[0]["s"]) + off
        m = re.match(r"^s(\d+)\.w(\d+)$", base)
        if m:
            return self.sent[int(m.group(1))][int(m.group(2))][key] + off
        m = re.match(r"^s(\d+):(.+)$", base)
        if m:
            target = norm(m.group(2))
            for w in self.sent[int(m.group(1))]:
                if norm(w["w"]) == target:
                    return w[key] + off
            raise SystemExit(f"ancre introuvable : {v}")
        m = re.match(r"^@(.+?)(?:#(\d+))?$", base)
        if m:
            target, nth = norm(m.group(1)), int(m.group(2) or 1)
            hits = [w for w in self.words if norm(w["w"]) == target]
            if len(hits) < nth:
                raise SystemExit(f"ancre introuvable : {v}")
            return hits[nth - 1][key] + off
        raise SystemExit(f"ancre illisible : {v}")


TIME_KEYS = {"at", "cam_at", "start", "end", "lit_at", "count_at", "count_end", "split_at", "accent_at", "diff_at",
             "fold_at", "wordmark_at", "button_at", "click_at", "source_at", "note_at", "caption_at", "card_at",
             "door_at", "walk_at", "label_at", "check_at", "mark_at",
             "scan_at", "core_at", "out_at", "total_at", "patients_at",
             "sick_at", "lock_at", "curve_at", "tag_at", "gap_at", "pooled_at"}


def resolve(obj, clock):
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in TIME_KEYS and isinstance(v, (str, int, float)):
                obj[k] = round(clock.t(v), 3)
            elif k != "sentences":
                resolve(v, clock)
    elif isinstance(obj, list):
        for x in obj:
            resolve(x, clock)


ICONS = ["camera", "magnifier", "phone", "chair", "door", "check", "fundus", "doc", "clock", "calendar", "chart", "chip",
         "heart", "pill", "hospital", "eye", "brain", "stethoscope", "user", "users", "message", "xray", "ecg", "skin", "mic"]
IMAGES = ["fundus", "xray", "skin", "mammo", "ct"]
# ce que l'IA lit, déduit de l'icône d'entrée quand film.json ne le dit pas (champ « modality »)
MODALITY = {"fundus": "image", "xray": "image", "skin": "image", "eye": "image", "camera": "image", "magnifier": "image",
            "mic": "voix", "message": "texte", "phone": "texte", "ecg": "signal", "heart": "signal",
            "doc": "donnees", "chart": "donnees", "chip": "donnees", "users": "donnees", "user": "donnees",
            "hospital": "donnees", "calendar": "donnees", "brain": "image", "stethoscope": "signal", "pill": "donnees",
            "clock": "donnees", "check": "donnees", "door": "donnees", "chair": "donnees"}
MODALITIES = ["image", "voix", "texte", "signal", "donnees"]


# --------------------------------------------------------------------------------------------- icônes au trait
def icon(name, stroke="currentColor", sw=3):
    s = f'fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
    if name == "camera":
        return f'<svg viewBox="0 0 120 100" {s}><rect x="10" y="30" width="100" height="56" rx="8"/><path d="M38 30l8-12h28l8 12"/><circle cx="60" cy="58" r="19"/><circle cx="60" cy="58" r="9"/></svg>'
    if name == "magnifier":
        return f'<svg viewBox="0 0 100 100" {s}><circle cx="42" cy="42" r="28"/><path d="M63 63l26 26"/><path d="M28 42a14 14 0 0 1 14-14"/></svg>'
    if name == "phone":
        return f'<svg viewBox="0 0 70 130" {s}><rect x="4" y="4" width="62" height="122" rx="12"/><path d="M27 12h16"/></svg>'
    if name == "chair":
        return f'<svg viewBox="0 0 80 90" {s}><path d="M18 8v44h44"/><path d="M18 52v32M62 52v32"/><path d="M18 30h30"/></svg>'
    if name == "door":
        return f'<svg viewBox="0 0 200 320" {s}><rect x="6" y="6" width="188" height="308"/><circle cx="160" cy="170" r="6"/></svg>'
    if name == "check":
        return f'<svg viewBox="0 0 60 60" {s}><circle cx="30" cy="30" r="26"/><path d="M18 31l8 8 16-18"/></svg>'
    if name == "doc":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M24 8h38l16 16v68H24z"/><path d="M62 8v16h16"/><path d="M34 44h34M34 56h34M34 68h22"/></svg>'
    if name == "clock":
        return f'<svg viewBox="0 0 100 100" {s}><circle cx="50" cy="50" r="40"/><path d="M50 26v24l16 10"/></svg>'
    if name == "calendar":
        return f'<svg viewBox="0 0 100 100" {s}><rect x="12" y="20" width="76" height="68" rx="6"/><path d="M12 38h76M32 10v18M68 10v18"/><path d="M28 54h8M46 54h8M64 54h8M28 70h8M46 70h8"/></svg>'
    if name == "chart":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M12 10v78h80"/><path d="M28 70V52M46 70V36M64 70V44M82 70V22"/></svg>'
    if name == "chip":
        return f'<svg viewBox="0 0 100 100" {s}><rect x="24" y="24" width="52" height="52" rx="6"/><rect x="38" y="38" width="24" height="24" rx="3"/><path d="M36 10v14M50 10v14M64 10v14M36 76v14M50 76v14M64 76v14M10 36h14M10 50h14M10 64h14M76 36h14M76 50h14M76 64h14"/></svg>'
    if name == "heart":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M50 86C20 64 8 48 8 32a20 20 0 0 1 42-10 20 20 0 0 1 42 10c0 16-12 32-42 54z"/><path d="M22 48h16l6-12 10 24 6-12h18"/></svg>'
    if name == "pill":
        return f'<svg viewBox="0 0 100 100" {s}><rect x="10" y="34" width="80" height="32" rx="16" transform="rotate(-35 50 50)"/><path d="M41 37l18 26"/></svg>'
    if name == "hospital":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M14 90V30h72v60"/><path d="M6 90h88"/><path d="M50 40v20M40 50h20"/><path d="M40 90V72h20v18"/></svg>'
    if name == "eye":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M6 50c12-20 28-30 44-30s32 10 44 30c-12 20-28 30-44 30S18 70 6 50z"/><circle cx="50" cy="50" r="14"/></svg>'
    if name == "brain":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M48 16c-10-6-24 0-24 12-12 2-16 16-8 24-6 10 2 24 14 22 2 10 14 14 22 6V16z"/><path d="M52 16c10-6 24 0 24 12 12 2 16 16 8 24 6 10-2 24-14 22-2 10-14 14-22 6"/><path d="M30 40c6 0 10 4 10 10M70 40c-6 0-10 4-10 10M34 66c4-6 10-6 14-4M66 66c-4-6-10-6-14-4"/></svg>'
    if name == "stethoscope":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M22 10v26a18 18 0 0 0 36 0V10"/><path d="M40 54v12a20 20 0 0 0 40 0V58"/><circle cx="80" cy="50" r="8"/></svg>'
    if name == "user":
        return f'<svg viewBox="0 0 100 100" {s}><circle cx="50" cy="32" r="18"/><path d="M16 90c0-20 16-32 34-32s34 12 34 32"/></svg>'
    if name == "users":
        return f'<svg viewBox="0 0 100 100" {s}><circle cx="36" cy="34" r="15"/><path d="M8 88c0-17 13-28 28-28s28 11 28 28"/><circle cx="70" cy="30" r="12"/><path d="M66 56c14-2 28 8 28 26"/></svg>'
    if name == "message":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M12 18h76v52H44L24 86V70H12z"/><path d="M28 38h44M28 52h30"/></svg>'
    if name == "xray":
        return f'<svg viewBox="0 0 100 100" {s}><rect x="10" y="8" width="80" height="84" rx="6"/><path d="M50 18v64"/><path d="M50 30c-10 0-22 4-26 10M50 42c-12 0-24 4-28 12M50 54c-12 0-22 4-26 12M50 30c10 0 22 4 26 10M50 42c12 0 24 4 28 12M50 54c12 0 22 4 26 12"/></svg>'
    if name == "ecg":
        return f'<svg viewBox="0 0 100 100" {s}><rect x="8" y="16" width="84" height="68" rx="6"/><path d="M14 54h18l6-14 8 30 8-36 6 20h26"/></svg>'
    if name == "skin":
        return f'<svg viewBox="0 0 100 100" {s}><path d="M8 62c14-8 28-8 42 0s28 8 42 0"/><path d="M8 78c14-8 28-8 42 0s28 8 42 0"/><circle cx="50" cy="38" r="12"/><path d="M50 14v6M50 56v6M26 38h6M68 38h6"/></svg>'
    if name == "mic":
        return f'<svg viewBox="0 0 100 100" {s}><rect x="36" y="8" width="28" height="52" rx="14"/><path d="M22 46a28 28 0 0 0 56 0"/><path d="M50 74v16M36 90h28"/></svg>'
    if name == "fundus":
        return (f'<svg viewBox="0 0 200 200" fill="none" stroke-linecap="round"><circle cx="100" cy="100" r="92" stroke="{stroke}" stroke-width="{sw}"/>'
                f'<circle cx="132" cy="96" r="15" stroke="{stroke}" stroke-width="{sw}"/><g stroke="{stroke}" stroke-width="{sw*0.7:.1f}" opacity=".8">'
                '<path d="M122 88C100 70 80 52 46 44"/><path d="M120 92C96 86 70 84 30 92"/><path d="M121 104C98 116 72 130 44 156"/>'
                '<path d="M124 108C112 130 100 150 92 182"/><path d="M134 82C138 60 142 40 150 22"/><path d="M140 108C150 128 160 140 174 152"/></g></svg>')
    raise KeyError(name)




def person_svg(x, y, h, color, extra_attrs="", cls="pers"):
    w = h * 0.4
    return (f'<svg class="{cls}" {extra_attrs} style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px" '
            f'viewBox="0 0 40 100"><circle cx="20" cy="13" r="11" fill="{color}"/><path d="M3 100V47a17 17 0 0 1 34 0V100Z" fill="{color}"/></svg>')


# --------------------------------------------------------------------------------------------- images redessinées au trait
# viewBox 0 0 360 360 ; « fill » : la forme de fond, « paths » : (tracé, épaisseur, opacité, remplissage),
# « spots » : ce que l'IA repère (points carbone), « lock » : le cadre des repères (x0, y0, x1, y1)
IMG = {
    "fundus": {
        "fill": '<circle cx="180" cy="180" r="150"/>',
        "paths": [("M180 30a150 150 0 1 0 0.1 0", 2.4, 1, None), ("M229 166a21 21 0 1 0 42 0a21 21 0 1 0 -42 0", 2, 1, None),
                  ("M232 158C205 118 150 100 88 124", 1.8, .75, None), ("M178 112C166 90 150 76 128 66", 1.2, .7, None),
                  ("M232 178C205 220 150 238 88 216", 1.8, .75, None), ("M170 228C162 252 142 268 120 278", 1.2, .7, None),
                  ("M262 150C276 118 290 92 296 70", 1.5, .75, None), ("M264 182C280 214 292 246 294 272", 1.5, .75, None),
                  ("M250 145C246 118 232 86 218 62", 1.2, .7, None), ("M250 187C250 220 240 254 226 290", 1.2, .7, None),
                  ("M135 180a15 15 0 1 0 30 0a15 15 0 1 0 -30 0", 0, 0, "rgba(22,23,28,.1)")],
        "spots": [(128, 200, 5), (142, 214, 5), (118, 218, 4.5), (146, 192, 4)], "lock": (100, 176, 166, 236)},
    "xray": {
        "fill": '<rect x="20" y="20" width="320" height="320" rx="18"/>',
        "paths": [("M70 330C64 250 70 150 112 92C140 60 220 60 248 92C290 150 296 250 290 330", 2.2, 1, None),
                  ("M180 70V330", 5, .3, None),
                  ("M168 96C120 100 92 170 96 300C130 312 160 300 170 280Z", 1.8, .9, None),
                  ("M192 96C240 100 268 170 264 300C230 312 200 300 190 280Z", 1.8, .9, None),
                  ("M178 200C150 205 150 270 190 286C230 290 244 240 214 214Z", 1.4, .7, "rgba(22,23,28,.08)"),
                  ("M120 92C145 82 165 86 178 92", 1.6, .8, None), ("M182 92C195 86 215 82 240 92", 1.6, .8, None)]
                 + [(f"M170 {120+i*30}C140 {108+i*30} 112 {124+i*30} 100 {146+i*30}", 1.3, .5, None) for i in range(5)]
                 + [(f"M190 {120+i*30}C220 {108+i*30} 248 {124+i*30} 260 {146+i*30}", 1.3, .5, None) for i in range(5)],
        "spots": [(128, 170, 8), (139, 183, 4.5)], "lock": (106, 148, 158, 202)},
    "skin": {
        "fill": '<rect x="30" y="60" width="300" height="240" rx="26"/>',
        "paths": [("M40 110C120 100 240 120 320 108", 1.2, .3, None), ("M40 250C120 240 240 262 320 248", 1.2, .3, None),
                  ("M44 290C130 282 230 296 316 286", 1.2, .25, None), ("M44 76C130 70 230 82 316 74", 1.2, .25, None),
                  ("M150 168C152 140 190 132 206 150C224 166 222 196 204 210C186 226 156 218 148 200C140 188 148 178 150 168Z", 2, 1, "rgba(22,23,28,.5)"),
                  ("M176 160C190 156 200 172 192 184C182 194 168 186 170 174Z", 0, 0, "rgba(22,23,28,.35)")],
        "spots": [(152, 166, 4), (214, 196, 4), (170, 214, 4)], "lock": (134, 126, 232, 230)},
    "mammo": {
        "fill": '<path d="M60 40C200 40 300 140 300 220C300 290 230 330 140 330L60 330Z"/>',
        "paths": [("M60 40C200 40 300 140 300 220C300 290 230 330 140 330L60 330Z", 2.2, 1, None),
                  ("M60 40L150 40L60 170", 1.5, .4, None),
                  ("M290 220C230 210 160 190 80 150", 1.3, .5, None), ("M290 226C230 232 160 250 80 270", 1.3, .5, None),
                  ("M292 222C220 220 150 220 80 210", 1.3, .5, None), ("M286 230C230 250 170 290 110 320", 1.2, .4, None),
                  ("M190 240m-14 0a14 14 0 1 0 28 0a14 14 0 1 0 -28 0", 0, 0, "rgba(22,23,28,.22)"),
                  ("M190 222V212M206 228L214 220M208 244H218M190 258V268M174 252L166 260M172 236H162", 1.4, .7, None)],
        "spots": [(190, 240, 7), (199, 233, 3.5)], "lock": (164, 214, 216, 266)},
    "ct": {
        "fill": '<path d="M40 180C40 100 110 60 180 60C250 60 320 100 320 180C320 260 250 300 180 300C110 300 40 260 40 180Z"/>',
        "paths": [("M40 180C40 100 110 60 180 60C250 60 320 100 320 180C320 260 250 300 180 300C110 300 40 260 40 180Z", 2.2, 1, None),
                  ("M70 180C70 120 110 96 160 104C166 150 166 220 156 260C110 266 70 236 70 180Z", 1.8, .9, "#F4EFE6"),
                  ("M290 180C290 120 250 96 200 104C194 150 194 220 204 260C250 266 290 236 290 180Z", 1.8, .9, "#F4EFE6"),
                  ("M162 270a18 18 0 1 0 36 0a18 18 0 1 0 -36 0", 1.8, .8, None),
                  ("M168 170C150 200 160 240 190 246C214 240 214 196 196 172Z", 1.4, .7, "rgba(22,23,28,.1)"),
                  ("M110 132C120 150 116 176 104 196", 1, .4, None), ("M250 132C240 150 244 176 256 196", 1, .4, None)],
        "spots": [(110, 160, 7)], "lock": (90, 140, 130, 180)},
}


def image_svg(name, ink=INK):
    im = IMG.get(name) or IMG["xray"]
    out = [f'<g class="imfill" fill="#E6DCC8" stroke="none">{im["fill"]}</g>']
    for d, sw, op, fill in im["paths"]:
        if sw:
            out.append(f'<path class="imtr" d="{d}" fill="{fill or "none"}" stroke="{ink}" stroke-width="{sw}" stroke-opacity="{op}" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            out.append(f'<path class="imfl" d="{d}" fill="{fill}" stroke="none"/>')
    return "".join(out)


def iconbox(name, x, y, w, h, color, t, a="draw", extra=""):
    return f'<div class="ico" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px;color:{color}" data-a="{a}" data-t="{t:.2f}" {extra}>{icon(name)}</div>'


def svg_layer(x, y, w, h, inner, a=None, t=0.0, extra="", vb=None):
    vb = vb or f"0 0 {w:.0f} {h:.0f}"
    an = f'data-a="{a}" data-t="{t:.2f}"' if a else ""
    return (f'<svg class="lay" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px" viewBox="{vb}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round" {an} {extra}>{inner}</svg>')


def kicker(y0, text, t, fig=None, right=None):
    lab = (f'<span class="fig">Fig. {fig}</span> · ' if fig else "") + esc(text)
    out = [f'<div class="kick" style="left:{ML}px;top:{y0+58}px;width:{CW}px" data-a="rise" data-t="{t:.2f}">{lab}</div>',
           f'<div class="krule" style="left:{ML}px;top:{y0+106}px;width:{CW}px" data-a="wipe" data-t="{t+0.1:.2f}"></div>']
    if right:
        out.append(f'<div class="kick" style="right:{ML+48}px;top:{y0+58}px;text-align:right" data-a="rise" data-t="{t+0.15:.2f}">{esc(right)}</div>')
    return out


def ptitle(y0, text, t):
    """Titre Bodoni de la planche (y 136) ; renvoie (html, bas du titre)."""
    lines = 1 if len(text) <= 34 else 2
    return (f'<div class="ptitle" style="left:{ML}px;top:{y0+132}px;width:{CW}px" data-a="rise" data-t="{t:.2f}">{esc(text)}</div>',
            132 + lines * 64)


def ci_panel(y0, top, ci, t, x0=120, x1=960, label=None):
    """Écart et intervalle de confiance : échelle, ligne « aucun effet », moustache qui grandit, point carbone."""
    h = []
    lo, hi, nul = ci["low"], ci["high"], ci.get("null", 0)
    a, b = min(lo, nul), max(hi, nul)
    pad = (b - a) * 0.28 or 0.5
    d0, d1 = a - pad, b + pad
    X = lambda v: x0 + (v - d0) / (d1 - d0) * (x1 - x0)
    dec = ci.get("dec", 2)
    lab = label or f'{ci.get("label", "Écart")} · intervalle de confiance à 95 %'
    h.append(f'<div class="kick" style="left:{x0:.0f}px;top:{y0+top:.0f}px;width:{x1-x0:.0f}px" data-a="rise" data-t="{t:.2f}">{esc(lab)}</div>')
    ay = top + 150
    h.append(svg_layer(x0 - 10, y0 + ay - 10, x1 - x0 + 20, 20, f'<path d="M10 10H{x1-x0+10:.0f}" stroke="{INK}" stroke-opacity=".45" stroke-width="2.5"/>', "draw", t + 0.05, 'data-d="0.5"'))
    zx = X(nul)
    h.append(f'<div class="zero" style="left:{zx-1.5:.0f}px;top:{y0+ay-62:.0f}px;height:80px" data-a="fade" data-t="{t+0.2:.2f}"></div>')
    # « aucun effet » du côté opposé à l'intervalle : jamais sur la moustache
    if (lo + hi) / 2 >= nul:
        h.append(f'<div class="kick sm" style="right:{W-zx+14:.0f}px;top:{y0+ay-66:.0f}px;text-align:right" data-a="fade" data-t="{t+0.3:.2f}">aucun effet</div>')
    else:
        h.append(f'<div class="kick sm" style="left:{zx+14:.0f}px;top:{y0+ay-66:.0f}px" data-a="fade" data-t="{t+0.3:.2f}">aucun effet</div>')
    wy = ay - 36
    wl, wr = X(lo), X(hi)
    h.append(svg_layer(wl - 4, y0 + wy - 18, wr - wl + 8, 36,
                       f'<path d="M4 18H{wr-wl+4:.0f}M4 4V32M{wr-wl+4:.0f} 4V32" stroke="{ACD}" stroke-width="5"/>', "growc", t + 0.45))
    px = X(ci["num"])
    h.append(f'<div class="cipt" style="left:{px-15:.0f}px;top:{y0+wy-15:.0f}px" data-a="pop" data-t="{t+0.7:.2f}"></div>')
    if ci.get("value"):
        h.append(f'<div class="cival" style="left:{px-120:.0f}px;width:240px;top:{y0+wy-86:.0f}px" data-a="rise" data-t="{t+0.8:.2f}">{esc(ci["value"])}</div>')
    for v, k in ((lo, 0), (hi, 1)):
        h.append(f'<div class="kick" style="left:{X(v)-90:.0f}px;width:180px;top:{y0+ay+18:.0f}px;text-align:center" data-a="rise" data-t="{t+0.9+k*0.1:.2f}">{fr(v, dec)}</div>')
    return h


def annot_note(x, y, w, text, t, cls="annot"):
    return f'<div class="{cls}" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px" data-a="rise" data-t="{t:.2f}">{esc(text)}</div>'


def nice_max(v):
    if v <= 0:
        return 1.0
    e = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * e >= v * 1.08:
            return m * e
    return 10 * e


def ticks_for(top):
    for n in (4, 5, 3):
        step = top / n
        if abs(step * 1000 - round(step * 1000)) < 1e-6:
            return [step * i for i in range(n + 1)]
    return [0, top / 2, top]


def tick_dec(step):
    for d in range(0, 4):
        if abs(step * 10 ** d - round(step * 10 ** d)) < 1e-6:
            return d
    return 3


def inv_norm(p):
    """Inverse de la loi normale (Acklam), pour une courbe ROC schématique tirée de la seule AUC."""
    p = min(max(p, 1e-9), 1 - 1e-9)
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    pl = 0.02425
    if p < pl:
        qq = math.sqrt(-2 * math.log(p))
        return (((((c[0]*qq+c[1])*qq+c[2])*qq+c[3])*qq+c[4])*qq+c[5]) / ((((d[0]*qq+d[1])*qq+d[2])*qq+d[3])*qq+1)
    if p > 1 - pl:
        qq = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*qq+c[1])*qq+c[2])*qq+c[3])*qq+c[4])*qq+c[5]) / ((((d[0]*qq+d[1])*qq+d[2])*qq+d[3])*qq+1)
    qq = p - 0.5
    r = qq * qq
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*qq / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))



# --------------------------------------------------------------------------------------------- sous-titres
def display_times(spoken, disp, ws):
    """Heure d'apparition de chaque mot affiché : alignement sur le texte dit (mot pour mot), les chiffres
    affichés (« 36 % ») prennent le temps des mots qu'ils remplacent (« trente-six pour cent »)."""
    times = [None] * len(disp)
    sm = difflib.SequenceMatcher(None, [norm(w) for w in spoken], [norm(w) for w in disp], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                times[j1 + k] = ws[i1 + k]["s"]
            continue
        if j2 == j1:
            continue
        if i2 > i1:
            t0, t1 = ws[i1]["s"], ws[i2 - 1]["e"]
        else:
            t0 = t1 = ws[i1 - 1]["e"] if i1 > 0 else ws[0]["s"]
        n = j2 - j1
        for k in range(n):
            times[j1 + k] = t0 + (t1 - t0) * k / n
    return times


def build_subs(film, skip=()):
    """Sous-titres mot à mot. Les phrases montrées en grande typo (pivot, nuance, promesse) n'en ont pas :
    le texte n'est jamais affiché deux fois."""
    out = []
    for k_s, sent in enumerate(film["sentences"]):
        if sent.get("mode", "sub") != "sub" or k_s in skip:
            continue
        ws = sent["_ws"]
        disp = sent.get("display", sent["text"]).split()
        times = display_times(sent["text"].split(), disp, ws)
        end = ws[-1]["e"]
        chunks, cur = [], []
        for k, tok in enumerate(disp):
            trial = " ".join(t for t, _ in cur + [(tok, 0)])
            if cur and len(trial) > 30:
                chunks.append(cur)
                cur = []
            cur.append((tok, k))
            if tok.endswith((",", ".")) and len(" ".join(t for t, _ in cur)) > 16 and k < len(disp) - 1:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        box = sent.get("box")
        # le pic est la suite exacte de mots (pas chaque mot isolé : « trop » peut revenir ailleurs dans la phrase)
        peak = [norm(p) for p in sent.get("peak", "").split()]
        dn = [norm(d) for d in disp]
        j0 = next((j for j in range(len(dn) - len(peak) + 1) if peak and dn[j:j + len(peak)] == peak), None)
        peak_idx = set(range(j0, j0 + len(peak))) if j0 is not None else set()
        for c_i, ch in enumerate(chunks):
            t_in = times[ch[0][1]]
            t_out = times[chunks[c_i + 1][0][1]] - 0.02 if c_i + 1 < len(chunks) else end + 0.3
            spans = []
            pk_seen = False
            for tok, k in ch:
                t = times[k]
                if box and tok == box:
                    spans.append(f'<span class="w kw" data-t="{t:.2f}"><span class="bx"></span><span class="tx">{esc(tok)}</span></span>')
                elif k in peak_idx:
                    # le trait part du premier mot du pic dans chaque morceau (un pic peut être coupé entre deux morceaux)
                    first, pk_seen = not pk_seen, True
                    stroke = '<span class="pkline"></span>' if first else ""
                    spans.append(f'<span class="w pk{" pk0" if first else ""}" data-t="{t:.2f}">{esc(tok)}{stroke}</span>')
                else:
                    spans.append(f'<span class="w" data-t="{t:.2f}">{esc(tok)}</span>')
            out.append(f'<div class="chunk light" data-in="{t_in:.2f}" data-out="{t_out:.2f}">{" ".join(spans)}</div>')
    return "\n".join(out)


def typo_words(text, ws, italic):
    toks = text.split()
    spans = []
    for k, tok in enumerate(toks):
        t = ws[min(k, len(ws) - 1)]["s"]
        it = " it" if italic and norm(tok) == norm(italic) else ""
        spans.append(f'<span class="tw{it}" data-t="{t:.2f}">{esc(tok)}</span>')
    return " ".join(spans)


# --------------------------------------------------------------------------------------------- la table : feuille inclinée (le constat)
NIGHT_H = {"hook_number": 860, "gag_waiting": 440, "gag_clock": 470}
NIGHT_DY = {"gag_waiting": 230, "gag_clock": 200, "steps": 40}


def night_height(st):
    if st["type"] == "steps":
        return 170 + 330 * len(st["steps"])
    return NIGHT_H.get(st["type"], 700)


def night_station(st):
    t = st["type"]
    y0 = st["y"]
    h = []
    if t == "hook_number":
        cap = st.get("caption_at", 2.3)
        h.append(f'<div class="mono" style="left:70px;top:{y0+52}px;width:640px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:26px;color:var(--ink-dim)" data-a="rise" data-t="0.35">{esc(st["header"])}</div>')
        h.append(f'<div class="rule" style="left:70px;top:{y0+98}px;width:620px" data-a="wipe" data-t="0.45"></div>')
        h.append(f'<div class="num" style="left:52px;top:{y0+130}px;font-size:280px" data-a="big" data-t="0.02" data-d="1.0">{esc(st["number"])}<span class="unit">{esc(st["unit"])}</span></div>')
        h.append(f'<div class="cap" style="left:72px;top:{y0+440}px;width:600px" data-a="rise" data-t="{cap:.2f}">{esc(st["caption"])}</div>')
        for i in range(st["people"]):
            fade = f' data-o="{st["lit_at"]:.2f}"' if i == st["lit"] else ""
            h.append(person_svg(80 + i * 128, y0 + 570, 170, "var(--ink-faint2)", f'data-a="up" data-t="{0.35 + i*0.09:.2f}"{fade}'))
        lx = 80 + st["lit"] * 128
        h.append(person_svg(lx, y0 + 570, 170, "var(--carbon)", f'data-a="step" data-t="{st["lit_at"]:.2f}"', cls="pers lit"))
        h.append(f'<div class="mono" style="left:72px;top:{y0+776}px;color:var(--ink-dim);font-size:26px" data-a="rise" data-t="{cap+0.6:.2f}">{esc(st["footnote"])}</div>')
    elif t == "gag_waiting":
        ta = st["cam_at"]
        h.append(f'<div class="mono" style="left:500px;top:{y0+40}px;width:240px;text-align:center;color:var(--ink)" data-a="rise" data-t="{ta+0.25:.2f}">{esc(st["door"])}</div>')
        h.append(f'<div class="ico door" style="left:520px;top:{y0+80}px;width:200px;height:320px;color:var(--ink)" data-a="draw" data-t="{ta+0.1:.2f}">{icon("door")}</div>')
        h.append(f'<div class="doorlight" style="left:526px;top:{y0+86}px;width:188px;height:308px" data-a="fade" data-t="{ta+0.6:.2f}"></div>')
        h.append(f'<div class="clock" style="left:220px;top:{y0+60}px" data-a="pop" data-t="{ta+0.3:.2f}"><div class="hand" data-fx="spin" data-t="{ta+0.5:.2f}" data-d="2.4"></div><div class="hand2" data-fx="spin2" data-t="{ta+0.5:.2f}" data-d="2.4"></div><div class="pin"></div></div>')
        for i in range(st["chairs"]):
            h.append(f'<div class="ico" style="left:{60 + i*76}px;top:{y0+330}px;width:72px;height:82px;color:var(--ink-dim)" data-a="pop" data-t="{ta+0.35+i*0.07:.2f}">{icon("chair")}</div>')
        ox = 60 + (st["occupied"] - 1) * 76 + 10
        h.append(person_svg(ox, y0 + 262, 140, "var(--ink-faint2)", f'data-a="up" data-t="{ta+0.9:.2f}" data-fx="wait" data-fxt="{ta+1.3:.2f}"'))
    elif t == "gag_clock":
        ta = st["cam_at"]
        h.append(f'<div class="clock big" style="left:{(780-300)/2:.0f}px;top:{y0+40}px" data-a="pop" data-t="{ta+0.2:.2f}"><div class="hand" data-fx="spin" data-t="{ta+0.4:.2f}" data-d="2.4"></div><div class="hand2" data-fx="spin2" data-t="{ta+0.4:.2f}" data-d="2.4"></div><div class="pin"></div></div>')
        h.append(f'<div class="note" style="left:0;width:780px;text-align:center;top:{y0+380}px" data-a="rise" data-t="{ta+0.9:.2f}">{esc(st["label"])}</div>')
    elif t == "steps":
        ta = st["cam_at"]
        h.append(f'<div class="title" style="left:70px;top:{y0+10}px" data-a="rise" data-t="{ta+0.15:.2f}">{esc(st["title"])}</div>')
        h.append(f'<div class="rule" style="left:72px;top:{y0+92}px;width:620px" data-a="wipe" data-t="{st.get("mark_at", ta+0.9):.2f}"></div>')
        for i, s in enumerate(st["steps"]):
            sy = y0 + 170 + i * 330
            s["_y"] = sy
            at = s["at"]
            tall = s["icon"] == "phone"
            na = s.get("note_at", at + 0.5)
            # l'alerte s'affiche DANS l'écran seulement pour un téléphone ; sinon, à côté de la note (jamais sur l'icône)
            inside = tall and s.get("alert")
            buzz = f'data-fx="buzz" data-fxt="{na:.2f}"' if inside else ""
            alert = f'<div class="alert">{esc(s["alert"])}</div>' if inside else ""
            h.append(f'<div class="ico" style="left:{100 if tall else 84}px;top:{sy}px;width:{100 if tall else 130}px;height:{186 if tall else 110}px;color:var(--ink)" data-a="draw" data-t="{at:.2f}" {buzz}>{icon(s["icon"])}{alert}</div>')
            if inside:
                h.append(f'<svg class="buzzl" style="left:40px;top:{sy+20}px;width:220px;height:150px" viewBox="0 0 220 150" fill="none" stroke="#5D68FF" stroke-width="5" stroke-linecap="round" data-a="fade" data-t="{na:.2f}"><path d="M30 35c-14 24-14 56 0 80"/><path d="M190 35c14 24 14 56 0 80"/></svg>')
            h.append(f'<div class="mono" style="left:270px;top:{sy+8}px;width:470px;color:var(--ink-dim);white-space:normal" data-a="rise" data-t="{at+0.1:.2f}">{esc(s["label"])}</div>')
            ny = sy + 52 if len(s["label"]) <= 30 else sy + 92
            if s.get("note"):
                h.append(f'<div class="note" style="left:266px;top:{ny}px" data-a="rise" data-t="{na:.2f}">{esc(s["note"])}</div>')
            cy = ny + 76
            if s.get("alert") and not inside:
                h.append(f'<div class="chip acc" style="left:270px;top:{cy}px" data-a="pop" data-t="{na+0.25:.2f}">{esc(s["alert"])}</div>')
                cy += 66
            for c_i, c in enumerate(s.get("chips", [])):
                acc = " acc" if c_i == len(s["chips"]) - 1 else ""
                h.append(f'<div class="chip{acc}" style="left:{270 + c_i*96}px;top:{cy}px" data-a="pop" data-t="{na+0.3+c_i*0.2:.2f}">{esc(c)}</div>')
            if i < len(st["steps"]) - 1:
                top = sy + (200 if tall else 128)
                h.append(f'<div class="dash" style="left:147px;top:{top}px;height:{sy+330-top-12}px" data-a="grow" data-t="{st["steps"][i+1]["at"]-0.4:.2f}"></div>')
    return "\n".join(h)



# --------------------------------------------------------------------------------------------- dans la feuille (l'étude)
# Chaque planche est dessinée en coordonnées d'écran (0 à 1350) décalées de y0 : la caméra la cadre plein écran.
FIG_TYPES = {"ai_scan", "result_bars", "result_dots", "result_strips", "metric", "forest_plot", "roc_curve",
             "diagnostic_grid", "survival_curves", "image_scan", "chat"}


def bar_value(x, w, top, g, t, cls="bval", unit=""):
    val = str(g["value"])
    pre = "+" if val.strip().startswith("+") else ""
    return (f'<div class="{cls}" style="left:{x-60:.0f}px;width:{w+120:.0f}px;top:{top:.0f}px" data-a="big" data-t="{t-0.05:.2f}" data-d="0.5">'
            f'<span data-fx="count" data-t="{t:.2f}" data-d="1.0" data-to="{g["num"]}" data-dec="{decs(val)}" data-pre="{pre}">0</span>'
            f'<span class="unit">{esc(unit)}</span></div>')


def wave_bars(x0, y, w, hgt, n, t0, t1, seed):
    rnd = random.Random(seed)
    step = w / n
    out = []
    for i in range(n):
        env = 1 - abs(i - n / 2) / (n * 0.62)
        ks = ",".join(f"{max(0.1, min(1, (0.15 + rnd.random() * 0.85) * env)):.2f}" for _ in range(9)) + ",0.08"
        out.append(f'<div class="wbar" style="left:{x0 + i*step:.0f}px;top:{y:.0f}px;height:{hgt:.0f}px" data-fx="wave" data-t="{t0:.2f}" data-d="{max(0.6, t1 - t0):.2f}" data-k="{ks}" data-ap="{t0 - 0.3 + i*0.01:.2f}"></div>')
    return out


def ecg_path(w, hgt, beats):
    seg = w / beats
    d = f"M0 {hgt*0.6:.0f}"
    for b in range(beats):
        x = b * seg
        d += (f" L{x+seg*0.30:.0f} {hgt*0.6:.0f} L{x+seg*0.36:.0f} {hgt*0.5:.0f} L{x+seg*0.42:.0f} {hgt*0.6:.0f}"
              f" L{x+seg*0.50:.0f} {hgt*0.6:.0f} L{x+seg*0.54:.0f} {hgt*0.68:.0f} L{x+seg*0.58:.0f} {hgt*0.05:.0f}"
              f" L{x+seg*0.63:.0f} {hgt*0.85:.0f} L{x+seg*0.67:.0f} {hgt*0.6:.0f} L{x+seg*0.80:.0f} {hgt*0.6:.0f}"
              f" Q{x+seg*0.87:.0f} {hgt*0.38:.0f} {x+seg*0.94:.0f} {hgt*0.6:.0f}")
    return d + f" L{w:.0f} {hgt*0.6:.0f}"


def network(x, y, s, t, pulse_at, lit=True):
    pts = [(.5, .12), (.14, .38), (.86, .38), (.25, .84), (.75, .84), (.5, .5)]
    edges = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (1, 0), (2, 4), (3, 4)]
    lines = "".join(f'<path d="M{pts[a][0]*s:.0f} {pts[a][1]*s:.0f}L{pts[b][0]*s:.0f} {pts[b][1]*s:.0f}" stroke="{ACS}" stroke-opacity=".6" stroke-width="2.4"/>' for a, b in edges)
    out = [svg_layer(x, y, s, s, lines, "draw", t + 0.15, 'data-d="0.4" data-stg="0.05"')]
    for i, (px, py) in enumerate(pts):
        r = 15 if i == 5 else 9
        col = AC if i == 5 else ACS
        extra = f'data-fx="pulse" data-fxt="{pulse_at:.2f}"' if i == 5 else ""
        out.append(f'<div class="nd" style="left:{x+px*s-r:.0f}px;top:{y+py*s-r:.0f}px;width:{2*r}px;height:{2*r}px;background:{col}" data-a="pop" data-t="{t + i*0.06:.2f}" {extra}></div>')
    return out


def corners(x0, y0, x1, y1, L=26, sw=6, col=AC):
    p = (f"M{x0} {y0+L}V{y0}H{x0+L}M{x1-L} {y0}H{x1}V{y0+L}M{x1} {y1-L}V{y1}H{x1-L}M{x0+L} {y1}H{x0}V{y1-L}")
    return f'<path d="{p}" stroke="{col}" stroke-width="{sw}"/>'


def paper_station(st, film, fig=None):
    t = st["type"]
    y0 = st["y"]
    t0 = st.get("cam_at", 0)
    h = []

    if t == "id_card":
        # fiche bristol posée et scotchée : marge carbone, lignes réglées, une ligne par information
        rows = st["rows"]
        n = len(rows)
        rh = min(170, 760 / n)
        ch = 150 + n * rh
        cy = 150 + (880 - ch) / 2
        fs = 54 if n <= 5 else 46
        h.append(f'<div class="bristol" style="left:{ML}px;top:{y0+cy:.0f}px;width:{CW}px;height:{ch:.0f}px" data-a="hingeT" data-t="{t0+0.15:.2f}"></div>')
        h.append(f'<div class="tape" style="left:{W/2-110:.0f}px;top:{y0+cy-26:.0f}px" data-a="pop" data-t="{t0+0.5:.2f}"></div>')
        h.append(f'<div class="kick" style="left:{ML+48}px;top:{y0+cy+44:.0f}px" data-a="rise" data-t="{t0+0.45:.2f}"><span class="fig">{esc(st.get("title", "L\'étude en bref"))}</span></div>')
        h.append(f'<div class="bmargin" style="left:{ML+290}px;top:{y0+cy+110:.0f}px;height:{ch-140:.0f}px" data-a="grow" data-t="{t0+0.55:.2f}"></div>')
        for i, r in enumerate(rows):
            ry = y0 + cy + 110 + i * rh
            acc = " acc" if r.get("accent") else ""
            h.append(f'<div class="hair blue" style="left:{ML+30}px;top:{ry+rh-10:.0f}px;width:{CW-60}px" data-a="wipe" data-t="{t0+0.6+i*0.06:.2f}"></div>')
            h.append(f'<div class="kick" style="left:{ML+48}px;top:{ry+rh/2-30:.0f}px;width:225px" data-a="rise" data-t="{r["at"]-0.05:.2f}">{esc(r["label"])}</div>')
            h.append(f'<div class="idv{acc}" style="left:{ML+320}px;top:{ry+rh/2-fs*0.62:.0f}px;width:{CW-350}px;font-size:{fs}px" data-a="print" data-t="{r["at"]:.2f}">{esc(r["value"])}</div>')

    elif t == "ai_scan":
        at = st["at"]
        sa = st.get("scan_at", at + 0.8)
        ca = st.get("core_at", sa + 0.3)
        oa = st.get("out_at", ca + 1.4)
        mod = st.get("modality") or MODALITY.get(st.get("input_icon", "doc"), "donnees")
        h += kicker(y0, st.get("title", "Ce que fait l'IA"), t0 + 0.2, fig)
        # 1. ce qui entre
        h.append(iconbox(st.get("input_icon", "doc"), ML + 8, y0 + 168, 160, 160, "var(--ink)", at))
        h.append(f'<div class="kick" style="left:290px;top:{y0+168}px" data-a="rise" data-t="{at+0.1:.2f}">Ce qui entre</div>')
        h.append(f'<div class="ailab" style="left:290px;top:{y0+206}px;width:{W-ML-290}px" data-a="print" data-t="{at+0.2:.2f}">{esc(st["input_label"])}</div>')
        gy = y0 + 330
        if mod == "image":
            h.append(f'<div class="bandclip" style="left:{ML}px;top:{y0+160}px;width:176px;height:176px"><div class="band h" data-fx="band" data-t="{sa:.2f}" data-d="1.1" data-y0="-40" data-y1="176"></div></div>')
            h.append(svg_layer(ML - 8, y0 + 152, 208, 208, corners(4, 4, 204, 204, 30, 6), "lock", sa + 1.0))
            h.append(f'<div class="kick acc" style="left:290px;top:{gy+18}px" data-a="rise" data-t="{sa+1.1:.2f}">L\'image est lue point par point</div>')
        elif mod == "voix":
            h += wave_bars(290, gy, W - ML - 290, 74, 40, at + 0.1, ca, 3)
        elif mod == "signal":
            h.append(svg_layer(290, gy, W - ML - 290, 80, "".join(f'<path d="M0 {k*20}H{W-ML-290}" stroke="{INK}" stroke-opacity=".08" stroke-width="1"/>' for k in range(5))
                               + f'<path d="{ecg_path(W-ML-290, 80, 5)}" stroke="{INK}" stroke-width="3"/>', "draw", at + 0.2, 'data-d="1.6" data-ease="none"'))
        elif mod == "texte":
            h.append(f'<div class="bub hu" style="left:290px;top:{gy}px;width:330px;height:74px" data-a="pop" data-t="{at+0.3:.2f}"><i class="skl" style="width:240px;top:22px" data-a="growx" data-t="{at+0.45:.2f}"></i><i class="skl" style="width:170px;top:42px" data-a="growx" data-t="{at+0.6:.2f}"></i></div>')
            h.append(f'<div class="bub ia" style="left:640px;top:{gy+20}px;width:{W-ML-640}px;height:74px" data-a="pop" data-t="{sa:.2f}"><i class="skl lt" style="width:250px;top:22px" data-a="growx" data-t="{sa+0.15:.2f}"></i><i class="skl lt" style="width:180px;top:42px" data-a="growx" data-t="{sa+0.3:.2f}"></i></div>')
        else:
            for k in range(3):
                ry = gy + k * 28
                for c in range(4):
                    h.append(f'<i class="skl cell" style="left:{290 + c*172}px;top:{ry}px;width:{[120, 90, 140, 70][(c+k) % 4]}px" data-a="growx" data-t="{at+0.2+k*0.1+c*0.03:.2f}"></i>')
            h.append(f'<div class="rowhi" style="left:280px;top:{gy+24}px;width:{W-ML-280}px" data-a="wipe" data-t="{sa:.2f}"></div>')
        # 2. l'IA
        h.append(svg_layer(ML + 70, y0 + 424, 36, 100, f'<path d="M18 4V92M8 80L18 92L28 80" stroke="{INK}" stroke-width="3"/>', "draw", ca - 0.45, 'data-d="0.4"'))
        h.append(f'<div class="aicore" style="left:{ML}px;top:{y0+534}px;width:{CW}px;height:250px" data-a="pop" data-t="{ca-0.1:.2f}">'
                 f'<div class="band v" data-fx="band" data-t="{ca+0.6:.2f}" data-d="1.0" data-x0="-80" data-x1="{CW}"></div></div>')
        h += network(ML + 40, y0 + 569, 180, ca, ca + 0.7)
        ai_name = st.get("ai_name", "L'IA")
        h.append(f'<div class="kick lt" style="left:{ML+270}px;top:{y0+584}px" data-a="rise" data-t="{ca+0.1:.2f}">{esc(ai_name)}</div>')
        h.append(f'<div class="ailab lt" style="left:{ML+270}px;top:{y0+624}px;width:{CW-310}px" data-a="print" data-t="{ca+0.25:.2f}">{esc(st["ai_label"])}</div>')
        # 3. ce qui sort
        h.append(svg_layer(ML + 70, y0 + 792, 36, 96, f'<path d="M18 4V88M8 76L18 88L28 76" stroke="{INK}" stroke-width="3"/>', "draw", oa - 0.4, 'data-d="0.35"'))
        h.append(iconbox("check", ML + 18, y0 + 900, 104, 104, "var(--carbon-deep)", oa + 0.1))
        h.append(f'<div class="kick acc" style="left:240px;top:{y0+898}px" data-a="rise" data-t="{oa:.2f}">Ce qui sort</div>')
        out = st["output_label"]
        h.append(f'<div class="oout" style="left:240px;top:{y0+934}px;width:{W-ML-240}px" data-a="print" data-t="{oa+0.1:.2f}">{esc(out)}</div>')
        uw = min(W - ML - 240, 26 * len(out) + 20)
        h.append(svg_layer(236, y0 + 1006, uw + 8, 18, f'<path d="M4 12C{uw*0.3:.0f} 4 {uw*0.6:.0f} 14 {uw+4:.0f} 6" stroke="{AC}" stroke-width="6"/>', "draw", oa + 0.55, 'data-d="0.6"'))
        if st.get("output_note"):
            h.append(f'<div class="kick" style="left:240px;top:{y0+1030}px;width:{W-ML-240}px" data-a="rise" data-t="{oa+0.8:.2f}">{esc(st["output_note"])}</div>')

    elif t == "population_split":
        ct, sp = st["count_at"], st["split_at"]
        cd = max(0.8, st.get("count_end", ct + 1.4) - ct)
        dv = int(st.get("dot_value", 1) or 1)
        n = round(st["total"] / dv)
        g0, g1 = st["groups"]
        n0 = min(n, round(g0["n"] / dv))
        acc_t = g1.get("accent_at", sp + 1)
        h.append(f'<div class="num center" style="left:0;width:{W}px;top:{y0+110}px;font-size:150px" data-a="big" data-t="{ct-0.05:.2f}" data-d="0.55"><span data-fx="count" data-t="{ct:.2f}" data-d="{cd:.2f}" data-to="{st["total"]}" data-dec="0">0</span></div>')
        h.append(f'<div class="kick center" style="left:0;width:{W}px;top:{y0+276}px" data-a="rise" data-t="{ct+0.5:.2f}">{esc(st["total_label"])}</div>')
        sil = n <= 60
        rnd = random.Random(7)
        perm = list(range(n))
        rnd.shuffle(perm)
        left = set(perm[:n0])
        if sil:
            fw, fh = 42, 78
            cols = 9 if n <= 54 else 10
            cw_, ch_ = 78, 102
            gx0 = (W - cols * cw_) / 2 + (cw_ - fw) / 2
            gy0 = y0 + 380
            cc = 5 if max(n0, n - n0) <= 30 else 6
            ccw, cch = (64, 84) if cc == 5 else (58, 78)
            cxs = [72 + (430 - cc * ccw) / 2 + (ccw - fw) / 2, 578 + (430 - cc * ccw) / 2 + (ccw - fw) / 2]
            cy0 = y0 + 540
        else:
            cell = max(14.0, min(40.0, math.sqrt(936 * 520 / n)))
            fw = fh = cell * 0.62
            cols = int(936 // cell)
            cw_ = ch_ = cell
            gx0 = (W - cols * cell) / 2 + (cell - fw) / 2
            gy0 = y0 + 380
            cc = max(1, int(430 // cell))
            ccw = cch = cell
            cxs = [72 + (430 - cc * cell) / 2 + (cell - fw) / 2, 578 + (430 - cc * cell) / 2 + (cell - fw) / 2]
            cy0 = y0 + 540
        li = ri = 0
        for i in range(n):
            x = gx0 + (i % cols) * cw_
            y = gy0 + (i // cols) * ch_
            if i in left:
                tx, ty, side = cxs[0] + (li % cc) * ccw, cy0 + (li // cc) * cch, 0
                li += 1
            else:
                tx, ty, side = cxs[1] + (ri % cc) * ccw, cy0 + (ri // cc) * cch, 1
                ri += 1
            dl = rnd.uniform(0, 0.35)
            ap = ct + 0.1 + (i / max(1, n)) * min(cd, 1.4) * 0.9 + rnd.uniform(0, 0.1)
            col_t = f'{acc_t + dl*0.7:.2f}' if side else "-1"
            kind = "sil" if sil else "pdot"
            inner = "<i></i><b></b>" if sil else ""
            h.append(f'<div class="{kind}" style="left:{x:.0f}px;top:{y:.0f}px;width:{fw:.0f}px;height:{fh:.0f}px" data-fx="split" data-t="{ap:.2f}" data-in="{"up" if sil else "dot"}" '
                     f'data-mt="{sp+dl:.2f}" data-dx="{tx-x:.0f}" data-dy="{ty-y:.0f}" data-ct="{col_t}">{inner}</div>')
        for k, (g, nn) in enumerate(((g0, n0), (g1, n - n0))):
            x = 72 if k == 0 else 578
            acc = " acc" if k == 1 else ""
            h.append(f'<div class="gtab{acc}" style="left:{x}px;top:{y0+380}px;width:430px;height:118px" data-a="hingeT" data-t="{sp+0.45+k*0.12:.2f}">'
                     f'<span class="gl">{esc(g["label"])}</span><span class="gn">{fmt_int(g["n"])}</span></div>')
        if dv > 1:
            h.append(f'<div class="kick center" style="left:0;width:{W}px;top:{y0+1020}px" data-a="rise" data-t="{ct+0.9:.2f}">1 point = {dv} patients</div>')

    elif t == "two_groups":
        cols = st["groups"]
        cwid = (CW - 36) / 2
        for gi, g in enumerate(cols):
            x0 = ML + gi * (cwid + 36)
            acc = " acc" if g.get("accent") else ""
            h.append(f'<div class="gcard" style="left:{x0:.0f}px;top:{y0+150}px;width:{cwid:.0f}px;height:900px" data-a="pop" data-t="{g["at"]:.2f}"></div>')
            h.append(f'<div class="gtab{acc}" style="left:{x0:.0f}px;top:{y0+150}px;width:{cwid:.0f}px;height:96px" data-a="hingeT" data-t="{g["at"]+0.1:.2f}"><span class="gl">{esc(g["label"])}</span></div>')
            top = 300
            if g.get("sub"):
                h.append(f'<div class="kick" style="left:{x0+30:.0f}px;top:{y0+270}px;width:{cwid-60:.0f}px" data-a="rise" data-t="{g["at"]+0.25:.2f}">{esc(g["sub"])}</div>')
                top = 340
            ns = len(g["steps"])
            gap = min(240, (1010 - top) / ns)
            colr = "var(--carbon-deep)" if g.get("accent") else "var(--ink)"
            for k, stp in enumerate(g["steps"]):
                sy = y0 + top + k * gap
                h.append(iconbox(stp.get("icon", "doc"), x0 + 30, sy, 80, 80, colr, stp["at"]))
                h.append(f'<div class="gstep" style="left:{x0+134:.0f}px;top:{sy+4:.0f}px;width:{cwid-160:.0f}px" data-a="print" data-t="{stp["at"]+0.05:.2f}">{esc(stp["text"])}</div>')
                if k < ns - 1:
                    h.append(f'<div class="dash" style="left:{x0+68:.0f}px;top:{sy+96:.0f}px;height:{gap-112:.0f}px" data-a="grow" data-t="{g["steps"][k+1]["at"]-0.35:.2f}"></div>')

    elif t in ("result_bars", "result_strips"):
        gs = st["groups"]
        ng = len(gs)
        ci = ci_of(st)
        unit = st.get("unit", "")
        strips = t == "result_strips"
        if not strips:
            h += kicker(y0, "Résultat", t0 + 0.25, fig)
            tt, tb = ptitle(y0, st["title"], t0 + 0.35)
            h.append(tt)
        else:
            h.append(f'<div class="lsheet" style="left:54px;top:{y0+52}px;width:972px;height:1000px" data-a="pop" data-t="{t0+0.1:.2f}"></div>')
            h.append(f'<div class="kick" style="left:110px;top:{y0+100}px;width:560px" data-a="rise" data-t="{t0+0.3:.2f}"><span class="fig">Fig. {fig}</span> · {esc(st["title"])}</div>')
            tb = 250
        base = y0 + (700 if not strips else 800)
        vmax = max(float(g["num"]) for g in gs) or 1
        top_v = nice_max(vmax)
        hmax = (700 - (tb + 130)) if not strips else 420
        bw = 180 if ng == 2 else 140
        gap = 168 if ng == 2 else 80
        block = ng * bw + (ng - 1) * gap
        px0, pw = (170, 730) if not strips else (162, 756)
        xs0 = px0 + (pw - block) / 2
        Y = lambda v: base - hmax * float(v) / top_v
        if not strips:
            tk = ticks_for(top_v)
            dec = tick_dec(tk[1] - tk[0]) if len(tk) > 1 else 0
            grid = "".join(f'<path d="M0 {Y(v)-base+hmax+2:.0f}H{900-150}" stroke="{INK}" stroke-opacity=".16" stroke-width="1.5" stroke-dasharray="4 7"/>' for v in tk[1:])
            h.append(svg_layer(150, base - hmax - 2, 750, hmax + 4, grid, "fade", t0 + 0.4))
            for k, v in enumerate(tk):
                h.append(f'<div class="kick sm" style="left:40px;width:96px;top:{Y(v)-14:.0f}px;text-align:right" data-a="fade" data-t="{t0+0.45+k*0.04:.2f}">{fr(v, dec)}</div>')
            h.append(svg_layer(146, base - 3, 760, 6, f'<path d="M2 3H758" stroke="{INK}" stroke-width="3"/>', "draw", t0 + 0.5, 'data-d="0.5"'))
        else:
            h.append(f'<div class="slot" style="left:162px;top:{base-3:.0f}px;width:756px" data-a="growc" data-t="{t0+0.4:.2f}"></div>')
        for gi, g in enumerate(gs):
            x = xs0 + gi * (bw + gap)
            hgt = max(10, base - Y(g["num"]))
            acc = " acc" if g.get("accent") else ""
            if strips:
                h.append(f'<div class="strip{acc}" style="left:{x:.0f}px;top:{base-hgt:.0f}px;width:{bw}px;height:{hgt:.0f}px" data-a="hingeB" data-t="{g["at"]:.2f}">'
                         f'<div class="sval{acc}"><span data-fx="count" data-t="{g["at"]+0.1:.2f}" data-d="0.8" data-to="{g["num"]}" data-dec="{decs(g["value"])}" data-pre="{"+" if str(g["value"]).startswith("+") else ""}">0</span>{esc(unit)}</div></div>')
            else:
                h.append(f'<div class="bar{acc}" style="left:{x:.0f}px;top:{base-hgt:.0f}px;width:{bw}px;height:{hgt:.0f}px" data-a="growup" data-t="{g["at"]:.2f}"></div>')
                h.append(bar_value(x, bw, base - hgt - 90, g, g["at"], "bval" + acc, unit))
            lw = bw + gap - 16
            h.append(f'<div class="kick{acc} center" style="left:{x+bw/2-lw/2:.0f}px;width:{lw:.0f}px;top:{base+22:.0f}px" data-a="rise" data-t="{g["at"]+0.3:.2f}">{esc(g["label"])}</div>')
        nums = [float(g["num"]) for g in gs]
        ann = (ci or {}).get("value") or (st.get("diff") if st.get("diff") and len(st["diff"]) <= 8 else None)
        ann_at = ((ci or {}).get("at") or st.get("diff_at") or (max(g["at"] for g in gs) + 1.0))
        if strips and (ci or st.get("diff")):
            h.append(f'<div class="pin" style="left:842px;top:{y0+96}px" data-a="pop" data-t="{ann_at:.2f}"></div>')
            h.append(f'<div class="string" style="left:851px;top:{y0+112}px;height:56px" data-a="grow" data-t="{ann_at+0.1:.2f}"></div>')
            body = f'<span class="kick">Écart</span><span class="tagv">{esc(ann or "")}</span>'
            if ci:
                body += f'<span class="kick sm">IC 95 % : {fr(ci["low"], ci["dec"])} à {fr(ci["high"], ci["dec"])}</span>'
            elif st.get("diff"):
                body = f'<span class="kick">Écart</span><span class="kick acc">{esc(st["diff"])}</span>'
            h.append(f'<div class="tag" style="left:618px;top:{y0+166}px;width:400px" data-a="hingeT" data-t="{ann_at+0.25:.2f}">{body}</div>')
        elif not strips and ng == 2 and (ann or ci):
            hi_i, lo_i = nums.index(max(nums)), nums.index(min(nums))
            bx = xs0 + block + 30
            yhi, ylo = Y(nums[hi_i]), Y(nums[lo_i])
            lo_x = xs0 + lo_i * (bw + gap) + bw
            h.append(svg_layer(lo_x, ylo - 3, bx - lo_x + 4, 6, f'<path d="M2 3H{bx-lo_x+2:.0f}" stroke="{INKD}" stroke-width="2.5" stroke-dasharray="6 6"/>', "draw", ann_at - 0.3, 'data-d="0.35"'))
            h.append(svg_layer(bx - 26, yhi - 3, 34, ylo - yhi + 6, f'<path d="M4 3H24V{ylo-yhi+3:.0f}H4" stroke="{ACD}" stroke-width="4"/>', "draw", ann_at - 0.05, 'data-d="0.4"'))
            if ann:
                fs = 60 if len(ann) <= 6 else 44
                h.append(f'<div class="annot" style="left:{bx+14:.0f}px;top:{(yhi+ylo)/2-fs*0.6:.0f}px;font-size:{fs}px" data-a="rise" data-t="{ann_at+0.2:.2f}">{esc(ann)}</div>')
        if not strips:
            if ci:
                h += ci_panel(y0, 818, ci, ann_at + 0.6)
            elif st.get("diff") and not ann:
                h.append(f'<div class="pillwrap" style="left:0;width:{W}px;top:{y0+840}px" data-a="pop" data-t="{ann_at:.2f}"><span class="pill acc">{esc(st["diff"])}</span></div>')

    elif t == "result_dots":
        gs = st["groups"]
        ci = ci_of(st)
        h += kicker(y0, "Résultat", t0 + 0.25, fig)
        tt, tb = ptitle(y0, st["title"], t0 + 0.35)
        h.append(tt)
        unit = st.get("unit", "%")
        bottom = 0
        for gi, g in enumerate(gs[:2]):
            x0 = ML if gi == 0 else 578
            acc = " acc" if g.get("accent") else ""
            n, k = int(g["n"]), int(g["k"])
            h.append(f'<div class="glab{acc}" style="left:{x0}px;width:430px;top:{y0+tb+26}px" data-a="rise" data-t="{t0+0.5+gi*0.1:.2f}">{esc(g["label"])}</div>')
            cell = max(10.0, min(56.0, math.sqrt(430 * 300 / max(1, n))))
            cols = max(1, int(430 // cell))
            rows = math.ceil(n / cols)
            r = cell * 0.34
            gw = cols * cell
            dx0 = x0 + (430 - gw) / 2
            dy0 = y0 + tb + 90
            rnd = random.Random(11 + gi)
            base, lit = [], []
            for i in range(n):
                cx = (i % cols) * cell + cell / 2
                cy = (i // cols) * cell + cell / 2
                base.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{INK}" fill-opacity=".14" data-fx0="{rnd.uniform(-300, 300):.0f}" data-fy0="{rnd.uniform(-260, 160):.0f}" data-ap="{rnd.uniform(0, 0.6):.2f}"/>')
                if i < k:
                    lit.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{AC if g.get("accent") else INK}"/>')
            hp = rows * cell
            h.append(f'<svg class="lay" style="left:{dx0:.0f}px;top:{dy0:.0f}px;width:{gw:.0f}px;height:{hp:.0f}px;overflow:visible" viewBox="0 0 {gw:.0f} {hp:.0f}" data-fx="flydots" data-t="{t0+0.5+gi*0.15:.2f}">{"".join(base)}</svg>')
            h.append(f'<svg class="lay" style="left:{dx0:.0f}px;top:{dy0:.0f}px;width:{gw:.0f}px;height:{hp:.0f}px" viewBox="0 0 {gw:.0f} {hp:.0f}" data-fx="litdots" data-t="{g["at"]:.2f}" data-d="1.0">{"".join(lit)}</svg>')
            vy = dy0 + hp + 20
            h.append(f'<div class="bval{acc}" style="left:{x0}px;width:430px;top:{vy:.0f}px;font-size:100px" data-a="big" data-t="{g["at"]-0.05:.2f}" data-d="0.5">'
                     f'<span data-fx="count" data-t="{g["at"]:.2f}" data-d="1.0" data-to="{g["num"] if "num" in g else frnum(g["value"])}" data-dec="{decs(g["value"])}">0</span><span class="unit">{esc(unit)}</span></div>')
            h.append(f'<div class="kick{acc} center" style="left:{x0}px;width:430px;top:{vy+118:.0f}px" data-a="rise" data-t="{g["at"]+0.3:.2f}">{k} sur {fmt_int(n)}</div>')
            bottom = max(bottom, vy + 150 - y0)
        ann_at = (ci or {}).get("at") or st.get("diff_at") or (max(g["at"] for g in gs) + 1.0)
        if ci and bottom <= 820:
            h += ci_panel(y0, max(bottom + 20, 820), ci, ann_at)
        elif st.get("diff"):
            h.append(f'<div class="pillwrap" style="left:0;width:{W}px;top:{y0+min(960, bottom+40):.0f}px" data-a="pop" data-t="{ann_at:.2f}"><span class="pill acc">{esc(st["diff"])}</span></div>')

    elif t == "metric":
        ms = st["metrics"]
        m = len(ms)
        h += kicker(y0, "Mesures", t0 + 0.25, fig)
        tt, tb = ptitle(y0, st["title"], t0 + 0.35)
        h.append(tt)
        top = tb + 50
        rh = min(300, (1030 - top) / m)
        big = m == 1
        if big:
            top = tb + 170
        for i, g in enumerate(ms):
            ry = y0 + top + i * rh
            mx = float(g.get("max", 100))
            frac = max(0.0, min(1.0, float(g["num"]) / mx))
            acc = g.get("accent", i == 0)
            a = " acc" if acc else ""
            h.append(f'<div class="mlab{a}" style="left:{ML}px;top:{ry:.0f}px;width:470px" data-a="rise" data-t="{g["at"]-0.1:.2f}">{esc(g["label"])}</div>')
            val = str(g["value"])
            h.append(f'<div class="mval{a}" style="left:{ML if big else 460}px;width:{CW if big else W-ML-460}px;top:{ry+(150 if big else -30):.0f}px;{"text-align:left;font-size:220px" if big else ""}" data-a="big" data-t="{g["at"]-0.05:.2f}" data-d="0.5">'
                     f'<span data-fx="count" data-t="{g["at"]:.2f}" data-d="1.0" data-to="{g["num"]}" data-dec="{decs(val)}" data-pre="{"+" if val.startswith("+") else ""}">0</span><span class="unit">{esc(g.get("unit", ""))}</span></div>')
            if big:
                ry += 290
            h.append(f'<div class="track" style="left:{ML}px;top:{ry+128:.0f}px;width:{CW}px" data-a="wipe" data-t="{g["at"]-0.2:.2f}"></div>')
            cip = parse_ci(g.get("note"))
            if cip:
                lo, hi = max(0, cip["low"] / mx), min(1, cip["high"] / mx)
                h.append(f'<div class="ciband" style="left:{ML + lo*CW:.0f}px;top:{ry+114:.0f}px;width:{max(6, (hi-lo)*CW):.0f}px" data-a="growc" data-t="{g["at"]+0.9:.2f}"></div>')
            h.append(f'<div class="tfill{a}" style="left:{ML}px;top:{ry+124:.0f}px;width:{max(8, frac*CW):.0f}px" data-a="fill" data-t="{g["at"]:.2f}"></div>')
            if g.get("note"):
                h.append(f'<div class="kick{a}" style="left:{ML}px;top:{ry+156:.0f}px;width:{CW}px" data-a="rise" data-t="{g["at"]+0.4:.2f}">{esc(g["note"])}</div>')
        if st.get("caption"):
            h.append(f'<div class="cap" style="left:{ML}px;top:{y0+min(1010, top + m*rh):.0f}px;width:{CW}px;color:var(--ink-dim)" data-a="rise" data-t="{st.get("caption_at", ms[-1]["at"] + 0.8):.2f}">{esc(st["caption"])}</div>')

    elif t == "key_points":
        pts = st["points"]
        n = len(pts)
        h += kicker(y0, st.get("title", "Ce qu'il faut retenir"), t0 + 0.25)
        rh = min(290, 880 / n)
        for i, pt in enumerate(pts):
            ry = y0 + 160 + i * rh
            h.append(f'<div class="kpn" style="left:{ML}px;top:{ry+6:.0f}px" data-a="big" data-t="{pt["at"]-0.05:.2f}" data-d="0.5">{i + 1}</div>')
            h.append(f'<div class="kpt" style="left:210px;top:{ry+28:.0f}px;width:{W-ML-210}px" data-a="print" data-t="{pt["at"]+0.08:.2f}">{esc(pt["text"])}</div>')
            if i < n - 1:
                h.append(f'<div class="hair" style="left:{ML}px;top:{ry+rh-14:.0f}px;width:{CW}px" data-a="wipe" data-t="{pts[i+1]["at"]-0.3:.2f}"></div>')

    elif t == "typo":
        ws = film["sentences"][st["sentence"]]["_ws"]
        h.append(f'<div class="typo" style="left:90px;width:{W-180}px;top:{y0+330}px">{typo_words(st["text"], ws, st.get("italic"))}</div>')
        h.append(f'<div class="rule" style="left:{W/2-60:.0f}px;top:{y0+900}px;width:120px" data-a="wipe" data-t="{ws[-1]["s"]:.2f}"></div>')

    elif t == "studies_stack":
        # méta-analyse ou revue : une petite feuille imprimée par étude (par lot au-delà de 40), lâchée sur la table
        at = st["at"]
        n = int(st["n_studies"])
        per = max(1, math.ceil(n / 40))
        k = math.ceil(n / per)
        cols = 8 if k > 24 else (6 if k > 12 else 4)
        rows = math.ceil(k / cols)
        cw_ = 116 if cols == 8 else (140 if cols == 6 else 170)
        sh = min(150, 470 / rows) - 16
        sw_ = sh * 0.74
        gx = (W - cols * cw_) / 2 + (cw_ - sw_) / 2
        h += kicker(y0, st.get("title", "Les études regroupées"), t0 + 0.2)
        h.append(f'<div class="num center" style="left:0;width:{W}px;top:{y0+150}px;font-size:170px" data-a="big" data-t="{at-0.05:.2f}" data-d="0.6">'
                 f'<span data-fx="count" data-t="{at:.2f}" data-d="{min(1.4, 0.4 + k * 0.03):.2f}" data-to="{n}" data-dec="0">0</span></div>')
        h.append(f'<div class="glab" style="left:0;width:{W}px;top:{y0+336}px" data-a="rise" data-t="{at+0.3:.2f}">{esc(st.get("label", "études"))}</div>')
        gy = y0 + 430
        rnd = random.Random(31)
        for i in range(k):
            x = gx + (i % cols) * cw_ + rnd.uniform(-8, 8)
            y = gy + (i // cols) * (sh + 16) + rnd.uniform(-5, 5)
            rot = rnd.uniform(-6, 6)
            acc = " acc" if i % 7 == 3 else ""
            lines = "".join(f'<i style="top:{18 + j*13*(sh/120):.0f}px;width:{[70, 56, 64, 44][j % 4]}%"></i>' for j in range(5))
            h.append(f'<div class="msheet{acc}" style="left:{x:.0f}px;top:{y:.0f}px;width:{sw_:.0f}px;height:{sh:.0f}px" data-a="deal" data-rot="{rot:.1f}" data-t="{at + 0.15 + (i / max(1, k - 1)) * 1.2:.2f}">{lines}</div>')
        by = gy + rows * (sh + 16) + 6
        if per > 1:
            h.append(f'<div class="kick center" style="left:0;width:{W}px;top:{by:.0f}px" data-a="rise" data-t="{at+1.0:.2f}">1 feuille = {per} études</div>')
            by += 46
        if st.get("n_patients"):
            pa = st.get("patients_at", at + 1.6)
            h.append(f'<div class="glab acc" style="left:0;width:{W}px;top:{by+14:.0f}px;font-size:42px" data-a="rise" data-t="{pa:.2f}">'
                     f'<span data-fx="count" data-t="{pa:.2f}" data-d="1.0" data-to="{int(st["n_patients"])}" data-dec="0">0</span> patients au total</div>')
            by += 74
        if st.get("sub"):
            h.append(f'<div class="kick center" style="left:0;width:{W}px;top:{by+20:.0f}px" data-a="rise" data-t="{st.get("patients_at", at + 1.6) + 0.4:.2f}">{esc(st["sub"])}</div>')

    elif t == "forest_plot":
        studies = st["studies"][:12]
        n = len(studies)
        pooled = st.get("pooled")
        nul = float(st.get("null", 0))
        logs = st.get("log", nul == 1)
        f_ = (lambda v: math.log(max(1e-6, float(v)))) if logs else (lambda v: float(v))
        h += kicker(y0, "Méta-analyse", t0 + 0.25, fig)
        tt, tb = ptitle(y0, st.get("title", "Chaque étude, puis l'effet regroupé"), t0 + 0.35)
        h.append(tt)
        vals = [f_(s[k]) for s in studies for k in ("low", "high")] + [f_(nul)]
        if pooled:
            vals += [f_(pooled["low"]), f_(pooled["high"])]
        a, b = min(vals), max(vals)
        pad = (b - a) * 0.08 or 0.5
        x0p, x1p = 400, 1000
        X = lambda v: x0p + (f_(v) - (a - pad)) / ((b + pad) - (a - pad)) * (x1p - x0p)
        top = y0 + tb + 50
        rh = min(66, (820 - tb - 50) / (n + 1))
        zx = X(nul)
        last = top + n * rh
        h.append(f'<div class="zero" style="left:{zx-1.5:.0f}px;top:{top-20:.0f}px;height:{last-top+120:.0f}px" data-a="fade" data-t="{t0+0.5:.2f}"></div>')
        ws_ = [float(s.get("weight", 1)) for s in studies]
        wmax = max(ws_) or 1
        for i, s in enumerate(studies):
            ry = top + i * rh + rh / 2
            at = s.get("at", st.get("at", t0 + 0.8) + i * 0.25)
            h.append(f'<div class="kick" style="left:{ML}px;top:{ry-16:.0f}px;width:310px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" data-a="rise" data-t="{at:.2f}">{esc(s["label"])}</div>')
            xl, xr = X(s["low"]), X(s["high"])
            h.append(svg_layer(xl - 2, ry - 9, xr - xl + 4, 18, f'<path d="M2 9H{xr-xl+2:.0f}" stroke="{INK}" stroke-width="3"/>', "growc", at + 0.05))
            side = 14 + 22 * math.sqrt(ws_[i] / wmax)
            h.append(f'<div class="sq" style="left:{X(s["value"])-side/2:.0f}px;top:{ry-side/2:.0f}px;width:{side:.0f}px;height:{side:.0f}px" data-a="pop" data-t="{at+0.15:.2f}"></div>')
        sep_y = last + 10
        h.append(f'<div class="hair" style="left:{ML}px;top:{sep_y:.0f}px;width:{CW}px" data-a="wipe" data-t="{(pooled or {}).get("at", t0 + 2.5) - 0.4:.2f}"></div>')
        if pooled:
            pa = pooled.get("at", t0 + 2.5)
            py = sep_y + 64
            h.append(f'<div class="mlab acc" style="left:{ML}px;top:{py-26:.0f}px;width:310px;font-size:36px" data-a="rise" data-t="{pa:.2f}">{esc(pooled.get("label", "Effet regroupé"))}</div>')
            xl, xr, xv = X(pooled["low"]), X(pooled["high"]), X(pooled["value"])
            h.append(svg_layer(xl, py - 22, xr - xl, 44, f'<path d="M0 22L{xv-xl:.0f} 0L{xr-xl:.0f} 22L{xv-xl:.0f} 44Z" fill="{AC}"/>', "drop", pa + 0.1))
            if pooled.get("text"):
                h.append(f'<div class="kick acc" style="left:{ML}px;top:{py+48:.0f}px;width:{CW}px" data-a="rise" data-t="{pa+0.5:.2f}">{esc(pooled["text"])}</div>')
        h.append(f'<div class="kick" style="left:{ML}px;top:{y0+1000}px" data-a="rise" data-t="{t0+0.7:.2f}">← {esc(st.get("left_label", "favorise le témoin"))}</div>')
        right_label = st.get("right_label", "favorise l'IA")
        h.append(f'<div class="kick acc" style="right:{ML}px;top:{y0+1000}px;text-align:right" data-a="rise" data-t="{t0+0.8:.2f}">{esc(right_label)} →</div>')

    elif t == "roc_curve":
        auc = st["auc"]
        aat = auc["at"]
        cat = st.get("curve_at", aat - 1.0)
        h += kicker(y0, "Courbe ROC", t0 + 0.25, fig, right="schéma · AUC exacte")
        px0, py0, S = 210, 200, 660
        dprime = math.sqrt(2) * inv_norm(min(0.995, max(0.505, float(auc["num"]))))
        fprs = [0] + [10 ** (-3 + 3 * k / 40) for k in range(41)]
        pts = [(f, ncdf(inv_norm(f) + dprime) if f > 0 else 0) for f in fprs]
        pts[-1] = (1, 1)
        d = "M" + " L".join(f"{x*S:.1f} {S - y*S:.1f}" for x, y in pts)
        h.append(svg_layer(px0, y0 + py0, S, S, f'<path d="{d} L{S} {S} Z" fill="{AC}" fill-opacity=".13" stroke="none"/>', "fade", aat - 0.3))
        h.append(svg_layer(px0 - 3, y0 + py0 - 3, S + 6, S + 6, f'<path d="M3 3V{S+3}H{S+3}" stroke="{INK}" stroke-width="3"/>', "draw", t0 + 0.4, 'data-d="0.6"'))
        h.append(svg_layer(px0, y0 + py0, S, S, f'<path d="M0 {S}L{S} 0" stroke="{INKD}" stroke-width="2" stroke-dasharray="8 10"/>', "draw", t0 + 0.8, 'data-d="0.6" data-ease="none"'))
        h.append(svg_layer(px0, y0 + py0, S, S, f'<path d="{d}" stroke="{AC}" stroke-width="7"/>', "draw", cat, 'data-d="1.4"'))
        h.append(f'<div class="kick center" style="left:{px0}px;width:{S}px;top:{y0+py0+S+20}px" data-a="rise" data-t="{t0+0.6:.2f}">{esc(st.get("x_label", "Fausses alertes"))} →</div>')
        h.append(f'<div class="kick center rot" style="left:{px0-S/2-46:.0f}px;width:{S}px;top:{y0+py0+S/2-14:.0f}px" data-a="rise" data-t="{t0+0.7:.2f}">{esc(st.get("y_label", "Malades repérés"))} →</div>')
        h.append(f'<div class="kick sm rot45" style="left:{px0+S*0.66:.0f}px;top:{y0+py0+S*0.42:.0f}px" data-a="fade" data-t="{t0+1.2:.2f}">hasard</div>')
        val = str(auc["value"])
        h.append(f'<div class="bval acc" style="left:{px0+S*0.42:.0f}px;width:380px;top:{y0+py0+S*0.56:.0f}px;text-align:left;font-size:110px" data-a="big" data-t="{aat-0.05:.2f}" data-d="0.5">'
                 f'<span data-fx="count" data-t="{aat:.2f}" data-d="1.0" data-to="{auc["num"]}" data-dec="{decs(val)}">0</span></div>')
        h.append(f'<div class="kick acc" style="left:{px0+S*0.42+6:.0f}px;top:{y0+py0+S*0.56+120:.0f}px" data-a="rise" data-t="{aat+0.3:.2f}">Aire sous la courbe</div>')
        if auc.get("note"):
            h.append(f'<div class="kick" style="left:{px0+S*0.42+6:.0f}px;top:{y0+py0+S*0.56+160:.0f}px;width:{S*0.58:.0f}px" data-a="rise" data-t="{aat+0.5:.2f}">{esc(auc["note"])}</div>')

    elif t == "diagnostic_grid":
        total = min(100, int(st["total"]))
        sick, found, fa = int(st["sick"]), int(st["found"]), int(st.get("false_alarms", 0))
        at = st.get("at", t0 + 0.5)
        sk = st.get("sick_at", at + 1.0)
        sa = st.get("scan_at", sk + 0.7)
        h += kicker(y0, "Précision diagnostique", t0 + 0.25, fig)
        legend = st.get("legend") or f"{sick} malades, cerclés, sur {total} patients"
        h.append(f'<div class="kick" style="left:{ML}px;top:{y0+136}px;width:{CW}px" data-a="rise" data-t="{t0+0.4:.2f}">{esc(legend)}</div>')
        rnd = random.Random(21)
        ids = list(range(total))
        rnd.shuffle(ids)
        sick_ids = set(ids[:sick])
        missed = set(sorted(sick_ids, key=lambda i: rnd.random())[:max(0, sick - found)])
        healthy = [i for i in ids if i not in sick_ids]
        alarms = set(healthy[:fa])
        cell, ds = 64, 36
        gx0 = (W - 10 * cell) / 2 + (cell - ds) / 2
        gy0 = y0 + 214
        rows = math.ceil(total / 10)
        sd = 1.3
        for i in range(total):
            x, y = gx0 + (i % 10) * cell, gy0 + (i // 10) * cell
            tint = []
            if i in sick_ids:
                tint.append([round(sk + (i % 10) * 0.02, 2), "rgba(22,23,28,0)", "inset 0 0 0 4px #16171C"])
            rt = round(sa + (i // 10) / max(1, rows) * sd, 2)
            if i in sick_ids and i not in missed:
                tint.append([rt, AC, "inset 0 0 0 0px #16171C"])
            if i in alarms:
                tint.append([rt, INKD, "inset 0 0 0 0px #16171C"])
            h.append(f'<div class="dd" style="left:{x:.0f}px;top:{y:.0f}px" data-a="pop" data-t="{at + i*0.006:.2f}" data-tint=\'{json.dumps(tint)}\'></div>')
        h.append(f'<div class="bandclip" style="left:{gx0-30:.0f}px;top:{gy0-20:.0f}px;width:{10*cell+60}px;height:{rows*cell+40}px"><div class="band h" data-fx="band" data-t="{sa:.2f}" data-d="{sd+0.2:.2f}" data-y0="-40" data-y1="{rows*cell+40}"></div></div>')
        for k, key in enumerate(("sens", "spec")):
            mtr = st.get(key)
            if not mtr:
                continue
            x = ML if k == 0 else 560
            acc = " acc" if k == 0 else ""
            val = str(mtr["value"])
            h.append(f'<div class="bval{acc}" style="left:{x}px;width:440px;top:{y0+884}px;text-align:left;font-size:96px" data-a="big" data-t="{mtr["at"]-0.05:.2f}" data-d="0.5">'
                     f'<span data-fx="count" data-t="{mtr["at"]:.2f}" data-d="0.9" data-to="{mtr["num"]}" data-dec="{decs(val)}">0</span><span class="unit">{esc(mtr.get("unit", " %"))}</span></div>')
            h.append(f'<div class="kick sm{acc}" style="left:{x+4}px;top:{y0+990}px;width:470px" data-a="rise" data-t="{mtr["at"]+0.3:.2f}">{esc(mtr.get("label", "Sensibilité" if k == 0 else "Spécificité"))}</div>')

    elif t == "survival_curves":
        gs = st["groups"][:2]
        times = [float(x) for x in st["times"]]
        xmax = float(st.get("x_max", times[-1])) or 1
        allv = [float(v) for g in gs for v in g["values"]]
        ymin = float(st.get("y_min", max(0, math.floor((min(allv) - 5) / 10) * 10)))
        h += kicker(y0, "Suivi dans le temps", t0 + 0.25, fig)
        tt, tb = ptitle(y0, st.get("title", ""), t0 + 0.35) if st.get("title") else ("", 150)
        if tt:
            h.append(tt)
        px0, px1, pyt, pyb = 170, 800, y0 + tb + 70, y0 + 860
        X = lambda v: px0 + float(v) / xmax * (px1 - px0)
        Y = lambda v: pyt + (100 - float(v)) / (100 - ymin) * (pyb - pyt)
        h.append(svg_layer(px0 - 3, pyt - 3, px1 - px0 + 6, pyb - pyt + 6, f'<path d="M3 3V{pyb-pyt+3:.0f}H{px1-px0+3:.0f}" stroke="{INK}" stroke-width="3"/>', "draw", t0 + 0.4, 'data-d="0.6"'))
        for v in (100, (100 + ymin) / 2, ymin):
            h.append(f'<div class="kick sm" style="left:40px;width:110px;top:{Y(v)-14:.0f}px;text-align:right" data-a="fade" data-t="{t0+0.5:.2f}">{fr(v, 0)} %</div>')
        step_ = max(1, len(times) // 6)
        for v in times[::step_]:
            h.append(f'<div class="kick sm center" style="left:{X(v)-50:.0f}px;width:100px;top:{pyb+14:.0f}px" data-a="fade" data-t="{t0+0.55:.2f}">{fr(v, 0)}</div>')
        h.append(f'<div class="kick center" style="left:{px0}px;width:{px1-px0}px;top:{pyb+56:.0f}px" data-a="rise" data-t="{t0+0.6:.2f}">{esc(st.get("x_label", "Mois de suivi"))}</div>')
        ends = []
        for k, g in enumerate(gs):
            vals = [float(v) for v in g["values"]]
            d = f"M{X(times[0])-px0:.1f} {Y(vals[0])-pyt:.1f}"
            for i in range(1, len(times)):
                d += f" H{X(times[i])-px0:.1f} V{Y(vals[i])-pyt:.1f}"
            col, sw = (AC, 7) if g.get("accent") else (INKD, 4.5)
            h.append(svg_layer(px0, pyt, px1 - px0, pyb - pyt + 4, f'<path d="{d}" stroke="{col}" stroke-width="{sw}" stroke-linecap="butt"/>', "draw", g.get("at", t0 + 1.0), 'data-d="2.2" data-ease="none"'))
            ends.append([Y(vals[-1]), g, vals[-1]])
        ends.sort(key=lambda e: e[0])
        if len(ends) == 2 and ends[1][0] - ends[0][0] < 96:
            mid = (ends[0][0] + ends[1][0]) / 2
            ends[0][0], ends[1][0] = mid - 48, mid + 48
        for ly, g, last in ends:
            a = " acc" if g.get("accent") else ""
            val = g.get("end_label", fr(last, decs(str(g["values"][-1]))) + " %")
            h.append(f'<div class="kick{a}" style="left:{px1+18:.0f}px;top:{ly-40:.0f}px;width:{W-ML-px1-18:.0f}px" data-a="rise" data-t="{g.get("at", t0+1.0)+2.2:.2f}">{esc(g["label"])}</div>')
            h.append(f'<div class="bval{a}" style="left:{px1+18:.0f}px;top:{ly-6:.0f}px;text-align:left;font-size:44px" data-a="rise" data-t="{g.get("at", t0+1.0)+2.3:.2f}">{esc(val)}</div>')
        if st.get("note"):
            nt = st["note"]
            na = nt.get("at", t0 + 3.4)
            if nt.get("time") is not None:
                ti = min(range(len(times)), key=lambda i: abs(times[i] - float(nt["time"])))
                v1, v2 = sorted([float(gs[0]["values"][ti]), float(gs[1]["values"][ti])])
                bx = X(times[ti]) + 8
                h.append(svg_layer(bx, Y(v2) - 3, 26, Y(v1) - Y(v2) + 6, f'<path d="M3 3H20V{Y(v1)-Y(v2)+3:.0f}H3" stroke="{ACD}" stroke-width="4"/>', "draw", na - 0.2, 'data-d="0.35"'))
            h.append(f'<div class="annot" style="left:{px0+24}px;top:{pyb-62:.0f}px;font-size:42px" data-a="rise" data-t="{na:.2f}">{esc(nt["text"])}</div>')

    elif t == "chat":
        msgs = st["messages"][:4]
        h.append(f'<div class="ccard" style="left:108px;top:{y0+150}px;width:864px;height:790px" data-a="pop" data-t="{t0+0.2:.2f}"></div>')
        h.append(f'<div class="kick" style="left:150px;top:{y0+184}px" data-a="rise" data-t="{t0+0.35:.2f}"><span class="fig">Fig. {fig}</span> · {esc(st.get("title", "Conversation"))}</div>')
        rnd = random.Random(5)
        y = y0 + 250
        last_ia = None
        for m_ in msgs:
            ia = m_.get("from", "ia") == "ia"
            L = int(m_.get("lines", 4 if ia else 2))
            bw_ = 600 if ia else 470
            bh = 58 + L * 38
            if y + bh > y0 + 920:
                break
            x = 150 if ia else 972 - 42 - bw_
            mat = m_["at"]
            if ia:
                h.append(f'<div class="typing" style="left:150px;top:{y:.0f}px" data-a="fade" data-t="{mat-0.9:.2f}" data-o="{mat-0.05:.2f}"><i data-fx="typing" data-t="{mat-0.85:.2f}"></i><i data-fx="typing" data-t="{mat-0.75:.2f}"></i><i data-fx="typing" data-t="{mat-0.65:.2f}"></i></div>')
            lab = m_.get("label", "IA" if ia else {"patient": "Patient", "soignant": "Soignant", "question": "Question"}.get(m_.get("from"), "Patient"))
            lines = "".join(f'<i class="skl{" lt" if ia else ""}" style="top:{52 + j*38}px;width:{(0.55 + rnd.random()*0.38)*(bw_-60) if j == L-1 else (0.85 + rnd.random()*0.12)*(bw_-60):.0f}px" data-a="growx" data-t="{mat+0.15+j*0.18:.2f}"></i>' for j in range(L))
            h.append(f'<div class="bub {"ia" if ia else "hu"}" style="left:{x:.0f}px;top:{y:.0f}px;width:{bw_}px;height:{bh}px" data-a="pop" data-t="{mat:.2f}"><span class="kick sm{" lt" if ia else ""}">{esc(lab)}</span>{lines}</div>')
            if ia:
                last_ia = (x, y, bw_, bh, mat + 0.15 + L * 0.18)
            y += bh + 34
        if st.get("rating") and last_ia:
            rt = st["rating"]
            ra = rt.get("at", last_ia[4] + 0.6)
            x, yb, bw_, bh, _ = last_ia
            bx = x + bw_ + 22
            ry_ = min(y0 + 800, yb + bh + 40)
            h.append(svg_layer(bx, yb, 30, bh, f'<path d="M3 3H24V{bh-3}H3" stroke="{AC}" stroke-width="5"/>', "draw", ra - 0.3, 'data-d="0.35"'))
            h.append(svg_layer(bx + 22, yb + bh / 2 - 2, 70, ry_ - (yb + bh / 2) + 6, f'<path d="M0 3H40V{ry_-(yb+bh/2):.0f}" stroke="{AC}" stroke-width="3"/>', "draw", ra - 0.05, 'data-d="0.35"'))
            h.append(f'<div class="bval acc" style="left:420px;width:{930-420}px;top:{ry_+10:.0f}px;text-align:right;font-size:76px" data-a="big" data-t="{ra:.2f}" data-d="0.5">{esc(rt["value"])}</div>')
            if rt.get("label"):
                h.append(f'<div class="kick acc" style="left:300px;width:{930-300}px;top:{ry_+96:.0f}px;text-align:right" data-a="rise" data-t="{ra+0.3:.2f}">{esc(rt["label"])}</div>')

    elif t == "image_scan":
        img = st.get("image", "xray")
        at = st.get("at", t0 + 0.4)
        sa = st.get("scan_at", at + 1.0)
        la = st.get("lock_at", sa + 1.3)
        oa = st.get("out_at", la + 0.8)
        h += kicker(y0, st.get("title", "Ce que l'IA lit"), t0 + 0.25, fig, right="schéma")
        bx, by_, S = 228, y0 + 170, 624
        k = S / 360
        h.append(svg_layer(bx, by_, S, S, image_svg(img), "draw", at, 'data-d="1.1" data-stg="0.06"', vb="0 0 360 360"))
        h.append(f'<div class="bandclip" style="left:{bx}px;top:{by_}px;width:{S}px;height:{S}px"><div class="band h" data-fx="band" data-t="{sa:.2f}" data-d="1.3" data-y0="-60" data-y1="{S}"></div></div>')
        im = IMG.get(img) or IMG["xray"]
        for i, (cx, cy, r) in enumerate(im["spots"]):
            h.append(f'<div class="spot" style="left:{bx+cx*k-r*k:.0f}px;top:{by_+cy*k-r*k:.0f}px;width:{2*r*k:.0f}px;height:{2*r*k:.0f}px" data-a="pop" data-t="{la-0.35+i*0.08:.2f}"></div>')
        lx0, ly0, lx1, ly1 = (v * k for v in im["lock"])
        h.append(svg_layer(bx + lx0 - 6, by_ + ly0 - 6, lx1 - lx0 + 12, ly1 - ly0 + 12, corners(6, 6, lx1 - lx0 + 6, ly1 - ly0 + 6, 22, 6), "lock", la))
        cxm = bx + (lx0 + lx1) / 2
        h.append(svg_layer(cxm - 3, by_ + ly1 + 8, 6, y0 + 846 - (by_ + ly1 + 8), f'<path d="M3 0V{y0+846-(by_+ly1+8):.0f}" stroke="{AC}" stroke-width="3"/>', "draw", la + 0.35, 'data-d="0.35"'))
        h.append(f'<div class="kick acc" style="left:{max(ML, cxm-200):.0f}px;top:{y0+856}px;width:520px" data-a="rise" data-t="{la+0.6:.2f}">{esc(st.get("found_label", "Signes repérés"))}</div>')
        if st.get("result_label"):
            h.append(f'<div class="pillwrap" style="left:0;width:{W}px;top:{y0+920}px" data-a="pop" data-t="{oa:.2f}"><span class="pill">{esc(st["result_label"])}</span></div>')

    elif t == "face_to_face":
        at = st["at"]
        h.append(f'<div class="kick center" style="left:0;width:{W}px;top:{y0+80}px" data-a="rise" data-t="{st.get("label_at", at+1.1):.2f}">{esc(st["label"])}</div>')
        h.append(person_svg(140, y0 + 220, 340, "var(--ink)", f'data-a="slideL" data-t="{at:.2f}"'))
        h.append(person_svg(804, y0 + 220, 340, "var(--carbon)", f'data-a="slideR" data-t="{at+0.15:.2f}"'))
        h.append(f'<div class="card" style="left:335px;top:{y0+250}px;width:410px" data-a="pop" data-t="{st.get("card_at", at+0.55):.2f}">'
                 f'<div class="mono s" style="color:var(--ink-dim);font-size:26px">{esc(st["card_title"])}</div>'
                 f'<div class="cardv">{esc(st["card_value"])}</div>'
                 f'<div class="mono s" style="color:var(--carbon-deep);font-size:26px;margin-top:12px;letter-spacing:.04em">{esc(st["card_note"])}</div></div>')
        h.append(iconbox("check", 510, y0 + 520, 60, 60, "var(--carbon-deep)", st.get("check_at", at + 1.6)))

    elif t == "flow_door":
        at = st["at"]
        ca, da, wa = st.get("card_at", at + 0.45), st.get("door_at", at + 1.2), st.get("walk_at", at + 1.6)
        h.append(f'<div class="card" style="left:70px;top:{y0+190}px;width:400px" data-a="pop" data-t="{ca:.2f}">'
                 f'<div class="ico s" style="width:54px;height:54px;color:var(--carbon-deep)">{icon("check")}</div>'
                 f'<div class="cardv it" style="font-size:46px;margin-top:10px">{esc(st["from_label"])}</div></div>')
        h.append(f'<div class="dashh" style="left:490px;top:{y0+300}px;width:230px" data-a="growx" data-t="{da-0.15:.2f}"></div>')
        h.append(f'<div class="mono" style="left:730px;top:{y0+110}px;width:240px;text-align:center;color:var(--ink)" data-a="rise" data-t="{da+0.1:.2f}">{esc(st["to_label"])}</div>')
        h.append(f'<div class="ico door" style="left:750px;top:{y0+150}px;width:200px;height:320px;color:var(--ink)" data-a="draw" data-t="{da:.2f}">{icon("door")}</div>')
        h.append(f'<div class="doorlight acc" style="left:756px;top:{y0+156}px;width:188px;height:308px" data-a="fade" data-t="{wa:.2f}"></div>')
        for kk in range(3):
            h.append(person_svg(140 + kk * 70, y0 + 480, 150, "var(--carbon)",
                                f'data-a="up" data-t="{ca+0.3+kk*0.1:.2f}" data-fx="walk" data-fxt="{wa+kk*0.2:.2f}" data-d="1.4" data-dx="{620 - kk*40}"'))

    elif t == "remaining_dots":
        at = st["at"]
        cols, cell, r = 23, 22, 7
        rows = math.ceil(st["n"] / cols)
        wpx, hpx = cols * cell, rows * cell
        base = "".join(f'<circle cx="{(i % cols) * cell + cell/2:.1f}" cy="{(i // cols) * cell + cell/2:.1f}" r="{r-1}" fill="none" stroke="{INK}" stroke-opacity=".38" stroke-width="1.6"/>' for i in range(st["n"]))
        lit = "".join(f'<circle cx="{(i % cols) * cell + cell/2:.1f}" cy="{(i // cols) * cell + cell/2:.1f}" r="{r}" fill="{AC}"/>' for i in range(st["k"]))
        x0 = (W - wpx) / 2
        h.append(f'<div class="num center" style="left:0;width:{W}px;top:{y0+120}px;font-size:150px" data-a="big" data-t="{at-0.05:.2f}" data-d="0.55"><span data-fx="count" data-t="{at:.2f}" data-d="1.1" data-to="{st["value"]}" data-dec="0">0</span><span class="unit">%</span></div>')
        h.append(f'<div class="kick center" style="left:0;width:{W}px;top:{y0+300}px" data-a="rise" data-t="{at+0.5:.2f}">{esc(st["label"])}</div>')
        h.append(f'<svg class="lay" style="left:{x0:.0f}px;top:{y0+380}px;width:{wpx}px;height:{hpx}px" viewBox="0 0 {wpx} {hpx}" data-fx="litdots" data-t="{at+0.15:.2f}" data-d="1.0">{base}</svg>')
        h.append(f'<svg class="lay" style="left:{x0:.0f}px;top:{y0+380}px;width:{wpx}px;height:{hpx}px" viewBox="0 0 {wpx} {hpx}" data-a="fade" data-t="{st["cam_at"]+0.1:.2f}">{lit}</svg>')
        h.append(f'<div class="kick acc center" style="left:0;width:{W}px;top:{y0+400+hpx}px" data-a="rise" data-t="{st["cam_at"]+0.35:.2f}">{esc(st["group_label"])} · {st["k"]} venus · {st["n"]-st["k"]} absents</div>')
    return "\n".join(x for x in h if x)



# --------------------------------------------------------------------------------------------- assemblage
def build(project):
    proj = pathlib.Path(project).resolve()
    film = json.loads((proj / "film.json").read_text(encoding="utf-8"))
    wd = json.loads((proj / film["words_file"]).read_text(encoding="utf-8"))
    words = wd["words"] if isinstance(wd, dict) else wd
    words = [{"w": w["w"], "s": float(w.get("s", w.get("start"))), "e": float(w.get("e", w.get("end")))} for w in words]
    clock = Clock(film, words)
    resolve(film, clock)
    D = float(film["duration"])

    def find_sentence(text):
        for k, s in enumerate(film["sentences"]):
            if s["text"] == text:
                return k
        raise SystemExit(f"phrase introuvable : {text}")

    night, pv, paper, en = film["night"], film["pivot"], film["paper"], film["end"]
    # temps dérivés : la table s'arrête, la question du pivot, pli vers le papier ; à la fin, pli du papier vers la table
    pv["start"] = night["end"]
    pv["end"] = pv["fold_at"] + FOLD_DUR + 0.05
    paper["start"] = pv["fold_at"] - 0.05
    en["start"] = en["fold_at"] - 0.05
    paper["end"] = en["fold_at"] + FOLD_DUR + 0.05
    en["end"] = D

    # ---- la table : planches empilées sur la feuille, le moteur les espace lui-même
    y = 0
    for st in night["stations"]:
        st["y"] = y
        y += night_height(st) + NIGHT_GAP
    sheet_h = y + 400
    night_html = "\n".join(night_station(st) for st in night["stations"])
    ncam = []
    for st in night["stations"]:
        ncam.append([st["cam_at"], -st["y"] + NIGHT_DY.get(st["type"], 0)])
        if st["type"] == "steps":
            for s in st["steps"][1:]:
                ncam.append([s["at"] - 0.3, -(s["_y"]) + STEP_DY])

    # ---- le papier : une planche par écran ; la première nuance arrive par une déchirure (verso)
    pst = paper["stations"]
    skip_subs = set()
    for st in pst:
        if st["type"] == "typo":
            st["sentence"] = find_sentence(st["text"])
            skip_subs.add(st["sentence"])
    tear_i = next((i for i, st in enumerate(pst) if st["type"] == "typo" and i > 0), None) if paper.get("tear", True) else None
    # chaque planche est une feuille : la suivante est posée par-dessus (du bas, puis de la droite, en alternance),
    # la précédente s'enfonce et s'assombrit ; la première nuance arrive par une déchirure qui révèle le verso
    fig = 0
    plates, pin = [], []
    for i, st in enumerate(pst):
        st["y"] = 0
        if st["type"] in FIG_TYPES:
            fig += 1
            st["_fig"] = fig
        verso = i == tear_i
        inner = paper_station(st, film, st.get("_fig"))
        plates.append(f'<div class="plate{" verso" if verso else ""}" id="plate{i}"><div class="pground"></div><div class="plight"></div>'
                      f'<div class="pcrease"></div>{inner}<div class="pdim"></div></div>')
        mode = "first" if i == 0 else ("tear" if verso else ("up" if i % 2 else "right"))
        pin.append([round(st["cam_at"] - (0.45 if verso else 0.05), 3), mode])
    paper_html = "\n".join(plates)
    tear, tear_html = None, ""
    if tear_i is not None:
        tear = {"at": pin[tear_i][0]}
        prev = pst[tear_i - 1]
        copy = paper_station(prev, film, prev.get("_fig"))
        rnd = random.Random(11)
        pts = [(x, 620 + (rnd.random() - .5) * 46) for x in range(0, W + 36, 36)]
        top_clip = "polygon(0 0," + f"{W}px 0," + ",".join(f"{x}px {yy:.0f}px" for x, yy in reversed(pts)) + ")"
        bot_clip = "polygon(" + ",".join(f"{x}px {yy:.0f}px" for x, yy in pts) + f",{W}px {H}px,0 {H}px)"
        edge = " ".join(f"{x},{yy:.0f}" for x, yy in pts)
        fib = f'<svg class="lay" style="left:0;top:0;width:{W}px;height:{H}px" viewBox="0 0 {W} {H}"><polyline points="{edge}" fill="none" stroke="#FFFDF8" stroke-width="7" stroke-linejoin="round"/></svg>'
        tear_html = (f'<div class="tearh" id="tearT" style="clip-path:{top_clip}"><div class="pground"></div><div class="pcrease"></div>{copy}{fib}</div>'
                     f'<div class="tearh" id="tearB" style="clip-path:{bot_clip}"><div class="pground"></div><div class="pcrease"></div>{copy}{fib}</div>')

    pv_k = find_sentence(pv["text"])
    pv_ws = film["sentences"][pv_k]["_ws"]
    en_k = find_sentence(en["promise"])
    en_ws = film["sentences"][en_k]["_ws"]
    skip_subs |= {pv_k, en_k}
    subs = build_subs(film, skip_subs)

    runtime = {"duration": D, "fold": FOLD_DUR, "ncam": ncam, "plates": pin, "tear": tear,
               "night": [night["start"], night["end"]], "paper": [paper["start"], paper["end"]],
               "pivot": {"start": pv["start"], "fold_at": pv["fold_at"]},
               "end": {"start": en["start"], "fold_at": en["fold_at"], "click_at": en["click_at"], "button_at": en["button_at"]}}

    css = (HERE / "moteur.css").read_text(encoding="utf-8")
    js = (HERE / "moteur.js").read_text(encoding="utf-8")
    check_svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'

    doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="assets/vendor/gsap.min.js"></script>
<style>
{css}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{D}" data-width="{W}" data-height="{H}">
  <div id="bgnight" class="clip" data-start="0" data-duration="{D}" data-track-index="0"><div class="tablebg"></div><div class="halo" id="nhalo"></div></div>

  <div id="night" class="clip" data-start="{night['start']}" data-duration="{night['end']-night['start']:.3f}" data-track-index="1">
    <div class="persp"><div id="nplane"><div id="ncam">
      <div class="sheetsh" style="height:{sheet_h}px"></div>
      <div class="sheet" id="nsheet" style="height:{sheet_h}px"><div class="corner"></div><div class="crease"></div>
{night_html}
      </div>
    </div></div></div>
    <div class="nscrim"></div>
  </div>

  <div id="end" class="clip" data-start="{en['start']:.3f}" data-duration="{D-en['start']:.3f}" data-track-index="2">
    <div class="endbg"><div class="halo" id="ehalo"></div></div>
    <svg id="glyph" viewBox="0 0 20 26" style="left:{W/2-48:.0f}px;top:250px;width:96px;height:125px"><path class="g1" d="M1.5 1.5H13L18.5 7V24.5H1.5Z"/><path class="g2" d="M13 1.5V7H18.5"/><path class="g3" d="M1.5 24.5L18.5 7"/></svg>
    <div class="typo endtypo" style="left:{(W-660)/2:.0f}px;width:660px;top:440px">{typo_words(en['promise'], en_ws, en.get('promise_italic'))}</div>
    <div class="wordmark" style="left:0;width:{W}px;top:640px" data-a="big" data-t="{en['wordmark_at']-0.05:.2f}" data-d="0.7">Papercraft<span>.AI</span></div>
    <div class="btn" id="btn" style="left:{W/2-120:.0f}px;top:800px;width:240px" data-a="pop" data-t="{en['button_at']:.2f}"><span id="btnlabel">{esc(en['button'])}</span><span id="btnok">{check_svg}Abonné</span></div>
    <div class="ripple" id="ripple" style="left:{W/2-70:.0f}px;top:768px"></div>
    <div class="mono center" style="left:0;width:{W}px;top:960px;color:var(--ink-dim);font-size:26px;letter-spacing:.1em" data-a="rise" data-t="{en['source_at']:.2f}">{esc(en['source'])}</div>
    <div class="mono center" style="left:0;width:{W}px;top:1000px;color:var(--ink-dim);font-size:26px;letter-spacing:.06em;text-transform:none" data-a="rise" data-t="{en['source_at']+0.15:.2f}">{esc(en['doi'])}</div>
    <svg id="cursor" viewBox="0 0 24 34" style="left:0;top:0;width:34px;height:48px"><path d="M2 2v26l7-6 5 10 4-2-5-10h9z" fill="#F7F3EC" stroke="#16171C" stroke-width="1.6" stroke-linejoin="round"/></svg>
  </div>

  <div id="paper" class="clip" data-start="{paper['start']:.3f}" data-duration="{paper['end']-paper['start']:.3f}" data-track-index="3">
    <div class="foldsheet" id="psheet">
      <div class="pground"></div>
      <div id="pcam">
{paper_html}
      {tear_html}
      </div>
      <div class="pcorner"></div>
    </div>
    <div class="flapwrap"><div class="flap paperflap" id="pflap"></div></div>
    <div class="streak" id="pstreak"></div>
  </div>

  <div id="pivot" class="clip" data-start="{pv['start']:.3f}" data-duration="{pv['end']-pv['start']:.3f}" data-track-index="4">
    <div class="foldsheet" id="pvsheet">
      <div class="pvground"></div><div class="plight" id="pvlight"></div>
      <div class="typo pvtext" style="left:80px;width:{W-160}px;top:500px">{typo_words(pv['text'], pv_ws, pv.get('italic'))}</div>
    </div>
    <div class="flapwrap"><div class="flap nightflap" id="pvflap"></div></div>
    <div class="streak" id="pvstreak"></div>
  </div>

  <div id="subs" class="clip" data-start="0" data-duration="{D}" data-track-index="8">
{subs}
  </div>
  <div id="grain" class="clip" data-start="0" data-duration="{D}" data-track-index="9"><div class="grainin"></div></div>
  <audio id="mix" data-start="0" data-duration="{D}" data-track-index="11" src="{film['audio']}" data-volume="1"></audio>
</div>
<script>
window.FILM = {json.dumps(runtime, ensure_ascii=False)};
{js}
</script>
</body>
</html>
"""
    (proj / "index.html").write_text(doc, encoding="utf-8")

    # bruitages déduits de la structure : peu, au bon moment, jamais à la chaîne (retour du 26 octobre).
    # Bruits de papier pour les gestes de papier (feuille posée, pli, déchirure), un « ping » pour le résultat qui
    # compte, un « pop » pour l'écart ; rien sur chaque élément qui apparaît. [nom, seconde, volume]
    if film.get("sfx", True):
        sfx = [["impact-bass-1", 0.0, 0.24]]
        for st in night["stations"]:
            if st["type"] == "hook_number":
                sfx.append(["pop", st["lit_at"], 0.18])
            if st["type"] == "steps":
                for s in st["steps"]:
                    if s.get("alert"):
                        sfx.append(["notification", s.get("note_at", s["at"] + 0.5), 0.14])
        sfx += [["whoosh-short", st["cam_at"] + 0.05, 0.08] for st in night["stations"][1:]]
        sfx += [["papier-pli", pv["fold_at"] - 0.05, 0.32], ["whoosh-cinematic", pv["fold_at"] - 0.1, 0.12]]
        for p in pin[1:]:
            if p[1] in ("up", "right"):
                sfx.append(["papier-pose", p[0] + 0.12, 0.2])
        if tear:
            sfx.append(["papier-dechire", tear["at"] + 0.2, 0.34])
        for st in pst:
            ty = st["type"]
            if ty == "population_split":
                sfx.append(["ping", st["groups"][1].get("accent_at", st["split_at"] + 1), 0.12])
            if ty in ("result_bars", "result_strips", "result_dots"):
                sfx += [["ping", g["at"], 0.13] for g in st["groups"] if g.get("accent")]
                c = ci_of(st)
                at = (c or {}).get("at") or st.get("diff_at")
                if at:
                    sfx.append(["pop", at + 0.2, 0.16])
            if ty == "metric":
                sfx += [["ping", g["at"], 0.12] for g in st["metrics"] if g.get("accent")]
            if ty == "forest_plot" and st.get("pooled"):
                sfx.append(["pop", st["pooled"].get("at", st["cam_at"] + 2.5) + 0.5, 0.16])
            if ty == "roc_curve":
                sfx.append(["ping", st["auc"]["at"], 0.12])
            if ty == "diagnostic_grid" and st.get("sens"):
                sfx.append(["ping", st["sens"]["at"], 0.12])
            if ty == "image_scan":
                sfx.append(["ping", st.get("lock_at", st["cam_at"] + 2.7), 0.12])
            if ty == "chat" and st.get("rating"):
                sfx.append(["pop", st["rating"].get("at", st["cam_at"] + 3), 0.14])
        sfx += [["papier-pli", en["fold_at"] - 0.05, 0.28], ["whoosh-cinematic", en["fold_at"] - 0.1, 0.1],
                ["chime", en["wordmark_at"], 0.18], ["click", en["click_at"], 0.4]]
        sfx = sorted([[n, round(max(0.0, t), 3), v] for n, t, v in sfx], key=lambda e: e[1])
        # jamais deux bruitages à moins de 1,2 s : on garde le plus important (papier et fin d'abord)
        rang = {"impact-bass-1": 0, "papier-pli": 0, "papier-dechire": 0, "click": 0, "chime": 0, "whoosh-cinematic": 0,
                "papier-pose": 1, "ping": 2, "pop": 2, "notification": 2, "whoosh-short": 3}
        garde = []
        for e in sfx:
            proche = [g for g in garde if abs(g[1] - e[1]) < 1.2 and rang.get(g[0], 3) and rang.get(e[0], 3)]
            if not proche:
                garde.append(e)
            elif rang.get(e[0], 3) < min(rang.get(g[0], 3) for g in proche):
                for g in proche:
                    garde.remove(g)
                garde.append(e)
        sfx = sorted(garde, key=lambda e: e[1])
        (proj / "assets" / "audio").mkdir(parents=True, exist_ok=True)
        (proj / "assets" / "audio" / "sfx-events.json").write_text(json.dumps(sfx, ensure_ascii=False), encoding="utf-8")
    for s in film["sentences"]:
        s.pop("_ws", None)
    (proj / "film.resolu.json").write_text(json.dumps(film, ensure_ascii=False, indent=1), encoding="utf-8")
    nchunks = subs.count('class="chunk')
    print(f"index.html : {len(doc)//1024} Ko, {D} s, {nchunks} morceaux de sous-titres ; "
          f"table 0–{night['end']:.2f}, pli {pv['fold_at']:.2f}, papier {paper['start']:.2f}–{paper['end']:.2f}"
          + (f", déchirure {tear['at']:.2f}" if tear else "") + f", fin {en['start']:.2f}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
