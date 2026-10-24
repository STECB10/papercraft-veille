#!/usr/bin/env python3
"""Moteur de la série Papercraft.AI : film.json + onsets.json -> index.html HyperFrames (1080 x 1350, 30 i/s).

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
FOLD_DUR = 1.0  # durée d'un pli (pivot et fin)
# décalage vertical de la caméra par type de station, pour centrer le contenu au-dessus des sous-titres
CAM_DY = {"ai_scan": 20, "metric": 110, "key_points": 110, "studies_stack": 40, "gag_waiting": 230, "gag_clock": 200, "steps": 40, "face_to_face": 170, "flow_door": 150, "remaining_dots": 110,
          "id_card": 60, "two_groups": 0, "result_bars": 20}
STEP_DY = 360


def esc(s):
    return html.escape(str(s), quote=True)


def fmt_int(n):
    return f"{n:,}".replace(",", " ")


def norm(w):
    return w.replace("’", "'").strip(".,;:!?«»\"()…").lower()


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


ICONS = ["camera", "magnifier", "phone", "chair", "door", "check", "fundus", "doc", "clock", "calendar", "chart", "chip",
         "heart", "pill", "hospital", "eye", "brain", "stethoscope", "user", "users", "message", "xray", "ecg", "skin", "mic"]

TIME_KEYS = {"at", "cam_at", "start", "end", "lit_at", "count_at", "count_end", "split_at", "accent_at", "diff_at",
             "fold_at", "wordmark_at", "button_at", "click_at", "source_at", "note_at", "caption_at", "card_at",
             "door_at", "walk_at", "label_at", "check_at", "mark_at",
             "scan_at", "core_at", "out_at", "total_at", "patients_at"}


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


def build_subs(film, dark_ranges):
    out = []
    for sent in film["sentences"]:
        if sent.get("mode", "sub") != "sub":
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
        peak_toks = sent.get("peak", "").split()
        for c_i, ch in enumerate(chunks):
            t_in = times[ch[0][1]]
            t_out = times[chunks[c_i + 1][0][1]] - 0.02 if c_i + 1 < len(chunks) else end + 0.3
            dark = any(a <= t_in < b for a, b in dark_ranges)
            spans = []
            for tok, k in ch:
                t = times[k]
                if box and tok == box:
                    spans.append(f'<span class="w kw" data-t="{t:.2f}"><span class="bx"></span><span class="tx">{esc(tok)}</span></span>')
                elif peak_toks and tok in peak_toks:
                    first = tok == peak_toks[0]
                    stroke = '<span class="pkline"></span>' if first else ""
                    spans.append(f'<span class="w pk{" pk0" if first else ""}" data-t="{t:.2f}">{esc(tok)}{stroke}</span>')
                else:
                    spans.append(f'<span class="w" data-t="{t:.2f}">{esc(tok)}</span>')
            out.append(f'<div class="chunk {"dark" if dark else "light"}" data-in="{t_in:.2f}" data-out="{t_out:.2f}">{" ".join(spans)}</div>')
    return "\n".join(out)


def typo_words(text, ws, italic):
    toks = text.split()
    spans = []
    for k, tok in enumerate(toks):
        t = ws[min(k, len(ws) - 1)]["s"]
        it = " it" if italic and norm(tok) == norm(italic) else ""
        spans.append(f'<span class="tw{it}" data-t="{t:.2f}">{esc(tok)}</span>')
    return " ".join(spans)


# --------------------------------------------------------------------------------------------- stations nuit
def night_station(st):
    t = st["type"]
    y0 = st["y"]
    h = []
    if t == "hook_number":
        cap = st.get("caption_at", 2.3)
        h.append(f'<div class="mono" style="left:70px;top:{y0+52}px;width:640px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:22px;color:var(--ink-dim)" data-a="rise" data-t="0.35">{esc(st["header"])}</div>')
        h.append(f'<div class="rule" style="left:70px;top:{y0+94}px;width:620px" data-a="wipe" data-t="0.45"></div>')
        h.append(f'<div class="num" style="left:52px;top:{y0+130}px;font-size:280px" data-a="big" data-t="0.02" data-d="1.0">{esc(st["number"])}<span class="unit">{esc(st["unit"])}</span></div>')
        h.append(f'<div class="cap" style="left:72px;top:{y0+440}px;width:600px" data-a="rise" data-t="{cap:.2f}">{esc(st["caption"])}</div>')
        for i in range(st["people"]):
            fade = f' data-o="{st["lit_at"]:.2f}"' if i == st["lit"] else ""
            h.append(person_svg(80 + i * 128, y0 + 570, 170, "var(--paper-dim)", f'data-a="pop" data-t="{0.35 + i*0.09:.2f}"{fade}'))
        lx = 80 + st["lit"] * 128
        h.append(person_svg(lx, y0 + 570, 170, "var(--carbon)", f'data-a="step" data-t="{st["lit_at"]:.2f}"', cls="pers lit"))
        h.append(f'<div class="mono" style="left:72px;top:{y0+776}px;color:var(--ink-dim);font-size:24px" data-a="rise" data-t="{cap+0.6:.2f}">{esc(st["footnote"])}</div>')
    elif t == "gag_waiting":
        ta = st["cam_at"]
        h.append(f'<div class="mono" style="left:500px;top:{y0+40}px;width:240px;text-align:center;color:var(--ink)" data-a="rise" data-t="{ta+0.25:.2f}">{esc(st["door"])}</div>')
        h.append(f'<div class="ico door" style="left:520px;top:{y0+80}px;width:200px;height:320px;color:var(--ink)" data-a="draw" data-t="{ta+0.1:.2f}">{icon("door")}</div>')
        h.append(f'<div class="doorlight" style="left:526px;top:{y0+86}px;width:188px;height:308px" data-a="fade" data-t="{ta+0.6:.2f}"></div>')
        h.append(f'<div class="clock" style="left:220px;top:{y0+60}px" data-a="pop" data-t="{ta+0.3:.2f}"><div class="hand" data-fx="spin" data-t="{ta+0.5:.2f}" data-d="2.4"></div><div class="hand2" data-fx="spin2" data-t="{ta+0.5:.2f}" data-d="2.4"></div><div class="pin"></div></div>')
        for i in range(st["chairs"]):
            h.append(f'<div class="ico" style="left:{60 + i*76}px;top:{y0+330}px;width:72px;height:82px;color:var(--ink-dim)" data-a="pop" data-t="{ta+0.35+i*0.07:.2f}">{icon("chair")}</div>')
        ox = 60 + (st["occupied"] - 1) * 76 + 10
        h.append(person_svg(ox, y0 + 262, 140, "var(--paper-dim)", f'data-a="pop" data-t="{ta+0.9:.2f}" data-fx="wait" data-fxt="{ta+1.3:.2f}"'))
    elif t == "gag_clock":
        ta = st["cam_at"]
        h.append(f'<div class="clock big" style="left:{(780-300)/2:.0f}px;top:{y0+40}px" data-a="pop" data-t="{ta+0.2:.2f}"><div class="hand" data-fx="spin" data-t="{ta+0.4:.2f}" data-d="2.4"></div><div class="hand2" data-fx="spin2" data-t="{ta+0.4:.2f}" data-d="2.4"></div><div class="pin"></div></div>')
        h.append(f'<div class="note" style="left:0;width:780px;text-align:center;top:{y0+380}px" data-a="rise" data-t="{ta+0.9:.2f}">{esc(st["label"])}</div>')
    elif t == "steps":
        ta = st["cam_at"]
        h.append(f'<div class="title" style="left:70px;top:{y0+10}px" data-a="rise" data-t="{ta+0.15:.2f}">{esc(st["title"])}</div>')
        h.append(f'<div class="rule" style="left:72px;top:{y0+92}px;width:520px" data-a="wipe" data-t="{st.get("mark_at", ta+0.9):.2f}"></div>')
        for i, s in enumerate(st["steps"]):
            sy = y0 + 170 + i * 330
            s["_y"] = sy
            at = s["at"]
            tall = s["icon"] == "phone"
            na = s.get("note_at", at + 0.5)
            buzz = f'data-fx="buzz" data-fxt="{na:.2f}"' if s.get("alert") else ""
            alert = f'<div class="alert">{esc(s["alert"])}</div>' if s.get("alert") else ""
            h.append(f'<div class="ico" style="left:{100 if tall else 84}px;top:{sy}px;width:{100 if tall else 130}px;height:{186 if tall else 110}px;color:var(--ink)" data-a="pop" data-t="{at:.2f}" {buzz}>{icon(s["icon"])}{alert}</div>')
            if s.get("alert"):
                h.append(f'<svg class="buzzl" style="left:40px;top:{sy+20}px;width:220px;height:150px" viewBox="0 0 220 150" fill="none" stroke="#5D68FF" stroke-width="5" stroke-linecap="round" data-a="fade" data-t="{na:.2f}"><path d="M30 35c-14 24-14 56 0 80"/><path d="M190 35c14 24 14 56 0 80"/></svg>')
            h.append(f'<div class="mono" style="left:270px;top:{sy+16}px;color:var(--ink-dim)" data-a="rise" data-t="{at+0.1:.2f}">{esc(s["label"])}</div>')
            if s.get("note"):
                h.append(f'<div class="note" style="left:266px;top:{sy+52}px" data-a="rise" data-t="{na:.2f}">{esc(s["note"])}</div>')
            for c_i, c in enumerate(s.get("chips", [])):
                acc = " acc" if c_i == len(s["chips"]) - 1 else ""
                h.append(f'<div class="chip{acc}" style="left:{270 + c_i*96}px;top:{sy+140}px" data-a="pop" data-t="{na+0.3+c_i*0.2:.2f}">{esc(c)}</div>')
            if i < len(st["steps"]) - 1:
                top = sy + (200 if tall else 128)
                h.append(f'<div class="dash" style="left:147px;top:{top}px;height:{sy+330-top-12}px" data-a="grow" data-t="{st["steps"][i+1]["at"]-0.4:.2f}"></div>')
    return "\n".join(h)


# --------------------------------------------------------------------------------------------- stations papier
def dots_svg(n, cols, cell, r, k=0, color="#5D68FF", hollow=False):
    rows = math.ceil(n / cols)
    wpx, hpx = cols * cell, rows * cell
    base, lit = [], []
    for i in range(n):
        cx = (i % cols) * cell + cell / 2
        cy = (i // cols) * cell + cell / 2
        if hollow:
            base.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r-1:.1f}" fill="none" stroke="#16171C" stroke-opacity=".38" stroke-width="1.6"/>')
        else:
            base.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#16171C" fill-opacity=".13"/>')
        if i < k:
            lit.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{color}"/>')
    return wpx, hpx, "".join(base), "".join(lit)


def paper_station(st, film):
    t = st["type"]
    y0 = st["y"]
    h = []
    if t == "population_split":
        ct, sp = st["count_at"], st["split_at"]
        cd = max(0.8, st.get("count_end", ct + 1.4) - ct)
        h.append(f'<div class="num center" style="left:0;width:{W}px;top:{y0+80}px;font-size:150px" data-a="big" data-t="{ct-0.05:.2f}" data-d="0.55"><span data-fx="count" data-t="{ct:.2f}" data-d="{cd:.2f}" data-to="{st["total"]}" data-dec="0">0</span></div>')
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+262}px;color:var(--ink-dim)" data-a="rise" data-t="{ct+0.5:.2f}">{esc(st["total_label"])}</div>')
        n = round(st["total"] / st["dot_value"])
        cols, cell = 17, 34
        rows = math.ceil(n / cols)
        gx0 = (W - cols * cell) / 2
        gy0 = y0 + 392
        rnd = random.Random(7)
        perm = list(range(n))
        rnd.shuffle(perm)
        g0n = round(st["groups"][0]["n"] / st["dot_value"])
        left_ids = set(perm[:g0n])
        bc = 8
        lx0 = W / 2 - 46 - bc * cell
        rx0 = W / 2 + 46
        li = ri = 0
        circles = []
        for i in range(n):
            cx = gx0 + (i % cols) * cell + cell / 2
            cy = gy0 + (i // cols) * cell + cell / 2
            if i in left_ids:
                tx, ty, side = lx0 + (li % bc) * cell + cell / 2, gy0 + (li // bc) * cell + cell / 2, "L"
                li += 1
            else:
                tx, ty, side = rx0 + (ri % bc) * cell + cell / 2, gy0 + (ri // bc) * cell + cell / 2, "R"
                ri += 1
            circles.append(f'<circle class="pd pd{side}" cx="{cx:.1f}" cy="{cy:.1f}" r="10" fill="#16171C" fill-opacity=".72" '
                           f'data-dx="{tx-cx:.1f}" data-dy="{ty-cy:.1f}" data-dl="{rnd.uniform(0, 0.35):.3f}" data-ap="{(i / n) * min(cd, 1.4) * 0.9 + rnd.uniform(0, 0.12):.3f}"/>')
        hsvg = gy0 + max(rows, math.ceil(max(li, ri) / bc)) * cell + 20
        h.append(f'<svg class="dots" style="left:0;top:0;width:{W}px;height:{hsvg:.0f}px;overflow:visible" viewBox="0 0 {W} {hsvg:.0f}" '
                 f'data-fx="popdots" data-t="{ct+0.1:.2f}" data-split="{sp:.2f}" data-acc="{st["groups"][1].get("accent_at", sp + 1):.2f}">{"".join(circles)}</svg>')
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{gy0+rows*cell+18}px;color:var(--ink-dim);font-size:24px" data-a="rise" data-t="{ct+0.9:.2f}" data-o="{sp:.2f}">1 point = {st["dot_value"]} patients</div>')
        by = gy0 + math.ceil(max(li, ri) / bc) * cell + 22
        g0, g1 = st["groups"]
        h.append(f'<div class="glab" style="left:{lx0-40:.0f}px;top:{by:.0f}px;width:{bc*cell+80}px" data-a="rise" data-t="{sp+0.6:.2f}">{esc(g0["label"])}<span class="gn">{fmt_int(g0["n"])} patients</span></div>')
        h.append(f'<div class="glab acc" style="left:{rx0-40:.0f}px;top:{by:.0f}px;width:{bc*cell+80}px" data-a="rise" data-t="{sp+0.7:.2f}">{esc(g1["label"])}<span class="gn">{fmt_int(g1["n"])} patients</span></div>')
        acc = g1.get("accent_at", sp + 1)
        h.append(f'<div class="pill acc" style="left:{rx0 + bc*cell/2 - 150:.0f}px;top:{gy0-70}px" data-a="pop" data-t="{acc:.2f}">Avec IA</div>')
        h.append(f'<div class="ico" style="left:{rx0 + bc*cell/2 + 70:.0f}px;top:{gy0-70}px;width:56px;height:56px;color:var(--carbon-deep)" data-a="pop" data-t="{acc+0.6:.2f}">{icon("fundus", sw=6)}</div>')
    elif t == "face_to_face":
        at = st["at"]
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+80}px;color:var(--ink-dim)" data-a="rise" data-t="{st.get("label_at", at+1.1):.2f}">{esc(st["label"])}</div>')
        h.append(person_svg(140, y0 + 220, 340, "var(--ink)", f'data-a="slideL" data-t="{at:.2f}"'))
        h.append(person_svg(804, y0 + 220, 340, "var(--carbon)", f'data-a="slideR" data-t="{at+0.15:.2f}"'))
        h.append(f'<div class="card" style="left:335px;top:{y0+250}px;width:410px" data-a="pop" data-t="{st.get("card_at", at+0.55):.2f}">'
                 f'<div class="mono s" style="color:var(--ink-dim);font-size:24px">{esc(st["card_title"])}</div>'
                 f'<div class="cardv">{esc(st["card_value"])}</div>'
                 f'<div class="mono s" style="color:var(--carbon-deep);font-size:22px;margin-top:12px;letter-spacing:.04em">{esc(st["card_note"])}</div></div>')
        h.append(f'<div class="ico" style="left:510px;top:{y0+520}px;width:60px;height:60px;color:var(--carbon-deep)" data-a="pop" data-t="{st.get("check_at", at+1.6):.2f}">{icon("check")}</div>')
    elif t == "result_dots":
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+50}px;color:var(--ink-dim)" data-a="rise" data-t="{st["cam_at"]+0.3:.2f}">{esc(st["title"])}</div>')
        h.append(f'<div class="rule" style="left:120px;top:{y0+86}px;width:{W-240}px" data-a="wipe" data-t="{st["cam_at"]+0.4:.2f}"></div>')
        cols, cell, r = 19, 23, 7.5
        bw = cols * cell
        gap = 70
        x0s = [(W - 2 * bw - gap) / 2, (W - 2 * bw - gap) / 2 + bw + gap]
        hpx = 0
        for gi, g in enumerate(st["groups"]):
            x0 = x0s[gi]
            col = "#5D68FF" if g.get("accent") else "#16171C"
            wpx, hpx, base, lit = dots_svg(g["n"], cols, cell, r, g["k"], col)
            h.append(f'<svg class="dots" style="left:{x0:.0f}px;top:{y0+290}px;width:{wpx}px;height:{hpx}px" viewBox="0 0 {wpx} {hpx}" data-a="fade" data-t="{st["cam_at"]+0.2+gi*0.1:.2f}">{base}</svg>')
            h.append(f'<svg class="dots" style="left:{x0:.0f}px;top:{y0+290}px;width:{wpx}px;height:{hpx}px" viewBox="0 0 {wpx} {hpx}" data-fx="litdots" data-t="{g["at"]:.2f}" data-d="1.0">{lit}</svg>')
            colr = "var(--ink)" if g.get("accent") else "var(--ink-dim)"
            h.append(f'<div class="num" style="left:{x0:.0f}px;width:{bw}px;text-align:center;top:{y0+120}px;font-size:124px;color:{colr}" data-a="big" data-t="{g["at"]-0.05:.2f}" data-d="0.5">'
                     f'<span data-fx="count" data-t="{g["at"]:.2f}" data-d="1.0" data-to="{str(g["value"]).replace(",", ".")}" data-dec="1">0</span><span class="unit">%</span></div>')
            lc = "var(--carbon-deep)" if g.get("accent") else "var(--ink-dim)"
            acc_cls = " acc" if g.get("accent") else ""
            h.append(f'<div class="glab{acc_cls}" style="left:{x0-30:.0f}px;width:{bw+60}px;top:{y0+290+hpx+22}px" data-a="rise" data-t="{g["at"]+0.3:.2f}">{esc(g["label"])}<span class="gn">{g["k"]} sur {g["n"]}</span></div>')
        h.append(f'<div class="pillwrap" style="left:0;width:{W}px;top:{y0+290+hpx+128}px" data-a="pop" data-t="{st["diff_at"]:.2f}"><span class="pill acc">{esc(st["diff"])}</span></div>')
    elif t == "typo":
        ws = film["sentences"][st["sentence"]]["_ws"]
        h.append(f'<div class="typo" style="left:90px;width:{W-180}px;top:{y0+400}px">{typo_words(st["text"], ws, st.get("italic"))}</div>')
        h.append(f'<div class="rule" style="left:{W/2-60:.0f}px;top:{y0+700}px;width:120px" data-a="wipe" data-t="{ws[-1]["s"]:.2f}"></div>')
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
        for k in range(3):
            h.append(person_svg(140 + k * 70, y0 + 480, 150, "var(--carbon)",
                                f'data-a="pop" data-t="{ca+0.3+k*0.1:.2f}" data-fx="walk" data-fxt="{wa+k*0.2:.2f}" data-d="1.4" data-dx="{620 - k*40}"'))
    elif t == "id_card":
        rows = st["rows"]
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+40}px;color:var(--ink-dim)" data-a="rise" data-t="{st["cam_at"]+0.25:.2f}">{esc(st.get("title", "L'étude en bref"))}</div>')
        h.append(f'<div class="idcard" style="left:90px;top:{y0+100}px;width:{W-180}px;height:{70 + len(rows)*118}px" data-a="pop" data-t="{st["cam_at"]+0.15:.2f}"></div>')
        for i, r in enumerate(rows):
            ry = y0 + 140 + i * 118
            h.append(f'<div class="mono" style="left:130px;top:{ry+14}px;width:250px;color:var(--ink-dim);font-size:24px" data-a="rise" data-t="{r["at"]-0.05:.2f}">{esc(r["label"])}</div>')
            acc = "color:var(--carbon-deep);" if r.get("accent") else ""
            h.append(f'<div class="idv" style="left:390px;top:{ry}px;width:{W-90-390-40}px;{acc}" data-a="rise" data-t="{r["at"]:.2f}">{esc(r["value"])}</div>')
            if i < len(rows) - 1:
                h.append(f'<div class="rule" style="left:130px;top:{ry+96}px;width:{W-260}px" data-a="wipe" data-t="{r["at"]+0.1:.2f}"></div>')
    elif t == "two_groups":
        cols = st["groups"]
        cw = (W - 64 * 2 - 40) / 2
        for gi, g in enumerate(cols):
            x0 = 64 + gi * (cw + 40)
            acc = g.get("accent")
            h.append(f'<div class="gcol{" acc" if acc else ""}" style="left:{x0:.0f}px;top:{y0+100}px;width:{cw:.0f}px;height:{140 + len(g["steps"])*196}px" data-a="pop" data-t="{g["at"]:.2f}"></div>')
            h.append(f'<div class="pill{" acc" if acc else ""}" style="left:{x0+28:.0f}px;top:{y0+130}px" data-a="pop" data-t="{g["at"]+0.1:.2f}">{esc(g["label"])}</div>')
            if g.get("sub"):
                h.append(f'<div class="mono" style="left:{x0+30:.0f}px;top:{y0+188}px;width:{cw-60:.0f}px;color:var(--ink-dim);font-size:24px;letter-spacing:.04em" data-a="rise" data-t="{g["at"]+0.25:.2f}">{esc(g["sub"])}</div>')
            for k, stp in enumerate(g["steps"]):
                sy = y0 + 240 + k * 196
                colr = "var(--carbon-deep)" if acc else "var(--ink)"
                h.append(f'<div class="ico" style="left:{x0+30:.0f}px;top:{sy}px;width:64px;height:64px;color:{colr}" data-a="pop" data-t="{stp["at"]:.2f}">{icon(stp.get("icon", "doc"))}</div>')
                h.append(f'<div class="gstep" style="left:{x0+112:.0f}px;top:{sy-4}px;width:{cw-140:.0f}px" data-a="rise" data-t="{stp["at"]+0.05:.2f}">{esc(stp["text"])}</div>')
                if k < len(g["steps"]) - 1:
                    h.append(f'<div class="dash" style="left:{x0+61:.0f}px;top:{sy+76}px;height:104px" data-a="grow" data-t="{g["steps"][k+1]["at"]-0.35:.2f}"></div>')
    elif t == "result_bars":
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+50}px;color:var(--ink-dim)" data-a="rise" data-t="{st["cam_at"]+0.3:.2f}">{esc(st["title"])}</div>')
        h.append(f'<div class="rule" style="left:120px;top:{y0+86}px;width:{W-240}px" data-a="wipe" data-t="{st["cam_at"]+0.4:.2f}"></div>')
        gs = st["groups"]
        top = max(float(g["num"]) for g in gs) or 1
        bw, gap, base = 240, 120, y0 + 820
        x0 = (W - len(gs) * bw - (len(gs) - 1) * gap) / 2
        for gi, g in enumerate(gs):
            x = x0 + gi * (bw + gap)
            hgt = max(12, 520 * float(g["num"]) / top)
            cls = "bar acc" if g.get("accent") else "bar"
            h.append(f'<div class="{cls}" style="left:{x:.0f}px;top:{base-hgt:.0f}px;width:{bw}px;height:{hgt:.0f}px" data-a="growup" data-t="{g["at"]:.2f}"></div>')
            colr = "var(--ink)" if g.get("accent") else "var(--ink-dim)"
            dec = len(str(g["value"]).split(",")[1]) if "," in str(g["value"]) else 0
            h.append(f'<div class="num" style="left:{x-40:.0f}px;width:{bw+80}px;text-align:center;top:{base-hgt-130:.0f}px;font-size:104px;color:{colr}" data-a="big" data-t="{g["at"]-0.05:.2f}" data-d="0.5">'
                     f'<span data-fx="count" data-t="{g["at"]:.2f}" data-d="1.0" data-to="{str(g["value"]).replace(",", ".")}" data-dec="{dec}">0</span><span class="unit">{esc(st.get("unit", ""))}</span></div>')
            lc = "var(--carbon-deep)" if g.get("accent") else "var(--ink-dim)"
            acc_cls = " acc" if g.get("accent") else ""
            h.append(f'<div class="glab{acc_cls}" style="left:{x-50:.0f}px;width:{bw+100}px;top:{base+20}px" data-a="rise" data-t="{g["at"]+0.3:.2f}">{esc(g["label"])}</div>')
        h.append(f'<div class="rule" style="left:{x0-30:.0f}px;top:{base}px;width:{len(gs)*bw+(len(gs)-1)*gap+60:.0f}px" data-a="wipe" data-t="{st["cam_at"]+0.4:.2f}"></div>')
        if st.get("diff"):
            h.append(f'<div class="pillwrap" style="left:0;width:{W}px;top:{base+110}px" data-a="pop" data-t="{st["diff_at"]:.2f}"><span class="pill acc">{esc(st["diff"])}</span></div>')
    elif t == "ai_scan":
        # ce que fait l'IA : ce qui entre -> l'IA qui analyse (balayage, réseau qui s'allume) -> ce qui sort
        ta, at = st["cam_at"], st["at"]
        sa = st.get("scan_at", at + 0.8)
        ca = st.get("core_at", sa + 0.3)
        oa = st.get("out_at", ca + 1.4)
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+30}px;color:var(--ink-dim)" data-a="rise" data-t="{ta+0.2:.2f}">{esc(st.get("title", "Ce que fait l'IA"))}</div>')
        # 1. entrée
        h.append(f'<div class="aibox" style="left:80px;top:{y0+100}px;width:{W-160}px;height:250px" data-a="pop" data-t="{at-0.1:.2f}"></div>')
        h.append(f'<div class="scanglow" style="left:110px;top:{y0+130}px;width:200px;height:190px" data-a="fade" data-t="{sa:.2f}" data-o="{sa+1.6:.2f}"></div>')
        h.append(f'<div class="ico" style="left:130px;top:{y0+150}px;width:160px;height:150px;color:var(--ink)" data-a="draw" data-t="{at:.2f}">{icon(st.get("input_icon", "doc"))}</div>')
        h.append(f'<div class="scanbeam" style="left:110px;top:{y0+138}px;width:200px" data-fx="scan" data-t="{sa:.2f}" data-d="1.5" data-dy="170"></div>')
        h.append(f'<div class="aikick" style="left:340px;top:{y0+150}px" data-a="rise" data-t="{at+0.1:.2f}">Ce qui entre</div>')
        h.append(f'<div class="ailab" style="left:340px;top:{y0+192}px;width:{W-160-300}px" data-a="rise" data-t="{at+0.2:.2f}">{esc(st["input_label"])}</div>')
        # 2. l'IA
        h.append(f'<div class="dash" style="left:{W/2-1.5:.0f}px;top:{y0+362}px;height:76px" data-a="grow" data-t="{ca-0.35:.2f}"></div>')
        h.append(f'<div class="aicore" style="left:80px;top:{y0+450}px;width:{W-160}px;height:250px" data-a="pop" data-t="{ca-0.1:.2f}"></div>')
        nodes = [(0, [62, 125, 188]), (1, [40, 94, 156, 210]), (2, [62, 125, 188]), (3, [125])]
        pts = [(30 + c * 70, y) for c, ys in nodes for y in ys]
        edges = "".join(f'<path d="M{x1} {y1}L{x2} {y2}"/>' for (x1, y1) in pts for (x2, y2) in pts if x2 - x1 == 70)
        base_n = "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="#1B1D25" stroke="#A3A9FF" stroke-opacity=".5" stroke-width="2"/>' for x, y in pts)
        lit_n = "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="#5D68FF"/>' for x, y in pts)
        h.append(f'<svg class="dots" style="left:120px;top:{y0+450}px;width:270px;height:250px" viewBox="0 0 270 250" data-a="fade" data-t="{ca:.2f}">'
                 f'<g fill="none" stroke="#A3A9FF" stroke-opacity=".28" stroke-width="2">{edges}</g>{base_n}</svg>')
        h.append(f'<svg class="dots" style="left:120px;top:{y0+450}px;width:270px;height:250px" viewBox="0 0 270 250" data-fx="litdots" data-t="{ca+0.2:.2f}" data-d="1.0">{lit_n}</svg>')
        h.append(f'<div class="aikick lt" style="left:430px;top:{y0+500}px" data-a="rise" data-t="{ca+0.1:.2f}">{esc(st.get("ai_name", "L'IA"))}</div>')
        h.append(f'<div class="ailab lt" style="left:430px;top:{y0+542}px;width:{W-160-390}px" data-a="rise" data-t="{ca+0.25:.2f}">{esc(st["ai_label"])}</div>')
        # 3. sortie
        h.append(f'<div class="dash" style="left:{W/2-1.5:.0f}px;top:{y0+712}px;height:76px" data-a="grow" data-t="{oa-0.35:.2f}"></div>')
        h.append(f'<div class="aibox out" style="left:80px;top:{y0+800}px;width:{W-160}px;height:250px" data-a="pop" data-t="{oa-0.1:.2f}"></div>')
        h.append(f'<div class="ico" style="left:140px;top:{y0+865}px;width:120px;height:120px;color:var(--carbon-deep)" data-a="pop" data-t="{oa+0.15:.2f}">{icon("check")}</div>')
        h.append(f'<div class="aikick" style="left:300px;top:{y0+850}px;color:var(--carbon-deep)" data-a="rise" data-t="{oa:.2f}">Ce qui sort</div>')
        h.append(f'<div class="ailab big" style="left:300px;top:{y0+892}px;width:{W-160-260}px" data-a="rise" data-t="{oa+0.1:.2f}">{esc(st["output_label"])}</div>')
        if st.get("output_note"):
            h.append(f'<div class="ainote" style="left:300px;top:{y0+1000}px;width:{W-160-260}px" data-a="rise" data-t="{oa+0.5:.2f}">{esc(st["output_note"])}</div>')
    elif t == "studies_stack":
        # méta-analyse / revue : les études regroupées, une icône-feuille par étude (ou par lot d'études)
        ta, at = st["cam_at"], st["at"]
        n = int(st["n_studies"])
        per = max(1, math.ceil(n / 40))
        k = math.ceil(n / per)
        cols = 8 if k > 16 else (6 if k > 9 else 4)
        cw, ch = 104, 124
        gx = (W - cols * cw) / 2
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+30}px;color:var(--ink-dim)" data-a="rise" data-t="{ta+0.2:.2f}">{esc(st.get("title", "Les études regroupées"))}</div>')
        h.append(f'<div class="num center" style="left:0;width:{W}px;top:{y0+90}px;font-size:170px" data-a="big" data-t="{at-0.05:.2f}" data-d="0.6">'
                 f'<span data-fx="count" data-t="{at:.2f}" data-d="{min(1.4, 0.4 + k * 0.03):.2f}" data-to="{n}" data-dec="0">0</span></div>')
        h.append(f'<div class="glab" style="left:0;width:{W}px;top:{y0+270}px" data-a="rise" data-t="{at+0.3:.2f}">{esc(st.get("label", "études"))}</div>')
        gy = y0 + 360
        for i in range(k):
            x, y = gx + (i % cols) * cw + 12, gy + (i // cols) * ch
            acc = "var(--carbon-deep)" if i % 7 == 3 else "var(--ink)"
            h.append(f'<div class="ico" style="left:{x:.0f}px;top:{y:.0f}px;width:80px;height:100px;color:{acc}" data-a="pop" data-t="{at + 0.15 + (i / max(1, k - 1)) * 1.2:.2f}">{icon("doc", sw=4)}</div>')
        rows = math.ceil(k / cols)
        by = gy + rows * ch + 10
        if per > 1:
            h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{by}px;color:var(--ink-dim);font-size:22px" data-a="rise" data-t="{at+1.0:.2f}">1 feuille = {per} études</div>')
            by += 46
        if st.get("n_patients"):
            pa = st.get("patients_at", at + 1.6)
            h.append(f'<div class="glab acc" style="left:0;width:{W}px;top:{by+20}px;font-size:40px" data-a="rise" data-t="{pa:.2f}">'
                     f'<span data-fx="count" data-t="{pa:.2f}" data-d="1.0" data-to="{int(st["n_patients"])}" data-dec="0">0</span> patients au total</div>')
            by += 80
        if st.get("sub"):
            h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{by+24}px;color:var(--ink-dim)" data-a="rise" data-t="{st.get("patients_at", at + 1.6) + 0.4:.2f}">{esc(st["sub"])}</div>')
    elif t == "metric":
        # performance d'un modèle ou résultat regroupé : 1 à 3 jauges circulaires qui se remplissent
        ms = st["metrics"]
        m = len(ms)
        size = {1: 440, 2: 400, 3: 300}[m]
        gap = 40
        x0 = (W - m * size - (m - 1) * gap) / 2
        top = y0 + 150
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+40}px;color:var(--ink-dim)" data-a="rise" data-t="{st["cam_at"]+0.25:.2f}">{esc(st["title"])}</div>')
        h.append(f'<div class="rule" style="left:120px;top:{y0+80}px;width:{W-240}px" data-a="wipe" data-t="{st["cam_at"]+0.35:.2f}"></div>')
        for i, g in enumerate(ms):
            x = x0 + i * (size + gap)
            mx = float(g.get("max", 100))
            frac = max(0.0, min(1.0, float(g["num"]) / mx))
            acc = g.get("accent", i == 0)
            col = "#5D68FF" if acc else "#16171C"
            r, sw = 44, 7
            circ = 2 * math.pi * r
            h.append(f'<svg class="dots" style="left:{x:.0f}px;top:{top}px;width:{size}px;height:{size}px" viewBox="0 0 100 100" data-a="fade" data-t="{g["at"]-0.3:.2f}">'
                     f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#16171C" stroke-opacity=".10" stroke-width="{sw}"/>'
                     f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" transform="rotate(-90 50 50)" '
                     f'stroke-dasharray="{circ:.2f}" stroke-dashoffset="{circ:.2f}" data-fx="ring" data-t="{g["at"]:.2f}" data-d="1.1" data-off="{circ * (1 - frac):.2f}"/></svg>')
            dec = len(str(g["value"]).split(",")[1]) if "," in str(g["value"]) else 0
            fs = {1: 150, 2: 128, 3: 96}[m]
            colr = "var(--ink)" if acc else "var(--ink-dim)"
            h.append(f'<div class="num" style="left:{x:.0f}px;width:{size}px;text-align:center;top:{top + size/2 - fs*0.48:.0f}px;font-size:{fs}px;color:{colr}" data-a="big" data-t="{g["at"]-0.05:.2f}" data-d="0.5">'
                     f'<span data-fx="count" data-t="{g["at"]:.2f}" data-d="1.0" data-to="{str(g["value"]).replace(",", ".")}" data-dec="{dec}">0</span><span class="unit">{esc(g.get("unit", ""))}</span></div>')
            acc_cls = " acc" if acc else ""
            h.append(f'<div class="glab{acc_cls}" style="left:{x-20:.0f}px;width:{size+40}px;top:{top+size+28}px" data-a="rise" data-t="{g["at"]+0.3:.2f}">{esc(g["label"])}'
                     + (f'<span class="gn">{esc(g["note"])}</span>' if g.get("note") else "") + '</div>')
        if st.get("caption"):
            h.append(f'<div class="cap center" style="left:110px;width:{W-220}px;top:{top+size+150}px;font-size:34px;color:var(--ink-dim)" data-a="rise" data-t="{st.get("caption_at", ms[-1]["at"] + 0.8):.2f}">{esc(st["caption"])}</div>')
    elif t == "key_points":
        # constats numérotés (revue, cohorte, étude qualitative…), chacun au mot qui l'énonce
        pts = st["points"]
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+40}px;color:var(--ink-dim)" data-a="rise" data-t="{st["cam_at"]+0.25:.2f}">{esc(st.get("title", "Ce qu'il faut retenir"))}</div>')
        hh = 200 if len(pts) <= 3 else 176
        for i, pt in enumerate(pts):
            y = y0 + 110 + i * (hh + 26)
            h.append(f'<div class="aibox" style="left:80px;top:{y}px;width:{W-160}px;height:{hh}px" data-a="slideL" data-t="{pt["at"]-0.1:.2f}"></div>')
            h.append(f'<div class="kpn" style="left:120px;top:{y + hh/2 - 52:.0f}px" data-a="pop" data-t="{pt["at"]:.2f}">{i + 1}</div>')
            h.append(f'<div class="ailab" style="left:250px;top:{y + hh/2 - 50:.0f}px;width:{W-160-210}px;height:100px;display:flex;align-items:center" data-a="rise" data-t="{pt["at"]+0.1:.2f}">{esc(pt["text"])}</div>')
    elif t == "remaining_dots":
        at = st["at"]
        cols, cell, r = 23, 22, 7
        wpx, hpx, base, lit = dots_svg(st["n"], cols, cell, r, st["k"], "#5D68FF", hollow=True)
        x0 = (W - wpx) / 2
        h.append(f'<div class="num center" style="left:0;width:{W}px;top:{y0+30}px;font-size:150px" data-a="big" data-t="{at-0.05:.2f}" data-d="0.55"><span data-fx="count" data-t="{at:.2f}" data-d="1.1" data-to="{st["value"]}" data-dec="0">0</span><span class="unit">%</span></div>')
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+210}px;color:var(--ink-dim)" data-a="rise" data-t="{at+0.5:.2f}">{esc(st["label"])}</div>')
        h.append(f'<svg class="dots" style="left:{x0:.0f}px;top:{y0+290}px;width:{wpx}px;height:{hpx}px" viewBox="0 0 {wpx} {hpx}" data-fx="litdots" data-t="{at+0.15:.2f}" data-d="1.0">{base}</svg>')
        h.append(f'<svg class="dots" style="left:{x0:.0f}px;top:{y0+290}px;width:{wpx}px;height:{hpx}px" viewBox="0 0 {wpx} {hpx}" data-a="fade" data-t="{st["cam_at"]+0.1:.2f}">{lit}</svg>')
        h.append(f'<div class="mono center" style="left:0;width:{W}px;top:{y0+290+hpx+20}px;color:var(--carbon-deep);font-size:24px" data-a="rise" data-t="{st["cam_at"]+0.35:.2f}">{esc(st["group_label"])} · {st["k"]} venus · {st["n"]-st["k"]} absents</div>')
    return "\n".join(h)


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
    # temps dérivés : la nuit s'arrête, noir, texte du pivot, pli vers le papier ; à la fin, pli du papier vers la nuit
    pv["start"] = night["end"]
    pv["end"] = pv["fold_at"] + FOLD_DUR + 0.05
    paper["start"] = pv["fold_at"] - 0.05
    en["start"] = en["fold_at"] - 0.05
    paper["end"] = en["fold_at"] + FOLD_DUR + 0.05
    en["end"] = D

    for st in paper["stations"]:
        if st["type"] == "typo":
            st["sentence"] = find_sentence(st["text"])

    night_html = "\n".join(night_station(st) for st in night["stations"])
    paper_html = "\n".join(paper_station(st, film) for st in paper["stations"])
    world_h = max(st["y"] for st in paper["stations"]) + 1600

    ncam = []
    for st in night["stations"]:
        ncam.append([st["cam_at"], -st["y"] + CAM_DY.get(st["type"], 0)])
        if st["type"] == "steps":
            for s in st["steps"][1:]:
                ncam.append([s["at"] - 0.3, -(s["_y"]) + STEP_DY])
    pcam = [[st["cam_at"], -st["y"] + CAM_DY.get(st["type"], 0)] for st in paper["stations"]]

    pv_ws = film["sentences"][find_sentence(pv["text"])]["_ws"]
    en_ws = film["sentences"][find_sentence(en["promise"])]["_ws"]
    dark = [(0, paper["start"] + 0.4), (en["fold_at"] + 0.4, D + 1)]
    subs = build_subs(film, dark)

    runtime = {"duration": D, "fold": FOLD_DUR, "ncam": ncam, "pcam": pcam,
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
  <div id="bgnight" class="clip" data-start="0" data-duration="{D}" data-track-index="0"><div class="halo" id="nhalo"></div></div>

  <div id="night" class="clip" data-start="{night['start']}" data-duration="{night['end']-night['start']:.3f}" data-track-index="1">
    <div class="persp"><div id="nplane"><div id="ncam">
      <div class="sheet" id="nsheet"><div class="corner"></div><div class="crease"></div>
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
    <div class="mono center" style="left:0;width:{W}px;top:960px;color:var(--paper-dim);font-size:24px;letter-spacing:.1em" data-a="rise" data-t="{en['source_at']:.2f}">{esc(en['source'])}</div>
    <div class="mono center" style="left:0;width:{W}px;top:992px;color:var(--paper-dim);font-size:24px;letter-spacing:.06em;text-transform:none" data-a="rise" data-t="{en['source_at']+0.15:.2f}">{esc(en['doi'])}</div>
    <svg id="cursor" viewBox="0 0 24 34" style="left:0;top:0;width:34px;height:48px"><path d="M2 2v26l7-6 5 10 4-2-5-10h9z" fill="#F7F3EC" stroke="#16171C" stroke-width="1.6" stroke-linejoin="round"/></svg>
  </div>

  <div id="paper" class="clip" data-start="{paper['start']:.3f}" data-duration="{paper['end']-paper['start']:.3f}" data-track-index="3">
    <div class="foldsheet" id="psheet">
      <div class="pground"></div><div class="pcrease"></div><div class="pcorner"></div>
      <div id="pcam"><div id="pworld" style="height:{world_h}px">
{paper_html}
      </div></div>
    </div>
    <div class="flapwrap"><div class="flap paperflap" id="pflap"></div></div>
    <div class="streak" id="pstreak"></div>
  </div>

  <div id="pivot" class="clip" data-start="{pv['start']:.3f}" data-duration="{pv['end']-pv['start']:.3f}" data-track-index="4">
    <div class="foldsheet" id="pvsheet">
      <div class="pvblack"></div>
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

    # bruitages déduits de la structure (mêmes règles chaque jour) : [nom, seconde, volume]
    if film.get("sfx", True):
        sfx = [["impact-bass-1", 0.0, 0.26]]
        for st in night["stations"]:
            if st["type"] == "hook_number":
                sfx.append(["pop", st["lit_at"], 0.2])
            if st["type"] == "steps":
                for s in st["steps"]:
                    if s.get("alert"):
                        sfx.append(["notification", s.get("note_at", s["at"] + 0.5), 0.16])
        sfx += [["whoosh-short", t + 0.05, 0.12] for t, _ in ncam[1:]]
        sfx.append(["whoosh-cinematic", pv["fold_at"] - 0.1, 0.26])
        for st in paper["stations"]:
            if st["type"] == "population_split":
                sfx += [["pop", st["count_at"], 0.16], ["whoosh-short", st["split_at"], 0.14],
                        ["ping", st["groups"][1].get("accent_at", st["split_at"] + 1), 0.13]]
            if st["type"] in ("result_bars",):
                sfx += [["ping", g["at"], 0.13] for g in st["groups"] if g.get("accent")]
                if st.get("diff_at"):
                    sfx.append(["pop", st["diff_at"], 0.18])
            if st["type"] == "metric":
                sfx += [["ping", g["at"], 0.13] for g in st["metrics"]]
            if st["type"] == "studies_stack":
                sfx += [["pop", st["at"], 0.16]]
            if st["type"] == "key_points":
                sfx += [["whoosh-short", pt["at"], 0.1] for pt in st["points"]]
            if st["type"] == "result_dots":
                sfx += [["ping", g["at"], 0.13] for g in st["groups"] if g.get("accent")]
                sfx.append(["pop", st["diff_at"], 0.18])
        sfx += [["whoosh-short", t + 0.05, 0.1] for t, _ in pcam[1:]]
        sfx += [["whoosh-cinematic", en["fold_at"] - 0.1, 0.22], ["chime", en["wordmark_at"], 0.2], ["click", en["click_at"], 0.45]]
        sfx = sorted([[n, round(max(0.0, t), 3), v] for n, t, v in sfx], key=lambda e: e[1])
        (proj / "assets" / "audio" / "sfx-events.json").write_text(json.dumps(sfx, ensure_ascii=False), encoding="utf-8")
    for s in film["sentences"]:
        s.pop("_ws", None)
    (proj / "film.resolu.json").write_text(json.dumps(film, ensure_ascii=False, indent=1), encoding="utf-8")
    nchunks = subs.count('class="chunk')
    print(f"index.html : {len(doc)//1024} Ko, {D} s, {nchunks} morceaux de sous-titres ; "
          f"nuit 0–{night['end']:.2f}, pli {pv['fold_at']:.2f}, papier {paper['start']:.2f}–{paper['end']:.2f}, fin {en['start']:.2f}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
