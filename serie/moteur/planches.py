"""Planches de l'étude ajoutées le 7 novembre 2026 (DA v3.1), pour varier la mise en scène des méthodes et résultats.

  flow_chart  le parcours des participants, en entonnoir : chaque étape est une carte dont la largeur suit l'effectif,
              les exclusions sortent sur le côté (comme le diagramme de flux d'un article)
  big_stat    LE résultat, en grand : le chiffre roule ; pour un pourcentage, un anneau se trace jusqu'à sa valeur, et
              l'anneau du groupe comparé se trace à l'intérieur
  timeline    la chronologie de l'étude : une ligne qui descend, une date par étape (inclusions, suivi, analyse…)
  findings    ce que l'étude a trouvé, concrètement (retour du 8 novembre 2026) : 2 à 4 constats de terrain, chacun avec
              son dessin, son titre court, une ligne d'explication et, s'il y a lieu, une flèche (plus / moins / pareil) ;
              detail_at : la ligne d'explication arrive à part, sur le mot qui la dit
  ratio       un rapport (de cotes, de risques, de hasards) : le chiffre en grand, puis son intervalle sur une échelle
              logarithmique, puis la ligne « 1 = aucune différence » ; trois gestes sur trois moments de la voix
              (retour du 8 novembre 2026 : un rapport de cotes de 0,59 dessiné en jauge se lisait « 59 % »)

Coordonnées d'écran (planche plein cadre 1080 × 1350, zone utile y 150 à 1060), décalées de y0.
"""
import math

import mesure

B = None            # le module build (injecté par build.py)
TYPES = ["flow_chart", "big_stat", "timeline", "findings", "ratio"]
ML, CW, W = 72, 936, 1080


def _esc(s):
    return B.esc(s)


def _num(v):
    try:
        return float(str(v).replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".").lstrip("+"))
    except ValueError:
        return None


def _dec(v):
    s = str(v)
    return len(s.split(",")[1]) if "," in s else 0


def counter(value, t, d=1.0):
    """Le chiffre roule de 0 à sa valeur (affichage français) ; texte figé s'il ne se lit pas comme un nombre."""
    n = _num(value)
    if n is None or len(str(value)) > 9:
        return _esc(value)
    pre = "+" if str(value).strip().startswith("+") else ""
    return (f'<span data-fx="count" data-t="{t:.2f}" data-d="{d}" data-to="{n}" data-dec="{_dec(value)}" data-pre="{pre}">'
            f'{_esc(value)}</span>')


def station(st, film, fig, y0, t0):
    t = st["type"]
    h = []
    if t == "flow_chart":
        stages = st["stages"]
        k = len(stages)
        h += B.kicker(y0, st.get("title", "Le parcours des participants"), t0 + 0.2, fig)
        top, bot = y0 + 170, y0 + 1040
        slot = (bot - top) / k
        ch = min(150, slot - 58)
        nums = [_num(s.get("num", s["n"])) or 0 for s in stages]
        n0 = max(nums) or 1
        excl = {int(e["after"]): e for e in st.get("excluded", [])}
        for i, sg in enumerate(stages):
            frac = max(0.46, min(1.0, (nums[i] / n0) ** 0.5)) if n0 else 1
            cw = CW * frac
            x = (W - cw) / 2
            y = top + i * slot
            acc = " acc" if sg.get("accent") or (i == k - 1 and not any(s.get("accent") for s in stages)) else ""
            h.append(f'<div class="fcard{acc}" style="left:{x:.0f}px;top:{y:.0f}px;width:{cw:.0f}px;height:{ch:.0f}px" data-a="hingeT" data-t="{sg["at"] - 0.1:.2f}"></div>')
            npx = min(76, ch * 0.5)
            h.append(f'<div class="fnum{acc}" style="left:{x:.0f}px;top:{y + ch * 0.12:.0f}px;width:{cw:.0f}px;font-size:{npx:.0f}px" data-fit="1" data-fmin="40" '
                     f'data-a="print" data-t="{sg["at"]:.2f}">{counter(sg["n"], sg["at"], 0.8)}</div>')
            lpx, _ = mesure.ajuster(sg["label"], "schib600", cw - 60, 34, 26, max_lignes=1)
            h.append(f'<div class="flab{acc}" style="left:{x + 30:.0f}px;top:{y + ch * 0.12 + npx * 1.08:.0f}px;width:{cw - 60:.0f}px;font-size:{lpx}px" data-fit="1" '
                     f'data-fmin="22" data-a="rise" data-t="{sg["at"] + 0.15:.2f}">{_esc(sg["label"])}</div>')
            if i < k - 1:
                ay0, ay1 = y + ch + 8, y + slot - 8
                nt = stages[i + 1]["at"] - 0.35
                h.append(B.svg_layer(W / 2 - 20, ay0, 40, ay1 - ay0, f'<path d="M20 0V{ay1 - ay0 - 6:.0f}M8 {ay1 - ay0 - 18:.0f}L20 {ay1 - ay0 - 4:.0f}L32 {ay1 - ay0 - 18:.0f}" '
                                     f'stroke="var(--ink)" stroke-width="4"/>', "draw", nt, 'data-d="0.45"'))
                e = excl.get(i)
                if e:
                    ex = W / 2 + 26
                    ey = (ay0 + ay1) / 2
                    h.append(B.svg_layer(W / 2, ey - 2, 120, 4, '<path d="M0 2H118" stroke="var(--ink-dim)" stroke-width="3" stroke-dasharray="7 7"/>', "draw", e.get("at", nt) - 0.1))
                    h.append(f'<div class="fexcl" style="left:{ex + 104:.0f}px;top:{ey - 24:.0f}px;width:{W - ML - ex - 104:.0f}px" data-fit="1" data-fmin="20" '
                             f'data-a="rise" data-t="{e.get("at", nt):.2f}"><b>− {_esc(e["n"])}</b> {_esc(e["label"])}</div>')
    elif t == "big_stat":
        at = st["at"]
        unit = st.get("unit", "") or ""
        h += B.kicker(y0, st.get("title", "Le résultat"), t0 + 0.2)
        pct = unit.strip() == "%" and (_num(st.get("num", st["value"])) or -1) >= 0
        cmp_ = st.get("compare")
        if pct:
            R, cx, cy = 265, W / 2, y0 + 470
            v = min(100.0, _num(st.get("num", st["value"])) or 0)
            arc = _arc(cx - (R + 30), cy - (R + 30), R, v)
            h.append(f'<svg class="lay" style="left:{cx - R - 30:.0f}px;top:{cy - R - 30:.0f}px;width:{2 * R + 60}px;height:{2 * R + 60}px" viewBox="0 0 {2 * R + 60} {2 * R + 60}" '
                     f'data-a="fade" data-t="{t0 + 0.3:.2f}"><circle cx="{R + 30}" cy="{R + 30}" r="{R}" stroke="rgba(22,23,28,.10)" stroke-width="34" fill="none"/>'
                     + (f'<circle cx="{R + 30}" cy="{R + 30}" r="{R - 52}" stroke="rgba(22,23,28,.08)" stroke-width="18" fill="none"/>' if cmp_ else "") + '</svg>')
            h.append(f'<svg class="lay" style="left:{cx - R - 30:.0f}px;top:{cy - R - 30:.0f}px;width:{2 * R + 60}px;height:{2 * R + 60}px" viewBox="0 0 {2 * R + 60} {2 * R + 60}" '
                     f'data-a="draw" data-t="{at:.2f}" data-d="1.2" data-ease="power2.out"><path d="{arc}" stroke="var(--carbon)" stroke-width="34" fill="none" stroke-linecap="round"/></svg>')
            if cmp_ and _num(cmp_.get("num", cmp_.get("value"))) is not None:
                cv = min(100.0, _num(cmp_.get("num", cmp_.get("value"))))
                carc = _arc(cx - (R + 30), cy - (R + 30), R - 52, cv, off=R + 30)
                h.append(f'<svg class="lay" style="left:{cx - R - 30:.0f}px;top:{cy - R - 30:.0f}px;width:{2 * R + 60}px;height:{2 * R + 60}px" viewBox="0 0 {2 * R + 60} {2 * R + 60}" '
                         f'data-a="draw" data-t="{cmp_.get("at", at + 1.2):.2f}" data-d="1.0" data-ease="power2.out"><path d="{carc}" stroke="var(--ink-dim)" stroke-width="18" fill="none" stroke-linecap="round"/></svg>')
            inner = 2 * (R - 80) if cmp_ else 2 * (R - 50)
            num_w = mesure.largeur(str(st["value"]), "bodoni400", 200, -0.03) + mesure.largeur(unit, "bodoni400", 84)
            px = max(90, min(200, 200 * (inner - 20) / max(1, num_w)))
            h.append(f'<div class="bstat" style="left:{cx - inner / 2:.0f}px;top:{cy - px * 0.55:.0f}px;width:{inner:.0f}px;font-size:{px:.0f}px" data-fit="1" data-fmin="70" '
                     f'data-a="big" data-t="{at - 0.05:.2f}" data-d="0.6">{counter(st["value"], at, 1.2)}<span class="unit">{_esc(unit)}</span></div>')
            ly = cy + R + 64
        else:
            num_w = mesure.largeur(str(st["value"]), "bodoni400", 300, -0.03) + mesure.largeur(unit, "bodoni400", 126)
            px = max(120, min(300, 300 * (CW - 20) / max(1, num_w)))
            h.append(f'<div class="bstat" style="left:{ML}px;top:{y0 + 300:.0f}px;width:{CW}px;font-size:{px:.0f}px" data-fit="1" data-fmin="100" '
                     f'data-a="big" data-t="{at - 0.05:.2f}" data-d="0.7">{counter(st["value"], at, 1.1)}<span class="unit">{_esc(unit)}</span></div>')
            h.append(f'<div class="rule" style="left:{W / 2 - 90:.0f}px;top:{y0 + 300 + px * 1.02:.0f}px;width:180px;height:4px;background:var(--carbon)" data-a="growc" data-t="{at + 0.5:.2f}"></div>')
            ly = y0 + 300 + px * 1.02 + 50
        lpx, lls = mesure.ajuster(st["label"], "schib600", CW - 80, 46, 32, max_lignes=2, interligne=1.2)
        h.append(f'<div class="blab" style="left:{ML + 40}px;top:{ly:.0f}px;width:{CW - 80}px;font-size:{lpx}px" data-fit="1" data-fh="{2 * lpx * 1.2 + 6:.0f}" data-fmin="26" '
                 f'data-a="rise" data-t="{st.get("label_at", at + 0.4):.2f}">{_esc(st["label"])}</div>')
        if cmp_:
            cy2 = ly + len(lls) * lpx * 1.2 + 30
            h.append(f'<div class="bcmp" style="left:{ML}px;top:{cy2:.0f}px;width:{CW}px" data-fit="1" data-fmin="22" data-a="rise" data-t="{cmp_.get("at", at + 1.2):.2f}">'
                     f'contre <b>{_esc(cmp_.get("value", ""))}{_esc(cmp_.get("unit", unit))}</b> · {_esc(cmp_.get("label", ""))}</div>')
    elif t == "timeline":
        ev = st["events"]
        k = len(ev)
        h += B.kicker(y0, st.get("title", "Le calendrier de l'étude"), t0 + 0.2)
        top, bot = y0 + 210, y0 + 1000
        step = (bot - top) / max(1, k - 1) if k > 1 else 0
        lx = ML + 70
        h.append(f'<div class="tlrail" style="left:{lx - 2}px;top:{top:.0f}px;height:{bot - top:.0f}px" data-a="fade" data-t="{t0 + 0.3:.2f}"></div>')
        for i, e in enumerate(ev):
            y = top + i * step
            acc = " acc" if e.get("accent") or i == k - 1 else ""
            if i:
                h.append(f'<div class="tlfill" style="left:{lx - 3}px;top:{top + (i - 1) * step:.0f}px;height:{step:.0f}px" data-a="grow" data-t="{e["at"] - 0.45:.2f}"></div>')
            h.append(f'<div class="tldot{acc}" style="left:{lx - 19}px;top:{y - 19:.0f}px" data-a="pop" data-t="{e["at"] - 0.05:.2f}"></div>')
            wpx, _ = mesure.ajuster(str(e["when"]), "bodoni400", CW - 140, 72, 44, max_lignes=1)
            h.append(f'<div class="tlwhen{acc}" style="left:{lx + 60}px;top:{y - wpx * 0.62:.0f}px;width:{CW - 140}px;font-size:{wpx}px" data-fit="1" data-fmin="40" '
                     f'data-a="print" data-t="{e["at"]:.2f}">{_esc(e["when"])}</div>')
            lpx, lls = mesure.ajuster(e["label"], "schib500", CW - 140, 38, 28, max_lignes=2, interligne=1.2)
            h.append(f'<div class="tllab" style="left:{lx + 62}px;top:{y + wpx * 0.5:.0f}px;width:{CW - 140}px;font-size:{lpx}px" data-fit="1" data-fh="{2 * lpx * 1.2 + 6:.0f}" '
                     f'data-fmin="24" data-a="rise" data-t="{e["at"] + 0.15:.2f}">{_esc(e["label"])}</div>')
    elif t == "findings":
        items = st["items"]
        k = len(items)
        h += B.kicker(y0, st.get("title", "Ce qu'on a trouvé"), t0 + 0.2)
        top, bot = y0 + 165, y0 + 1045
        gap = 26
        ch = min(250, (bot - top - (k - 1) * gap) / k)
        y = top + (bot - top - (k * ch + (k - 1) * gap)) / 2
        for i, it in enumerate(items):
            at = it["at"]
            yy = y + i * (ch + gap)
            acc = " acc" if it.get("accent") else ""
            h.append(f'<div class="fdcard{acc}" style="left:{ML}px;top:{yy:.0f}px;width:{CW}px;height:{ch:.0f}px" data-a="slideL" data-t="{at - 0.15:.2f}"></div>')
            isz = min(110, ch - 60)
            h.append(B.iconbox(it.get("icon", "check"), ML + 34, yy + (ch - isz) / 2, isz, isz, "var(--ink)", at - 0.05, "draw", 'data-d="0.6"'))
            tx = ML + 34 + isz + 36
            arrow_w = 110 if it.get("tendance") else 0
            tw_ = CW - (tx - ML) - 34 - arrow_w
            lpx, lls = mesure.ajuster(it["label"], "schib600", tw_, 44, 32, max_lignes=1)
            dpx, dls = mesure.ajuster(it.get("detail", ""), "schib400", tw_, 33, 26, max_lignes=2, interligne=1.25)
            th = lpx * 1.15 + (len(dls) * dpx * 1.25 + 8 if it.get("detail") else 0)
            ty = yy + (ch - th) / 2
            h.append(f'<div class="fdlab" style="left:{tx:.0f}px;top:{ty:.0f}px;width:{tw_:.0f}px;font-size:{lpx}px" data-fit="1" data-fmin="26" '
                     f'data-a="rise" data-t="{at:.2f}">{_esc(it["label"])}</div>')
            dat = it.get("detail_at", at + 0.25)
            if it.get("detail"):
                h.append(f'<div class="fddet" style="left:{tx:.0f}px;top:{ty + lpx * 1.15 + 8:.0f}px;width:{tw_:.0f}px;font-size:{dpx}px" data-fit="1" '
                         f'data-fh="{len(dls) * dpx * 1.25 + 6:.0f}" data-fmin="22" data-a="rise" data-t="{dat:.2f}">{_esc(it["detail"])}</div>')
            tnd = it.get("tendance")
            if tnd:
                ax, ay = ML + CW - 34 - 80, yy + ch / 2 - 40
                d = {"plus": "M40 70V12M16 34L40 10L64 34", "moins": "M40 10V68M16 46L40 70L64 46", "pareil": "M10 30H70M10 50H70"}.get(tnd, "M10 40H70")
                h.append(B.svg_layer(ax, ay, 80, 80, f'<path d="{d}" stroke="var(--carbon)" stroke-width="8" fill="none"/>', "draw", max(at, dat) + 0.15, 'data-d="0.5"'))
    elif t == "ratio":
        h += ratio(st, y0, t0, fig)
    return h


def ratio(st, y0, t0, fig=None):
    """Un rapport et son intervalle. Champs : title, value (texte « 0,59 »), num, low, high, label (ce qu'on compare),
    left / right (ce que veut dire chaque côté de 1), at (le chiffre), ci_at (l'intervalle), null_at (la ligne à 1),
    caption + caption_at (la phrase qui conclut)."""
    h = []
    at = st["at"]
    ci_at = st.get("ci_at", at + 1.0)
    null_at = st.get("null_at", ci_at + 0.9)
    lo, hi, v, nul = float(st["low"]), float(st["high"]), float(st["num"]), float(st.get("null", 1))
    h += B.kicker(y0, st.get("title", "Le résultat"), t0 + 0.2, fig)
    # 1. le chiffre, en grand, et ce qu'il compare
    num_w = mesure.largeur(str(st["value"]), "bodoni400", 230, -0.03)
    px = max(120, min(230, 230 * (CW - 40) / max(1, num_w)))
    h.append(f'<div class="bstat" style="left:{ML}px;top:{y0 + 215:.0f}px;width:{CW}px;font-size:{px:.0f}px" data-fit="1" data-fmin="100" '
             f'data-a="big" data-t="{at - 0.05:.2f}" data-d="0.6">{counter(st["value"], at, 1.0)}</div>')
    ly = y0 + 215 + px * 1.02 + 18
    if st.get("label"):
        lpx, lls = mesure.ajuster(st["label"], "schib600", CW - 80, 40, 28, max_lignes=2, interligne=1.2)
        h.append(f'<div class="blab" style="left:{ML + 40}px;top:{ly:.0f}px;width:{CW - 80}px;font-size:{lpx}px" data-fit="1" data-fh="{2 * lpx * 1.2 + 6:.0f}" '
                 f'data-fmin="24" data-a="rise" data-t="{at + 0.3:.2f}">{_esc(st["label"])}</div>')
    # 2. l'intervalle, sur une échelle logarithmique (un rapport de 0,5 est aussi loin de 1 qu'un rapport de 2)
    x0, x1 = ML + 70, ML + CW - 70
    pos = all(x > 0 for x in (lo, hi, v, nul))
    f = math.log if pos else (lambda x: x)
    a, b = min(f(lo), f(nul)), max(f(hi), f(nul))
    pad = (b - a) * 0.18 or 0.3
    d0, d1 = a - pad, b + pad
    X = lambda x: x0 + (f(x) - d0) / (d1 - d0) * (x1 - x0)
    ay = y0 + 860
    h.append(f'<div class="tint" style="left:{x0 - 60:.0f}px;top:{ay - 240:.0f}px;width:{x1 - x0 + 120:.0f}px;height:390px" data-a="fade" data-t="{ci_at - 0.3:.2f}"></div>')
    h.append(f'<div class="kick" style="left:{x0:.0f}px;top:{ay - 216:.0f}px;width:{x1 - x0:.0f}px" data-a="rise" data-t="{ci_at - 0.2:.2f}">'
             f'{_esc(st.get("ci_label", "Intervalle de confiance à 95 %"))}</div>')
    h.append(B.svg_layer(x0 - 10, ay - 10, x1 - x0 + 20, 20, f'<path d="M10 10H{x1 - x0 + 10:.0f}" stroke="var(--ink)" stroke-opacity=".45" stroke-width="3"/>',
                         "draw", ci_at - 0.15, 'data-d="0.5"'))
    wl, wr, wy = X(lo), X(hi), ay - 60
    h.append(B.svg_layer(wl - 5, wy - 24, wr - wl + 10, 48, f'<path d="M5 24H{wr - wl + 5:.0f}M5 4V44M{wr - wl + 5:.0f} 4V44" stroke="var(--carbon-deep)" stroke-width="8"/>',
                         "growc", ci_at))
    pxp = X(v)
    h.append(f'<div class="cipt" style="left:{pxp - 18:.0f}px;top:{wy - 18:.0f}px;width:36px;height:36px" data-a="pop" data-t="{ci_at + 0.25:.2f}"></div>')
    dec = max(_dec(st["value"]), 2)
    for val, k in ((lo, 0), (hi, 1)):
        h.append(f'<div class="cival" style="left:{X(val) - 90:.0f}px;width:180px;top:{ay + 22:.0f}px;font-size:44px" data-a="rise" '
                 f'data-t="{ci_at + 0.35 + k * 0.1:.2f}">{B.fr(val, dec)}</div>')
    # 3. la ligne « aucune différence », et ce que veut dire chaque côté
    zx = X(nul)
    h.append(f'<div class="zero" style="left:{zx - 1.5:.0f}px;top:{ay - 150:.0f}px;height:172px" data-a="grow" data-t="{null_at:.2f}"></div>')
    txt = f"1 = {st.get('null_label', 'aucune différence')}"
    if zx > (x0 + x1) / 2:      # le texte du côté où il a la place, au-dessus de la moustache
        h.append(f'<div class="kick acc" style="right:{W - zx + 16:.0f}px;top:{ay - 156:.0f}px;text-align:right;white-space:nowrap" data-a="rise" data-t="{null_at + 0.15:.2f}">{_esc(txt)}</div>')
    else:
        h.append(f'<div class="kick acc" style="left:{zx + 16:.0f}px;top:{ay - 156:.0f}px;white-space:nowrap" data-a="rise" data-t="{null_at + 0.15:.2f}">{_esc(txt)}</div>')
    if st.get("left"):
        h.append(f'<div class="kick sm" style="left:{x0 - 30:.0f}px;width:{(x1 - x0) / 2:.0f}px;top:{ay + 96:.0f}px" data-fit="1" data-fmin="18" '
                 f'data-a="rise" data-t="{null_at + 0.35:.2f}">← {_esc(st["left"])}</div>')
    if st.get("right"):
        h.append(f'<div class="kick sm" style="left:{(x0 + x1) / 2 + 30:.0f}px;width:{(x1 - x0) / 2:.0f}px;top:{ay + 96:.0f}px;text-align:right" data-fit="1" data-fmin="18" '
                 f'data-a="rise" data-t="{null_at + 0.45:.2f}">{_esc(st["right"])} →</div>')
    if st.get("caption"):
        cpx, _ = mesure.ajuster(st["caption"], "schib600", CW - 80, 38, 26, max_lignes=1)
        h.append(f'<div class="blab" style="left:{ML + 40}px;top:{y0 + 1040:.0f}px;width:{CW - 80}px;font-size:{cpx}px;color:var(--carbon-deep)" data-fit="1" data-fmin="22" '
                 f'data-a="rise" data-t="{st.get("caption_at", null_at + 0.8):.2f}">{_esc(st["caption"])}</div>')
    return h


def _arc(x0, y0, r, pct, off=None):
    """Arc de cercle qui part d'en haut, dans le sens des aiguilles, jusqu'à pct % (coordonnées du SVG de l'anneau)."""
    c = off if off is not None else r + 30
    pct = max(0.5, min(99.9, pct))
    a = 2 * math.pi * pct / 100
    x1, y1 = c + r * math.sin(a), c - r * math.cos(a)
    large = 1 if pct > 50 else 0
    return f"M{c:.1f} {c - r:.1f}A{r} {r} 0 {large} 1 {x1:.1f} {y1:.1f}"
