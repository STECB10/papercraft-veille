#!/usr/bin/env python3
"""Mesure du texte avec les vraies chasses des polices de la série (serie/moteur/metriques.json, tirées des woff2).

Sert au moteur à placer les blocs les uns sous les autres et à choisir une taille qui tient dans sa boîte :
plus jamais un chiffre coupé par le bord de la feuille ni une légende qui déborde sur un dessin.
moteur.js refait une passe dans le navigateur (data-fit) au cas où une mesure serait un peu juste.

  largeur("37 467", "bodoni400", 280)                  -> largeur en px
  lignes("des adultes suivis…", "schib400", 34, 640)   -> liste des lignes (coupure aux espaces)
  ajuster(texte, police, boite_l, px_max, px_min, max_lignes=1, interligne=1.2, boite_h=None) -> (px, lignes)
"""
import json
import pathlib

_M = json.loads((pathlib.Path(__file__).resolve().parent / "metriques.json").read_text(encoding="utf-8"))
MAJ = {"mono400", "mono500"}      # le mono est toujours en capitales dans la série


def largeur(texte, police, px, approche=0.0, capitales=None):
    """Largeur d'une ligne en px. approche : letter-spacing en em (CSS l'ajoute après chaque caractère)."""
    m = _M[police]
    if capitales is None:
        capitales = police in MAJ
    t = texte.upper() if capitales else texte
    w = sum(m["w"].get(c, m["missing"]) for c in t)
    return (w + approche * len(t)) * px


def lignes(texte, police, px, boite_l, approche=0.0, capitales=None):
    mots = texte.split()
    out, cur = [], ""
    for mot in mots:
        essai = f"{cur} {mot}" if cur else mot
        if cur and largeur(essai, police, px, approche, capitales) > boite_l:
            out.append(cur)
            cur = mot
        else:
            cur = essai
    if cur:
        out.append(cur)
    return out or [""]


def ajuster(texte, police, boite_l, px_max, px_min, max_lignes=1, interligne=1.2, boite_h=None, approche=0.0, pas=2,
            capitales=None):
    """La plus grande taille (de px_max à px_min) où le texte tient en max_lignes dans boite_l (et boite_h).
    Aucun mot ne dépasse : un mot plus large que la boîte force une taille plus petite. Renvoie (px, lignes)."""
    px = px_max
    while True:
        ls = lignes(texte, police, px, boite_l, approche, capitales)
        trop_large = any(largeur(l, police, px, approche, capitales) > boite_l for l in ls)
        trop_haut = boite_h is not None and len(ls) * px * interligne > boite_h
        if (len(ls) <= max_lignes and not trop_large and not trop_haut) or px <= px_min:
            return px, ls
        px = max(px_min, px - pas)


def lignes_segments(texte, police, px, boite_l, approche=0.0, sep=" · "):
    """Comme lignes(), mais coupe de préférence entre les segments « A · B · C » (en-têtes, notes mono) :
    jamais un mot orphelin seul sur sa ligne quand un segment entier peut descendre."""
    segs = texte.split(sep)
    out, cur = [], ""
    for sg in segs:
        essai = f"{cur}{sep}{sg}" if cur else sg
        if largeur(essai, police, px, approche) <= boite_l:
            cur = essai
            continue
        if cur:
            out.append(cur)
        if largeur(sg, police, px, approche) <= boite_l:
            cur = sg
        else:
            parts = lignes(sg, police, px, boite_l, approche)
            out += parts[:-1]
            cur = parts[-1]
    if cur:
        out.append(cur)
    return out or [""]
