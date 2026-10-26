# Relais Cloudflare

Le planificateur de GitHub Actions (`schedule`) part avec des heures de retard, voire pas du tout.
Ce petit programme tourne chaque minute chez Cloudflare (gratuit) et lance les workflows à la place :

- **6 h 15 (heure de Paris)** : lance « Vidéo du jour ». À **7 h 30**, la relance une fois si la vidéo n'existe pas encore.
- **Dès que tu cliques Publier / Rejeter** sur Telegram : lance « Écoute Telegram » (publication en 1 à 2 minutes).

Les horaires `schedule` des workflows restent en place comme filet de sécurité : la garde « Déjà fait aujourd'hui ? »
et l'historique empêchent tout doublon.

## Installation (une fois, 10 minutes)

1. **Jeton GitHub** : github.com → Settings → Developer settings → Personal access tokens → *Fine-grained tokens* →
   *Generate new token*. Repository access : *Only select repositories* → `papercraft-veille`.
   Permissions : **Actions : Read and write**, **Contents : Read-only**. Expiration : 1 an. Copie le jeton.
2. **Compte Cloudflare** gratuit sur dash.cloudflare.com.
3. Depuis ce dossier `relais/` sur ton ordinateur (Node.js installé) :

   ```sh
   npx wrangler login
   npx wrangler deploy
   npx wrangler secret put GH_TOKEN            # colle le jeton GitHub
   npx wrangler secret put TELEGRAM_BOT_TOKEN  # même valeur que le secret GitHub
   npx wrangler secret put TELEGRAM_CHAT_ID    # même valeur que le secret GitHub
   ```

4. Vérifier : Cloudflare → Workers → `papercraft-relais` → *Logs*. Une ligne apparaît à chaque lancement.

Pense à renouveler le jeton GitHub avant son expiration (`npx wrangler secret put GH_TOKEN`).
