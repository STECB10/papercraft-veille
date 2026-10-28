# Papercraft.AI · une étude IA & santé par jour

Chaque matin, GitHub Actions :
1. cherche les études récentes (Europe PMC) — `pipeline/veille.py` ;
2. Claude choisit l'étude, écrit la fiche des faits, le script, l'animation et le post — skill `.claude/skills/etude-du-jour` ;
3. `pipeline/verifier.py` refuse tout chiffre absent de la source ;
4. `pipeline/fabriquer.py` fait la voix (ElevenLabs, Léo), l'animation (HyperFrames), la musique, le rendu et les contrôles ;
5. `pipeline/publication.py envoyer` envoie la vidéo sur Telegram avec Publier / Rejeter ;
6. toutes les 30 min, `publication.py ecouter` lit les clics et publie sur la page LinkedIn Papercraft.AI (Upload-Post).

## Le fonctionnement en schémas

*Vert : Claude. Orange : action humaine. Pointillés : secours.*

**Architecture.** Deux workflows GitHub Actions, un relais Cloudflare qui les lance à l'heure (le
planificateur de GitHub prend parfois des heures de retard), et cinq services externes. Une garde
empêche toute vidéo en double ; une alerte Telegram signale toute étape en échec.

![Architecture de Papercraft.AI](docs/architecture.svg)

**La chaîne de preuve.** Claude écrit, mais ne peut rien inventer : chaque chiffre de la vidéo vient
de `faits.json`, chaque fait cite `source.txt` mot pour mot, et `pipeline/verifier.py` refuse tout
écart. La voix est ensuite comparée à sa transcription, puis la vidéo passe ses propres contrôles
avant la validation humaine.

![Chaîne de preuve : du texte de l'étude à la validation humaine](docs/chaine-de-preuve.svg)

**Une journée, dans l'ordre.** Tout est automatique jusqu'à la vidéo sur Telegram ; rien n'est
publié sans le clic « Publier ».

![Déroulé d'une journée](docs/journee.svg)

Secrets (Settings → Secrets and variables → Actions) : `CLAUDE_CODE_OAUTH_TOKEN`, `ELEVENLABS_API_KEY`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `UPLOAD_POST_API_KEY`.
Variable facultative : `PUBLICATION_AUTO` = `oui` pour publier sans validation.

Règles de contenu : `serie/REGLES-CONTENU.md`. Format de l'animation : `serie/FILM-SCHEMA.md`.
Charte visuelle : `serie/frame.md` ; ses planches jouées en animation : `serie/reference/planches.html`.
Méthode et moteur dérivés de `motion-design-claude-code` (MIT, Colin Blain). Effets sonores : Pixabay Content License.
