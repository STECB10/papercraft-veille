# Papercraft.AI · une étude IA & santé par jour

Chaque matin, GitHub Actions :
1. cherche les études récentes (Europe PMC) — `pipeline/veille.py` ;
2. Claude choisit l'étude, écrit la fiche des faits, le script, l'animation et le post — skill `.claude/skills/etude-du-jour` ;
3. `pipeline/verifier.py` refuse tout chiffre absent de la source ;
4. `pipeline/fabriquer.py` fait la voix (ElevenLabs, Léo), l'animation (HyperFrames), la musique, le rendu et les contrôles ;
5. `pipeline/publication.py envoyer` envoie la vidéo sur Telegram avec Publier / Rejeter ;
6. toutes les 30 min, `publication.py ecouter` lit les clics et publie sur la page LinkedIn Papercraft.AI (Upload-Post).

Secrets (Settings → Secrets and variables → Actions) : `CLAUDE_CODE_OAUTH_TOKEN`, `ELEVENLABS_API_KEY`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `UPLOAD_POST_API_KEY`.
Variable facultative : `PUBLICATION_AUTO` = `oui` pour publier sans validation.

Règles de contenu : `serie/REGLES-CONTENU.md`. Format de l'animation : `serie/FILM-SCHEMA.md`.
Méthode et moteur dérivés de `motion-design-claude-code` (MIT, Colin Blain). Effets sonores : Pixabay Content License.
