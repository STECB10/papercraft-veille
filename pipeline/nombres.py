#!/usr/bin/env python3
"""Écrit en toutes lettres les nombres du texte dit, pour que la voix les lise comme un humain.

« 0,845 » -> « zéro virgule huit cent quarante-cinq » ; « 2 378 » -> « deux mille trois cent soixante-dix-huit » ;
« 36 % » -> « trente-six pour cent ». Le champ "display" (sous-titres) garde les chiffres : s'il est absent, il est
créé à partir du texte d'origine.

Usage : python3 pipeline/nombres.py       (réécrit jours/<date>/film.json)
"""
import re
import sys

UNITES = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize",
          "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
DIZAINES = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def moins_de_cent(n):
    if n < 20:
        return UNITES[n]
    d, u = divmod(n, 10)
    if d in (7, 9):
        base = "soixante" if d == 7 else "quatre-vingt"
        reste = 10 + u
        if d == 7 and u == 1:
            return "soixante et onze"
        return f"{base}-{UNITES[reste]}"
    if d == 8:
        return "quatre-vingts" if u == 0 else f"quatre-vingt-{UNITES[u]}"
    if u == 0:
        return DIZAINES[d]
    if u == 1:
        return f"{DIZAINES[d]} et un"
    return f"{DIZAINES[d]}-{UNITES[u]}"


def moins_de_mille(n, final=True):
    c, r = divmod(n, 100)
    if c == 0:
        return moins_de_cent(r)
    tete = "cent" if c == 1 else f"{UNITES[c]} cent" + ("s" if r == 0 and final else "")
    return tete if r == 0 else f"{tete} {moins_de_cent(r)}"


def entier(n):
    if n == 0:
        return "zéro"
    morceaux = []
    for valeur, nom in ((10**9, "milliard"), (10**6, "million")):
        q, n = divmod(n, valeur)
        if q:
            morceaux.append(f"{entier(q)} {nom}{'s' if q > 1 else ''}")
    q, n = divmod(n, 1000)
    if q:
        morceaux.append("mille" if q == 1 else f"{moins_de_mille(q, final=False)} mille")
    if n:
        morceaux.append(moins_de_mille(n))
    return " ".join(morceaux)


def en_lettres(txt):
    """Un nombre écrit en chiffres (« 2 378 », « 0,845 », « 12.5 ») -> lettres."""
    t = re.sub(r"[   ]", "", txt).replace(".", ",")
    if "," in t:
        e, d = t.split(",", 1)
        zeros = len(d) - len(d.lstrip("0"))
        dec = " ".join(["zéro"] * zeros + ([entier(int(d))] if d.strip("0") else []))
        return f"{entier(int(e or 0))} virgule {dec}"
    return entier(int(t))


NOMBRE = re.compile(r"(?<![\w,])(\d{1,3}(?:[   ]\d{3})+|\d+)(?:[,.](\d+))?(?![\w])")


def parler(texte):
    def rep(m):
        brut = m.group(1) + ("," + m.group(2) if m.group(2) else "")
        return en_lettres(brut)
    t = re.sub(r"(\d)\s*%", r"\1 pour cent", texte)
    t = re.sub(r"(\d)\s*€", r"\1 euros", t)
    t = NOMBRE.sub(rep, t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    from commun import dossier_du_jour, ecrire_json, lire_json
    jour = dossier_du_jour()
    film = lire_json(jour / "film.json")
    n = 0
    for s in film["sentences"]:
        if re.search(r"\d", s["text"]):
            s.setdefault("display", s["text"])
            s["text"] = parler(s["text"])
            n += 1
    ecrire_json(jour / "film.json", film)
    print(f"nombres : {n} phrase(s) réécrite(s) en toutes lettres")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        for x in ["0,845", "2 378 patients", "36 %", "18,2 %", "71", "80", "81", "91", "200", "201", "1 000", "2026", "0,05", "1 500 000", "21"]:
            print(f"{x!r:>18} -> {parler(x)}")
    else:
        main()
