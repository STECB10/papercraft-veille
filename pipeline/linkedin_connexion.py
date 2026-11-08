#!/usr/bin/env python3
"""Connexion du bot à LinkedIn, à lancer sur le Mac (une fois, puis tous les 60 jours quand le bot le rappelle).

  python3 pipeline/linkedin_connexion.py

1. Demande l'identifiant et le secret de l'application LinkedIn (onglet « Auth » de l'application sur
   developer.linkedin.com) ; ils peuvent aussi venir des variables LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET.
2. Ouvre LinkedIn dans le navigateur : tu te connectes toi-même et tu acceptes (le script ne voit jamais ton mot de passe).
3. Récupère le jeton sur http://localhost:8765/callback (adresse à déclarer dans « Authorized redirect URLs »).
4. Range les secrets dans le dépôt GitHub avec `gh secret set` si l'outil gh est installé et connecté ;
   sinon, affiche les valeurs à coller dans GitHub > Settings > Secrets and variables > Actions.
Rien d'autre que la bibliothèque standard de Python.
"""
import getpass
import http.server
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

DEPOT = "STECB10/papercraft-veille"
PORT = 8765
REDIRECTION = f"http://localhost:{PORT}/callback"
PORTEES = "w_organization_social r_organization_social"


def main():
    cid = os.environ.get("LINKEDIN_CLIENT_ID") or input("Client ID de l'application LinkedIn : ").strip()
    sec = os.environ.get("LINKEDIN_CLIENT_SECRET") or getpass.getpass("Client Secret (invisible à la frappe) : ").strip()
    etat = secrets.token_urlsafe(16)
    recu = {}

    class Retour(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if not self.path.startswith("/callback"):
                self.send_response(404)
                self.end_headers()
                return
            recu.update({k: v[0] for k, v in q.items()})
            ok = "code" in recu and recu.get("state") == etat
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "C'est bon, tu peux fermer cet onglet et revenir au terminal." if ok else \
                f"Échec : {recu.get('error_description') or recu.get('error') or 'réponse inattendue'}"
            self.wfile.write(f"<p style='font:20px sans-serif;margin:40px'>{msg}</p>".encode())

        def log_message(self, *a):
            pass

    serveur = http.server.HTTPServer(("127.0.0.1", PORT), Retour)
    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": cid, "redirect_uri": REDIRECTION, "state": etat, "scope": PORTEES},
        quote_via=urllib.parse.quote)
    print("\nJ'ouvre LinkedIn dans ton navigateur. Connecte-toi et accepte l'accès à la page.")
    print(f"(Si rien ne s'ouvre, copie cette adresse dans le navigateur :\n{url}\n)")
    webbrowser.open(url)
    fin = time.time() + 300
    serveur.timeout = 5
    while "code" not in recu and "error" not in recu and time.time() < fin:
        serveur.handle_request()
    serveur.server_close()
    if recu.get("state") != etat or "code" not in recu:
        sys.exit(f"Connexion interrompue : {recu.get('error_description') or recu.get('error') or 'pas de réponse en 5 minutes'}")

    corps = urllib.parse.urlencode({"grant_type": "authorization_code", "code": recu["code"], "redirect_uri": REDIRECTION,
                                    "client_id": cid, "client_secret": sec}).encode()
    req = urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken", data=corps,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            js = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"LinkedIn refuse l'échange du code : {e.code} {e.read().decode(errors='replace')[:300]}")
    jours = int(js.get("expires_in", 0)) // 86400
    portees = js.get("scope", "")
    print(f"\nJeton reçu : valable {jours} jours. Droits accordés : {portees or '(non précisés)'}")
    if "w_organization_social" not in portees and portees:
        print("Attention : le droit w_organization_social (publier au nom de la page) manque. L'accès à la "
              "Community Management API est-il bien accordé à l'application ?")
    valeurs = {"LINKEDIN_ACCESS_TOKEN": js["access_token"], "LINKEDIN_CLIENT_ID": cid, "LINKEDIN_CLIENT_SECRET": sec}
    if js.get("refresh_token"):
        valeurs["LINKEDIN_REFRESH_TOKEN"] = js["refresh_token"]
        print(f"LinkedIn donne aussi un jeton de renouvellement ({int(js.get('refresh_token_expires_in', 0)) // 86400} jours) : "
              "le bot renouvellera seul son accès d'ici là.")

    if shutil.which("gh") and subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0:
        for nom, val in valeurs.items():
            subprocess.run(["gh", "secret", "set", nom, "-R", DEPOT, "--body", val], check=True, capture_output=True)
            print(f"secret {nom} enregistré dans {DEPOT}")
        print("\nTerminé : le bot publiera désormais directement sur LinkedIn.")
    else:
        print(f"\nL'outil gh n'est pas disponible : colle ces valeurs dans GitHub > {DEPOT} > Settings > "
              "Secrets and variables > Actions > New repository secret (un secret par ligne) :\n")
        for nom, val in valeurs.items():
            print(f"{nom}\n{val}\n")


if __name__ == "__main__":
    main()
