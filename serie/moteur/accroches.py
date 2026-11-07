"""Les accroches de la table (premier écran du film) et les moments muets : plusieurs mises en scène, choisies
selon l'étude, pour que deux vidéos ne s'ouvrent jamais de la même façon.

Toutes les tailles sont calculées avec les vraies chasses des polices (mesure.py) : un chiffre, un titre ou une légende
prend la plus grande taille qui tient dans sa boîte, et chaque bloc est posé sous le précédent (jamais l'un sur
l'autre). moteur.js refait une passe dans le navigateur sur tout ce qui porte data-fit.

Accroches (night.stations[0]) :
  hook_number    un chiffre clé, sa légende et une figure qui DIT ce chiffre (grille de 100 pour un %, petites
                 feuilles pour des études, k silhouettes allumées sur n pour « k sur n », grand dessin sinon)
  hook_question  la question d'ouverture en grande typo, mot à mot avec la voix, le mot clé souligné à la main
  hook_image     ce que l'étude regarde, redessiné au trait (fond d'œil, radio, peau, ECG, cœur, cerveau…), balayé
  hook_versus    deux chiffres face à face (avant / avec l'IA, deux groupes, deux mesures), ou un chiffre face à « ? »
  hook_headline  le titre de l'étude (traduit) sur une coupure de papier, la partie clé surlignée au feutre
Moments muets : gag_clock, gag_waiting (build.py), gag_calendar, gag_pile (ici).
"""
import math
import random

import mesure

HOOKS = ["hook_number", "hook_question", "hook_image", "hook_versus", "hook_headline"]
GAGS = ["gag_clock", "gag_waiting", "gag_calendar", "gag_pile"]
VISUALS = ["grid", "sheets", "people", "icon", "none"]
SX, SW = 70, 640            # zone utile de la feuille posée sur la table (780 px de large, coin plié à droite)
HOOK_H = 880                # hauteur d'une accroche sur la feuille (le cadre en montre ~ 900 px avant le sous-titre)
UNITES_COURTES = {"%", "‰", "mm", "cm", "m", "kg", "g", "h", "min", "s", "j", "ms", "€", "$", "ans", "an", "mois", "fois", "x", "×"}
PERSONNES = ("personne", "patient", "adulte", "enfant", "habitant", "femme", "homme", "malade", "participant", "soignant",
             "médecin", "infirmi", "bébé", "nouveau-né", "sujet", "volontaire", "élève", "étudiant")

B = None                    # le module build (injecté par build.py : icônes, images, échappement, couleurs)


def _esc(s):
    return B.esc(s)


def num_of(txt):
    """« 11,1 » -> 11.1 ; « 37 467 » -> 37467 ; None si ce n'est pas un nombre."""
    try:
        return float(str(txt).replace(" ", "").replace(" ", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return None


# --------------------------------------------------------------------------------------------- blocs de texte posés
def header(h, text, y, t, center=False):
    """En-tête mono de l'accroche (type d'étude · lieu · années) : une ou deux lignes, jamais coupé. Renvoie le bas du filet."""
    px = 26
    ls = mesure.lignes_segments(text, "mono500", px, SW, approche=0.07)
    if len(ls) > 2:   # trop long même sur deux lignes : on garde deux lignes, le navigateur réduit (data-fit)
        ls = [ls[0], " ".join(ls[1:])]
    al = "text-align:center;" if center else ""
    h.append(f'<div class="mono hhead" style="left:{SX}px;top:{y}px;width:{SW}px;{al}font-size:{px}px;color:var(--ink-dim)" '
             f'data-fit="1" data-fh="{len(ls) * 39 + 2}" data-fmin="22" data-a="rise" data-t="{max(0.15, t - 0.5):.2f}">'
             + "<br>".join(_esc(l) for l in ls) + '</div>')
    bot = y + len(ls) * 39
    h.append(f'<div class="rule" style="left:{SX}px;top:{bot + 8}px;width:{SW}px" data-a="wipe" data-t="{max(0.25, t - 0.4):.2f}"></div>')
    return bot + 10


def text_block(h, cls, text, font, y, t, px_max, px_min, max_lines, lh, x=SX, w=SW, center=False, color=None, a="rise",
               box_h=None, extra=""):
    """Paragraphe ajusté à sa boîte ; renvoie (bas, px)."""
    px, ls = mesure.ajuster(text, font, w, px_max, px_min, max_lignes=max_lines, interligne=lh, boite_h=box_h)
    hgt = len(ls) * px * lh
    al = "text-align:center;" if center else ""
    col = f"color:{color};" if color else ""
    h.append(f'<div class="{cls}" style="left:{x}px;top:{y:.0f}px;width:{w}px;{al}{col}font-size:{px}px;line-height:{lh}" '
             f'data-fit="1" data-fh="{hgt + 4:.0f}" data-fmin="{max(20, px_min - 6)}" data-a="{a}" data-t="{t:.2f}" {extra}>{_esc(text)}</div>')
    return y + hgt, px


def footnote(h, text, t, y_max, center=False):
    """Note mono en bas de l'accroche ; renvoie le haut de la note (la figure s'arrête au-dessus)."""
    if not text:
        return y_max
    ls = mesure.lignes_segments(text, "mono500", 26, SW, approche=0.07)
    if len(ls) > 2:
        ls = [ls[0], " ".join(ls[1:])]
    top = y_max - len(ls) * 39
    al = "text-align:center;" if center else ""
    h.append(f'<div class="mono" style="left:{SX}px;top:{top:.0f}px;width:{SW}px;{al}color:var(--ink-dim);font-size:26px" '
             f'data-fit="1" data-fh="{len(ls) * 39 + 2}" data-fmin="22" data-a="rise" data-t="{t:.2f}">' + "<br>".join(_esc(l) for l in ls) + '</div>')
    return top


def big_number(h, number, unit, x, w, y, t, px_max, px_min, color="var(--ink)", center=False, count=None):
    """Le chiffre en Bodoni à la plus grande taille qui tient dans w ; une unité courte (« % », « mm ») le suit en petit,
    une unité en mots (« études », « personnes ») passe dessous en italique. Renvoie le bas."""
    unit = unit or ""
    inline = unit.strip() in UNITES_COURTES or len(unit.strip()) <= 2
    px = px_max
    while px > px_min:
        wid = mesure.largeur(number, "bodoni400", px, -0.035) + (mesure.largeur(unit, "bodoni400", px * 0.42) + 0.06 * px if inline and unit else 0)
        if wid <= w - 6:
            break
        px -= 4
    al = "text-align:center;" if center else ""
    u = f'<span class="unit">{_esc(unit)}</span>' if inline and unit else ""
    inner = _esc(number)
    if count:   # le chiffre roule jusqu'à sa valeur (chiffres tabulaires)
        inner = (f'<span data-fx="count" data-t="{t + 0.05:.2f}" data-d="0.9" data-to="{count[0]}" data-dec="{count[1]}" '
                 f'data-pre="">{_esc(number)}</span>')
    h.append(f'<div class="num hnum" style="left:{x}px;top:{y:.0f}px;width:{w}px;{al}font-size:{px}px;color:{color}" data-fit="1" '
             f'data-fmin="{px_min - 20}" data-a="big" data-t="{t + 0.02:.2f}" data-d="1.0">{inner}{u}</div>')
    bot = y + px * 0.92
    if unit and not inline:
        upx, uls = mesure.ajuster(unit, "bodoni400i", w, 66, 40, max_lignes=1)
        h.append(f'<div class="hunit" style="left:{x}px;top:{bot + 6:.0f}px;width:{w}px;{al}font-size:{upx}px" data-fit="1" '
                 f'data-fmin="34" data-a="rise" data-t="{t + 0.35:.2f}">{_esc(unit)}</div>')
        bot += 6 + upx * 1.12
    return bot


# --------------------------------------------------------------------------------------------- figures qui disent le chiffre
def visual_kind(st):
    v = st.get("visual")
    if v in VISUALS:
        return v
    unit = (st.get("unit") or "").strip().lower()
    n = num_of(st.get("number"))
    cap = (st.get("caption") or "").lower()
    # ce que l'on compte : l'unité, sinon le premier mot de la légende (« 37 467 | adultes ont passé… »)
    nom = unit or (cap.split() or [""])[0]
    if st.get("ratio"):
        return "people"
    if unit == "%" and n is not None and 1 <= n <= 99:
        return "grid"
    if n is not None and float(n).is_integer() and nom.startswith(("étude", "essai", "article", "publication", "travau")):
        return "sheets"
    if n is not None and float(n).is_integer() and 2 <= n <= 24 and any(nom.startswith(p) for p in PERSONNES):
        return "people"
    return "icon"


def visual(h, st, kind, top, bot, t, lit_at, center, x0=None):
    """Dessine la figure dans la boîte [top, bot] de la feuille (de x0, ou de toute la largeur, au bord droit)."""
    global SX, SW
    if x0 is not None:     # boîte étroite à droite du chiffre
        sx, sw = SX, SW
        SX, SW = x0, SX + SW - x0
        try:
            return visual(h, st, kind, top, bot, t, lit_at, False)
        finally:
            SX, SW = sx, sw
    avail = bot - top
    if avail < 120 or kind == "none":
        return
    n = num_of(st.get("number"))
    if kind == "grid":
        k = int(round(n))
        lab = 50 if st.get("grid_label", True) else 0
        cols, rows = (10, 10) if avail - lab >= 330 else (20, 5)
        cell = min(SW / cols, (avail - lab) / rows)
        gw, gh = cell * cols, cell * rows
        x0 = SX + (SW - gw) / 2 if center else SX
        y0 = top + (avail - lab - gh) / 2
        r = cell * 0.34
        dots = []
        for i in range(cols * rows):
            cx, cy = x0 + (i % cols + 0.5) * cell, y0 + (i // cols + 0.5) * cell
            on = ' class="on"' if i < k else ""
            dots.append(f'<circle cx="{cx - x0:.1f}" cy="{cy - y0:.1f}" r="{r:.1f}"{on} data-i="{i % cols + i // cols}"/>')
        h.append(f'<svg class="lay hgrid" style="left:{x0:.0f}px;top:{y0:.0f}px;width:{gw:.0f}px;height:{gh:.0f}px" viewBox="0 0 {gw:.0f} {gh:.0f}" '
                 f'data-fx="grid" data-t="{t:.2f}" data-lit="{lit_at:.2f}" data-n="{cols + rows - 2}">{"".join(dots)}</svg>')
        h.append(f'<div class="mono" style="left:{x0:.0f}px;top:{y0 + gh + 8:.0f}px;width:{gw:.0f}px;{"text-align:center;" if center else ""}'
                 f'color:var(--carbon-deep);font-size:26px" data-a="rise" data-t="{lit_at + 0.3:.2f}">{_esc(st.get("grid_text") or "Chaque point = 1 sur 100")}</div>'
                 if lab else "")
        return
    if kind == "sheets":
        total = int(n)
        rnd = random.Random(total)
        if total <= 48:
            # le quadrillage qui donne les plus grandes feuilles dans la boîte
            cols = max(range(3, 13), key=lambda c: min(SW / c, avail / (math.ceil(total / c) * 1.25)))
            rows = math.ceil(total / cols)
            cw = min(SW / cols, (avail / rows) / 1.25, 120)
            sw, sh = cw * 0.78, cw * 0.98
            gw = cols * cw
            x0 = SX + (SW - gw) / 2 if center else SX
            y0 = top + (avail - rows * cw * 1.25) / 2
            for i in range(total):
                x, y = x0 + (i % cols) * cw + (cw - sw) / 2, y0 + (i // cols) * cw * 1.25
                rot = rnd.uniform(-5, 5)
                acc = " acc" if i == total - 1 else ""
                h.append(f'<div class="msheet{acc}" style="left:{x:.0f}px;top:{y:.0f}px;width:{sw:.0f}px;height:{sh:.0f}px" data-a="deal" '
                         f'data-rot="{rot:.1f}" data-t="{t + 0.25 + i * min(0.06, 1.6 / total):.2f}">'
                         + "".join(f'<i style="top:{14 + j * 16}%;width:{[72, 60, 66, 46][j % 4]}%"></i>' for j in range(4)) + '</div>')
        else:   # beaucoup d'études : une pile qu'on ne compte pas, qui grandit
            n_f = 16
            sh = min(380, avail * 0.82)
            sw = sh * 0.78
            cx = SX + SW / 2 if center or SW < 400 else SX + 40 + sw / 2
            for i in range(n_f):
                x = cx - sw / 2 + rnd.uniform(-26, 26)
                y = top + avail - sh - i * min(9, (avail - sh) / n_f) + rnd.uniform(-6, 6)
                acc = " acc" if i == n_f - 1 else ""
                h.append(f'<div class="msheet{acc}" style="left:{x:.0f}px;top:{y:.0f}px;width:{sw:.0f}px;height:{sh:.0f}px" data-a="deal" '
                         f'data-rot="{rnd.uniform(-7, 7):.1f}" data-t="{t + 0.25 + i * 0.09:.2f}">'
                         + "".join(f'<i style="top:{10 + j * 9}%;width:{[70, 58, 64, 44, 62, 50, 66, 40][j % 8]}%"></i>' for j in range(8)) + '</div>')
        return
    if kind == "people":
        if st.get("ratio"):
            k, tot = int(st["ratio"]["k"]), int(st["ratio"]["n"])
        else:
            k, tot = 0, int(n)
        tot = max(1, min(tot, 30))
        per_row = tot if tot <= 10 else math.ceil(tot / 2)
        rows = math.ceil(tot / per_row)
        hgt = min(190, (avail - 20) / rows / 1.08)
        wid = hgt * 0.4
        gap = min(wid * 0.9, (SW - per_row * wid) / max(1, per_row - 1))
        rw = per_row * wid + (per_row - 1) * gap
        x0 = SX + (SW - rw) / 2 if center else SX
        y0 = top + (avail - rows * hgt * 1.08) / 2
        lit = set(range(k)) if k else set()
        if k and st["ratio"].get("lit") == "fin":
            lit = set(range(tot - k, tot))
        for i in range(tot):
            x, y = x0 + (i % per_row) * (wid + gap), y0 + (i // per_row) * hgt * 1.08
            h.append(B.person_svg(x, y, hgt, "var(--ink-faint2)", f'data-a="up" data-t="{t + 0.3 + i * 0.05:.2f}"'
                                  + (f' data-o="{lit_at:.2f}"' if i in lit else "")))
            if i in lit:
                h.append(B.person_svg(x, y, hgt, "var(--carbon)", f'data-a="fade" data-t="{lit_at:.2f}"', cls="pers lit"))
        return
    # grand dessin au trait : l'objet de l'étude (icône de la série ou image redessinée)
    nom = ((st.get("unit") or "").strip() or ((st.get("caption") or "").split() or [""])[0]).lower()
    name = st.get("icon") or ("users" if any(nom.startswith(p) for p in PERSONNES) else "doc")
    s = min(avail, 330, SW)
    x = SX + (SW - s) / 2 if center or SW < 400 else SX + SW - s - 10
    if name in B.IMG:
        h.append(f'<svg class="lay" style="left:{x:.0f}px;top:{top + (avail - s) / 2:.0f}px;width:{s:.0f}px;height:{s:.0f}px" viewBox="0 0 360 360" '
                 f'data-a="draw" data-t="{t + 0.3:.2f}" data-d="1.3" data-stg="0.05">{B.image_svg(name)}</svg>')
    else:
        h.append(f'<div class="ico" style="left:{x:.0f}px;top:{top + (avail - s) / 2:.0f}px;width:{s:.0f}px;height:{s:.0f}px;color:var(--ink)" '
                 f'data-a="draw" data-t="{t + 0.3:.2f}" data-d="1.4" data-stg="0.1">{B.icon(name, sw=2.2)}</div>')
        h.append(f'<div class="hglow" style="left:{x + s * 0.2:.0f}px;top:{top + (avail - s) / 2 + s * 0.2:.0f}px;width:{s * 0.6:.0f}px;height:{s * 0.6:.0f}px" '
                 f'data-a="fade" data-t="{lit_at:.2f}"></div>')


# --------------------------------------------------------------------------------------------- les cinq accroches
def hook_station(st, film, edition):
    t = st["type"]
    y0 = st["y"]
    ta = st["cam_at"]
    center = edition.get("align") == "center" and t in ("hook_number", "hook_question", "hook_image")
    h = []
    y = header(h, st.get("header", ""), y0 + 52, ta, center)
    if t == "hook_number":
        cap_t = st.get("caption_at", ta + 2.3)
        lit_at = st.get("lit_at", cap_t + 0.6)
        n = num_of(st["number"])
        cnt = None
        if n is not None and st.get("roll", True) and len(str(st["number"])) <= 6:
            dec = len(str(st["number"]).split(",")[1]) if "," in str(st["number"]) else 0
            cnt = (n, dec)
        kind = visual_kind(st)
        unit = st.get("unit", "") or ""
        fb = footnote(h, st.get("footnote"), cap_t + 0.6, y0 + HOOK_H - 40, center)
        g = []      # le groupe chiffre + légende + figure, recentré verticalement à la fin
        top = y + 34
        # chiffre court (« 185 », « 7 mm ») : la figure se met à côté du chiffre, pas dessous
        inline = unit.strip() in UNITES_COURTES or len(unit.strip()) <= 2
        numw = mesure.largeur(str(st["number"]), "bodoni400", 215, -0.035) + (mesure.largeur(unit, "bodoni400", 215 * 0.42) + 13 if inline and unit else 0)
        side = (kind == "icon" or (kind == "sheets" and (num_of(st["number"]) or 0) > 48)) and numw <= 380 and not center
        if side:
            nb = big_number(g, str(st["number"]), unit, SX, int(numw) + 30, top, ta, 215, 110, count=cnt)
            visual(g, st, kind, top - 10, max(nb, top + 250) + 10, ta, lit_at, False, x0=SX + int(numw) + 60)
            nb = max(nb, top + 250)
            yb, _ = text_block(g, "cap", st.get("caption", ""), "schib400", nb + 30, cap_t, 36, 28, 3, 1.3)
        else:
            nb = big_number(g, str(st["number"]), unit, SX, SW, top, ta, 250 if kind == "none" else 215, 110, center=center, count=cnt)
            yb, _ = text_block(g, "cap", st.get("caption", ""), "schib400", nb + 26, cap_t, 36, 28, 3, 1.3, center=center)
            if kind != "none":
                visual(g, st, kind, yb + 40, fb - 34, ta, lit_at, center)
                yb = fb - 34
        off = max(0, min(140, (fb - 40 - yb) * 0.45))
        h.append(f'<div class="hwrap" style="left:0;top:{off:.0f}px;width:780px;height:1px">' + "\n".join(g) + '</div>')
    elif t == "hook_question":
        k = st["_sentence"]
        sent = film["sentences"][k]
        toks = sent["text"].split()
        ws = sent["_ws"]
        it = B.norm(st.get("italic") or "")
        fb = footnote(h, st.get("footnote"), ws[-1]["e"] + 0.2, y0 + HOOK_H - 40, center)
        box_top = y + 50
        icon_s = 150 if st.get("icon") else 0
        box_h = fb - box_top - (icon_s + 50 if icon_s else 30)
        px, ls = mesure.ajuster(sent["text"], "bodoni400", SW, 104, 54, max_lignes=6, interligne=1.08, boite_h=box_h)
        lh = px * 1.08
        ty = box_top + max(0, (box_h - len(ls) * lh) / 2)
        wi = 0
        under = None
        for li, line in enumerate(ls):
            lw = mesure.largeur(line, "bodoni400", px, -0.02)
            lx = SX + (SW - lw) / 2 if center else SX
            spans, cx = [], lx
            for tok in line.split():
                tt = ws[min(wi, len(ws) - 1)]["s"] if B.norm(tok) else ws[min(wi, len(ws) - 1) - 1]["s"] + 0.05
                cls = " it" if it and B.norm(tok) == it else ""
                spans.append(f'<span class="tw{cls}" data-t="{tt:.2f}">{_esc(tok)}</span>')
                tw = mesure.largeur(tok, "bodoni400i" if cls else "bodoni400", px, -0.02)
                if cls and under is None:
                    under = (cx, ty + li * lh + px * 0.98, tw, tt)
                cx += tw + mesure.largeur(" ", "bodoni400", px)
                wi += 1
            h.append(f'<div class="hq" style="left:{SX}px;top:{ty + li * lh:.0f}px;width:{SW}px;font-size:{px}px;{"text-align:center;" if center else ""}" '
                     f'data-fit="1" data-fmin="{px - 14}">{" ".join(spans)}</div>')
        if under:
            ux, uy, uw, ut = under
            d = f"M4 10 C {uw * 0.3:.0f} 2, {uw * 0.6:.0f} 16, {uw + 8:.0f} 6"
            h.append(f'<svg class="lay" style="left:{ux - 4:.0f}px;top:{uy:.0f}px;width:{uw + 16:.0f}px;height:22px" viewBox="0 0 {uw + 16:.0f} 22" '
                     f'data-a="draw" data-t="{ut + 0.35:.2f}" data-d="0.55"><path d="{d}" stroke="var(--carbon)" stroke-width="7" fill="none" stroke-linecap="round"/></svg>')
        if icon_s:
            ix = SX + (SW - icon_s) / 2 if center else SX
            h.append(f'<div class="ico" style="left:{ix:.0f}px;top:{fb - 30 - icon_s:.0f}px;width:{icon_s}px;height:{icon_s}px;color:var(--ink)" '
                     f'data-a="draw" data-t="{ws[-1]["e"]:.2f}" data-d="1.1">{B.icon(st["icon"], sw=2.6)}</div>')
    elif t == "hook_image":
        title_t = st.get("title_at", ta + 1.2)
        lock_at = st.get("lock_at", title_t + 0.8)
        fb = footnote(h, st.get("footnote"), title_t + 0.6, y0 + HOOK_H - 40, center)
        tpx, tls = mesure.ajuster(st.get("title", ""), "bodoni400", SW, 58, 40, max_lignes=2, interligne=1.1)
        t_h = len(tls) * tpx * 1.1 if st.get("title") else 0
        img_top, img_bot = y + 36, fb - 34 - t_h - (24 if t_h else 0)
        s = min(img_bot - img_top, 520)
        ix = SX + (SW - s) / 2
        iy = img_top + (img_bot - img_top - s) / 2
        name = st.get("image", "xray")
        scan_at = st.get("scan_at", ta + 1.1)
        if name in B.IMG:
            im = B.IMG[name]
            spots = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r * 1.6:.1f}" fill="var(--carbon)" class="hspot"/>' for cx, cy, r in im["spots"])
            h.append(f'<svg class="lay" style="left:{ix:.0f}px;top:{iy:.0f}px;width:{s:.0f}px;height:{s:.0f}px" viewBox="0 0 360 360" '
                     f'data-a="draw" data-t="{ta + 0.25:.2f}" data-d="1.2" data-stg="0.04">{B.image_svg(name)}</svg>')
            h.append(f'<svg class="lay" style="left:{ix:.0f}px;top:{iy:.0f}px;width:{s:.0f}px;height:{s:.0f}px" viewBox="0 0 360 360" '
                     f'data-a="pop" data-t="{lock_at + 0.15:.2f}">{spots}</svg>')
            x0, y0b, x1, y1 = im["lock"]
            h.append(f'<svg class="lay" style="left:{ix:.0f}px;top:{iy:.0f}px;width:{s:.0f}px;height:{s:.0f}px" viewBox="0 0 360 360" '
                     f'data-a="lock" data-t="{lock_at:.2f}">{B.corners(x0 - 14, y0b - 14, x1 + 14, y1 + 14, L=24, sw=5)}</svg>')
        elif name == "ecg":
            gw, gh = SW, min(s, 300)
            gy = img_top + (img_bot - img_top - gh) / 2
            grid = "".join(f'<path d="M0 {k * gh / 6:.0f}H{gw}" stroke="rgba(22,23,28,.12)" stroke-width="1.5"/>' for k in range(7)) + \
                   "".join(f'<path d="M{k * gw / 12:.0f} 0V{gh}" stroke="rgba(22,23,28,.12)" stroke-width="1.5"/>' for k in range(13))
            h.append(f'<svg class="lay" style="left:{SX}px;top:{gy:.0f}px;width:{gw}px;height:{gh:.0f}px" viewBox="0 0 {gw} {gh:.0f}" data-a="fade" data-t="{ta + 0.2:.2f}">{grid}</svg>')
            h.append(f'<svg class="lay" style="left:{SX}px;top:{gy:.0f}px;width:{gw}px;height:{gh:.0f}px" viewBox="0 0 {gw} {gh:.0f}" data-a="draw" '
                     f'data-t="{ta + 0.3:.2f}" data-d="2.6" data-ease="none"><path d="{B.ecg_path(gw, gh, 4)}" stroke="var(--ink)" stroke-width="5"/></svg>')
            h.append(f'<div class="hglow" style="left:{SX + gw * 0.55:.0f}px;top:{gy - 20:.0f}px;width:{gh * 0.9:.0f}px;height:{gh * 0.9:.0f}px" data-a="fade" data-t="{lock_at:.2f}"></div>')
        else:
            h.append(f'<div class="ico" style="left:{ix:.0f}px;top:{iy:.0f}px;width:{s:.0f}px;height:{s:.0f}px;color:var(--ink)" data-a="draw" '
                     f'data-t="{ta + 0.25:.2f}" data-d="1.5" data-stg="0.1">{B.icon(name, sw=2)}</div>')
            h.append(f'<div class="hglow" style="left:{ix + s * 0.2:.0f}px;top:{iy + s * 0.2:.0f}px;width:{s * 0.6:.0f}px;height:{s * 0.6:.0f}px" data-a="fade" data-t="{lock_at:.2f}"></div>')
        if name != "ecg":
            h.append(f'<div class="bandclip" style="left:{ix:.0f}px;top:{iy:.0f}px;width:{s:.0f}px;height:{s:.0f}px">'
                     f'<div class="band h" data-fx="band" data-t="{scan_at:.2f}" data-d="1.1" data-y0="-40" data-y1="{s:.0f}"></div></div>')
        if st.get("title"):
            text_block(h, "htitle", st["title"], "bodoni400", fb - 34 - t_h, title_t, 58, 40, 2, 1.1, center=True)
    elif t == "hook_versus":
        L, R = st["left"], st["right"]
        cap_t = st.get("caption_at", R.get("at", ta + 2) + 0.8)
        fb = footnote(h, st.get("footnote"), cap_t + 0.6, y0 + HOOK_H - 40)
        g = []      # tout le face-à-face, recentré verticalement à la fin
        cw, gap = 290, 60
        xs = [SX, SX + cw + gap]
        lab_bot = y + 40
        for side, x in zip((L, R), xs):
            b, _ = text_block(g, "glab vlab", side.get("label", ""), "schib600", y + 40, min(side.get("at", ta + 0.4) - 0.1, ta + (0.35 if x == SX else 0.6)),
                              36, 28, 2, 1.15, x=x, w=cw, center=True)
            lab_bot = max(lab_bot, b)
        ny = lab_bot + 30
        bots = []
        for side, x, acc in ((L, xs[0], False), (R, xs[1], True)):
            at = side.get("at", ta + 0.6)
            if side.get("number") not in (None, ""):
                col = "var(--carbon-deep)" if acc else "var(--ink)"
                bots.append(big_number(g, str(side["number"]), side.get("unit", ""), x, cw, ny, at, 170, 80, color=col, center=True))
            else:
                g.append(f'<div class="num hnum" style="left:{x}px;top:{ny:.0f}px;width:{cw}px;text-align:center;font-size:190px;font-style:italic;color:var(--carbon-deep)" '
                         f'data-a="big" data-t="{at:.2f}" data-d="0.9">?</div>')
                bots.append(ny + 190 * 0.92)
            if side.get("note"):
                text_block(g, "mono vnote", side["note"], "mono500", bots[-1] + 14, at + 0.4, 26, 22, 2, 1.4, x=x, w=cw, center=True)
                bots[-1] += 14 + 2 * 36
        vb = max(bots)
        g.append(f'<div class="dash" style="left:{SX + cw + gap / 2 - 1:.0f}px;top:{y + 40:.0f}px;height:{vb - y - 30:.0f}px" data-a="grow" data-t="{ta + 0.3:.2f}"></div>')
        yb = vb
        if st.get("caption"):
            yb, _ = text_block(g, "cap", st["caption"], "schib400", vb + 40, cap_t, 36, 28, 3, 1.3, box_h=fb - vb - 70)
        off = max(0, min(150, (fb - 40 - yb) * 0.4))
        h.append(f'<div class="hwrap" style="left:0;top:{off:.0f}px;width:780px;height:1px">' + "\n".join(g) + '</div>')
    elif t == "hook_headline":
        mark_at = st.get("mark_at", ta + 1.6)
        fb = footnote(h, st.get("footnote"), mark_at + 0.5, y0 + HOOK_H - 40)
        text = st["headline"]
        mark = [B.norm(w) for w in (st.get("mark") or "").split()]
        cx0, cw = SX - 26, SW + 52
        box_top = y + 50
        box_h = fb - box_top - 60
        px, ls = mesure.ajuster(text, "bodoni400", cw - 80, 76, 44, max_lignes=6, interligne=1.12, boite_h=box_h - 150)
        lh = px * 1.12
        card_h = len(ls) * lh + 150
        cy = box_top + (box_h - card_h) / 2
        h.append(f'<div class="clipping" style="left:{cx0}px;top:{cy:.0f}px;width:{cw}px;height:{card_h:.0f}px" data-a="pop" data-t="{ta + 0.05:.2f}"></div>')
        h.append(f'<div class="tape" style="left:{cx0 + cw / 2 - 110:.0f}px;top:{cy - 24:.0f}px" data-a="fade" data-t="{ta + 0.35:.2f}"></div>')
        if st.get("journal"):
            h.append(f'<div class="kick acc" style="left:{cx0 + 40}px;top:{cy + 40:.0f}px;width:{cw - 80}px;white-space:nowrap" data-fit="1" data-fmin="20" '
                     f'data-a="rise" data-t="{ta + 0.3:.2f}">{_esc(st["journal"])}</div>')
        toks = text.split()
        # repère les mots surlignés : la première suite exacte de « mark » dans le titre
        dn = [B.norm(w) for w in toks]
        j0 = next((j for j in range(len(dn) - len(mark) + 1) if mark and dn[j:j + len(mark)] == mark), None)
        hl = set(range(j0, j0 + len(mark))) if j0 is not None else set()
        wi = 0
        for li, line in enumerate(ls):
            spans = []
            for tok in line.split():
                tt = ta + 0.45 + wi * 0.045
                if wi in hl:
                    d = mark_at + (wi - j0) * 0.12
                    spans.append(f'<span class="hlw tw" data-t="{tt:.2f}"><span class="hlb" data-a="growx" data-t="{d:.2f}"></span>{_esc(tok)}</span>')
                else:
                    spans.append(f'<span class="tw" data-t="{tt:.2f}">{_esc(tok)}</span>')
                wi += 1
            h.append(f'<div class="hline" style="left:{cx0 + 40}px;top:{cy + 100 + li * lh:.0f}px;width:{cw - 80}px;font-size:{px}px" data-fit="1" '
                     f'data-fmin="{px - 12}">{" ".join(spans)}</div>')
        h.append(f'<div class="hair" style="left:{cx0 + 40}px;top:{cy + card_h - 34:.0f}px;width:{cw - 80}px" data-a="wipe" data-t="{ta + 0.6:.2f}"></div>')
    return "\n".join(h)


# --------------------------------------------------------------------------------------------- moments muets en plus
def gag_station(st):
    t = st["type"]
    y0 = st["y"]
    ta = st["cam_at"]
    h = []
    if t == "gag_calendar":
        # une page de calendrier dont les jours se barrent un à un : le temps qui passe, sans un mot
        cw, ch = 460, 380
        x0, y = (780 - cw) / 2, y0 + 20
        h.append(f'<div class="calp" style="left:{x0:.0f}px;top:{y:.0f}px;width:{cw}px;height:{ch}px" data-a="pop" data-t="{ta + 0.15:.2f}"></div>')
        h.append(f'<div class="calh" style="left:{x0:.0f}px;top:{y:.0f}px;width:{cw}px;height:70px" data-a="fade" data-t="{ta + 0.3:.2f}"></div>')
        for k in (0.22, 0.78):
            h.append(f'<div class="calr" style="left:{x0 + cw * k - 8:.0f}px;top:{y - 22:.0f}px" data-a="pop" data-t="{ta + 0.35:.2f}"></div>')
        cell = (cw - 40) / 7
        crosses = []
        for i in range(35):
            cx, cy = 20 + (i % 7) * cell, 90 + (i // 7) * (ch - 110) / 5
            crosses.append(f'<path d="M{cx + 12:.0f} {cy + 10:.0f}L{cx + cell - 12:.0f} {cy + 46:.0f}M{cx + cell - 12:.0f} {cy + 10:.0f}L{cx + 12:.0f} {cy + 46:.0f}" '
                           f'stroke="var(--ink)" stroke-width="4" stroke-opacity=".75"/>')
        boxes = "".join(f'<rect x="{20 + (i % 7) * cell + 6:.0f}" y="{90 + (i // 7) * (ch - 110) / 5:.0f}" width="{cell - 12:.0f}" height="56" rx="6" '
                        f'fill="rgba(22,23,28,.05)"/>' for i in range(35))
        h.append(f'<svg class="lay" style="left:{x0:.0f}px;top:{y:.0f}px;width:{cw}px;height:{ch}px" viewBox="0 0 {cw} {ch}" data-a="fade" data-t="{ta + 0.35:.2f}">{boxes}</svg>')
        h.append(f'<svg class="lay" style="left:{x0:.0f}px;top:{y:.0f}px;width:{cw}px;height:{ch}px" viewBox="0 0 {cw} {ch}" data-a="draw" '
                 f'data-t="{ta + 0.6:.2f}" data-d="0.16" data-stg="0.06" data-ease="power1.out">{"".join(crosses)}</svg>')
        h.append(f'<div class="note" style="left:0;width:780px;text-align:center;top:{y0 + 430}px" data-a="rise" data-t="{ta + 1.0:.2f}" data-fit="1" data-fmin="34">{_esc(st["label"])}</div>')
    elif t == "gag_pile":
        # des dossiers qui s'empilent sur le bureau : la charge qui monte
        n = 11
        rnd = random.Random(7)
        base = y0 + 360
        h.append(f'<div class="rule" style="left:120px;top:{base + 4}px;width:540px" data-a="wipe" data-t="{ta + 0.1:.2f}"></div>')
        for i in range(n):
            w = 300 + rnd.uniform(-20, 20)
            x = 390 - w / 2 + rnd.uniform(-22, 22)
            y = base - 26 - i * 27
            h.append(f'<div class="folder" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px" data-a="deal" data-rot="{rnd.uniform(-4, 4):.1f}" '
                     f'data-t="{ta + 0.3 + i * 0.2:.2f}"></div>')
        h.append(f'<div class="note" style="left:0;width:780px;text-align:center;top:{y0 + 430}px" data-a="rise" data-t="{ta + 1.0:.2f}" data-fit="1" data-fmin="34">{_esc(st["label"])}</div>')
    return "\n".join(h)


# --------------------------------------------------------------------------------------------- la couverture (première image)
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def cover(film, edition, date, t_out):
    """La première image du film : une couverture plein cadre tirée de l'accroche (c'est elle que LinkedIn montre dans
    le fil avant la lecture). Immobile dès l'image 0, elle se soulève quand la voix commence et révèle la table.
    Rien n'y est inventé : chiffre, question, face-à-face ou titre viennent de l'accroche, déjà vérifiée."""
    h0 = film["night"]["stations"][0]
    t = h0["type"]
    W_, X, CWc = 1080, 90, 900
    g = []
    jour = f"{date.day} {MOIS[date.month - 1]} {date.year}" if date else ""
    g.append(f'<div class="cvk" style="left:{X}px;top:70px;width:{CWc}px">Papercraft.AI · l\'étude du jour</div>')
    g.append(f'<div class="cvk" style="left:{X}px;top:70px;width:{CWc}px;text-align:right">{_esc(jour)}</div>')
    g.append(f'<div class="cvrule" style="left:{X}px;top:118px;width:{CWc}px"></div>')
    top, bot = 190, 990
    blocs = []          # (hauteur, html à placer à y) : on centre l'ensemble entre top et bot
    if t == "hook_number":
        unit = h0.get("unit", "") or ""
        inline = unit.strip() in UNITES_COURTES or len(unit.strip()) <= 2
        px = 330
        while px > 140:
            wid = mesure.largeur(str(h0["number"]), "bodoni400", px, -0.035) + (mesure.largeur(unit, "bodoni400", px * 0.42) + 0.06 * px if inline and unit else 0)
            if wid <= CWc - 10:
                break
            px -= 6
        u = f'<span class="unit">{_esc(unit)}</span>' if inline and unit else ""
        blocs.append((px * 0.95, lambda y, px=px, u=u: f'<div class="cvnum" style="left:{X}px;top:{y:.0f}px;width:{CWc}px;font-size:{px}px" data-fit="1" data-fmin="120">{_esc(h0["number"])}{u}</div>'))
        if unit and not inline:
            upx, _ = mesure.ajuster(unit, "bodoni400i", CWc, 92, 50, max_lignes=1)
            blocs.append((upx * 1.15, lambda y, upx=upx: f'<div class="cvunit" style="left:{X}px;top:{y:.0f}px;width:{CWc}px;font-size:{upx}px" data-fit="1" data-fmin="44">{_esc(unit)}</div>'))
        cpx, cls = mesure.ajuster(h0.get("caption", ""), "schib600", CWc, 56, 36, max_lignes=3, interligne=1.2)
        blocs.append((24, lambda y: ""))
        blocs.append((len(cls) * cpx * 1.2, lambda y, cpx=cpx, n=len(cls): f'<div class="cvcap" style="left:{X}px;top:{y:.0f}px;width:{CWc}px;font-size:{cpx}px" data-fit="1" data-fh="{n * cpx * 1.2 + 6:.0f}" data-fmin="30">{_esc(h0.get("caption", ""))}</div>'))
    elif t in ("hook_question", "hook_image", "hook_headline"):
        if t == "hook_question":
            txt, mark = h0.get("text") or film["sentences"][0]["text"], (h0.get("italic") or "")
        elif t == "hook_image":
            txt, mark = h0.get("title", ""), ""
        else:
            txt, mark = h0.get("headline", ""), (h0.get("mark") or "")
        if t == "hook_image":   # le dessin de l'étude, au trait, au-dessus du titre
            name = h0.get("image", "xray")
            if name in B.IMG:
                art = (f'<svg class="lay" style="left:{W_ / 2 - 170:.0f}px;top:{{y:.0f}}px;width:340px;height:340px" viewBox="0 0 360 360">'
                       + B.image_svg(name) + '</svg>')
                blocs.append((380, lambda y, art=art: art.replace("{y:.0f}", f"{y:.0f}")))
            elif name == "ecg":
                d = B.ecg_path(CWc, 220, 4)
                blocs.append((280, lambda y, d=d: f'<svg class="lay" style="left:{X}px;top:{y:.0f}px;width:{CWc}px;height:220px" viewBox="0 0 {CWc} 220"><path d="{d}" stroke="var(--ink)" stroke-width="6" fill="none"/></svg>'))
            else:
                blocs.append((320, lambda y, name=name: f'<div class="ico" style="left:{W_ / 2 - 140:.0f}px;top:{y:.0f}px;width:280px;height:280px;color:var(--ink)">{B.icon(name, sw=2.2)}</div>'))
        room = bot - top - 40 - sum(b[0] for b in blocs)
        px, ls = mesure.ajuster(txt, "bodoni400", CWc, 124, 60, max_lignes=7, interligne=1.06, boite_h=room)
        mk = [B.norm(w) for w in mark.split()]
        toks = txt.split()
        dn = [B.norm(w) for w in toks]
        j0 = next((j for j in range(len(dn) - len(mk) + 1) if mk and dn[j:j + len(mk)] == mk), None)
        hl = set(range(j0, j0 + len(mk))) if j0 is not None else set()
        spans, wi = [], 0
        for line in ls:
            for tok in line.split():
                if wi in hl:
                    cls_ = "cvit" if t == "hook_question" else "cvhl"
                    spans.append(f'<span class="{cls_}">{_esc(tok)}</span>')
                else:
                    spans.append(_esc(tok))
                wi += 1
            spans.append("<br>")
        html = " ".join(spans[:-1]).replace(" <br> ", "<br>")
        blocs.append((len(ls) * px * 1.06, lambda y, px=px, html=html, n=len(ls): f'<div class="cvq" style="left:{X}px;top:{y:.0f}px;width:{CWc}px;font-size:{px}px" data-fit="1" data-fh="{n * px * 1.06 + 8:.0f}" data-fmin="50">{html}</div>'))
    elif t == "hook_versus":
        L, R = h0["left"], h0["right"]
        cw, gap = 420, 60
        lpx = 44
        blocs.append((lpx * 1.3, lambda y: "".join(f'<div class="cvlab" style="left:{X + k * (cw + gap)}px;top:{y:.0f}px;width:{cw}px" data-fit="1" data-fmin="28">{_esc(s.get("label", ""))}</div>' for k, s in enumerate((L, R)))))
        def nums(y):
            out = []
            for k, s in enumerate((L, R)):
                x = X + k * (cw + gap)
                if s.get("number") not in (None, ""):
                    u = s.get("unit", "") or ""
                    out.append(f'<div class="cvnum{" acc" if k else ""}" style="left:{x}px;top:{y:.0f}px;width:{cw}px;font-size:230px" data-fit="1" data-fmin="100">{_esc(s["number"])}<span class="unit">{_esc(u)}</span></div>')
                else:
                    out.append(f'<div class="cvnum acc" style="left:{x}px;top:{y:.0f}px;width:{cw}px;font-size:250px;font-style:italic">?</div>')
            out.append(f'<div class="cvsep" style="left:{X + cw + gap / 2 - 2:.0f}px;top:{y - 70:.0f}px;height:330px"></div>')
            return "".join(out)
        blocs.append((240, nums))
        if h0.get("caption"):
            cpx, cls = mesure.ajuster(h0["caption"], "schib600", CWc, 50, 34, max_lignes=3, interligne=1.2)
            blocs.append((40, lambda y: ""))
            blocs.append((len(cls) * cpx * 1.2, lambda y, cpx=cpx, n=len(cls): f'<div class="cvcap" style="left:{X}px;top:{y:.0f}px;width:{CWc}px;font-size:{cpx}px" data-fit="1" data-fh="{n * cpx * 1.2 + 6:.0f}" data-fmin="30">{_esc(h0["caption"])}</div>'))
    tot = sum(b[0] for b in blocs)
    y = top + max(0, (bot - top - tot) / 2)
    for hgt, fn in blocs:
        g.append(fn(y))
        y += hgt
    if h0.get("header"):
        g.append(f'<div class="cvrule" style="left:{X}px;top:1040px;width:{CWc}px"></div>')
        g.append(f'<div class="cvk" style="left:{X}px;top:1062px;width:{CWc}px;white-space:nowrap" data-fit="1" data-fmin="20">{_esc(h0["header"])}</div>')
    glyph = ('<svg class="cvglyph" viewBox="0 0 20 26" style="left:{x}px;top:1110px;width:44px;height:57px"><path d="M1.5 1.5H13L18.5 7V24.5H1.5Z"/>'
             '<path d="M13 1.5V7H18.5"/><path class="g3" d="M1.5 24.5L18.5 7"/></svg>').format(x=X + CWc - 44)
    g.append(glyph)
    return (f'<div id="cover" class="clip" data-start="0" data-duration="{t_out + 0.9:.2f}" data-track-index="7">'
            f'<div id="coverin"><div class="cvbg"></div><div class="cvfold"></div>' + "\n".join(x for x in g if x) + '</div></div>')
