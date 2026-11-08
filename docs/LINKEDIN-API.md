# Publier sur LinkedIn sans intermédiaire (API officielle, gratuite)

Le bot publie d'abord en direct sur la page Papercraft.AI par l'API de LinkedIn (`pipeline/linkedin.py`). Si l'accès
n'est pas configuré, a expiré ou échoue, il passe par Upload-Post (10 publications par mois en gratuit). À une vidéo
par jour, le niveau d'accès de départ de LinkedIn (« Development », 500 appels par jour) suffit largement : une
publication en coûte une dizaine.

## 1. Créer l'application (une fois, sur developer.linkedin.com)

1. **developer.linkedin.com > My apps > Create app**.
   - App name : par exemple « Papercraft veille » (jamais « LinkedIn » dans le nom ni le logo).
   - LinkedIn Page : la page **Papercraft.AI**.
   - Privacy policy URL : une page de politique de confidentialité en ligne (sur medicalagent.fr par exemple).
   - App logo : le logo Papercraft.
2. **Onglet Settings > Verify** : LinkedIn génère un lien de vérification. Un **super administrateur** de la page
   Papercraft.AI l'ouvre et valide. Sans ça, la demande d'accès est refusée.
3. **Onglet Products > Community Management API > Request access** : une application dédiée, sans autre produit. Le
   formulaire demande :
   - un **e-mail professionnel** vérifié (pas une adresse Gmail : LinkedIn refuse les adresses personnelles), par
     exemple une adresse @medicalagent.fr ;
   - la **raison sociale**, l'**adresse déclarée**, le **site** et la **politique de confidentialité** de la structure
     (la micro-entreprise Medical Agent : SIRET, adresse déclarée, medicalagent.fr) ;
   - le cas d'usage : publication automatique, après validation humaine, de vidéos de vulgarisation scientifique sur la
     page de l'entreprise.
   LinkedIn examine la demande (quelques jours en général). Refus = nouvelle application et nouvelle demande.
4. **Onglet Auth** :
   - noter le **Client ID** et le **Client Secret** ;
   - dans **Authorized redirect URLs for your app**, ajouter exactement `http://localhost:8765/callback`.

## 2. Connecter le bot (une fois, puis tous les 60 jours)

Sur le Mac, dans le dépôt :

```
cd ~/ma-video/papercraft-push && git pull && python3 pipeline/linkedin_connexion.py
```

Le script demande le Client ID et le Client Secret, ouvre LinkedIn dans le navigateur (tu te connectes toi-même et
tu acceptes), récupère le jeton et l'enregistre dans les secrets du dépôt avec `gh` s'il est installé. Sinon, il
affiche les quatre valeurs à coller dans GitHub > Settings > Secrets and variables > Actions :
`LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` (et `LINKEDIN_REFRESH_TOKEN` si LinkedIn en
donne un).

Le jeton vit 60 jours. Le bot prévient sur Telegram dix jours avant l'expiration : il suffit de relancer la même
commande. Si LinkedIn donne un jeton de renouvellement (réservé à certains partenaires), le bot renouvelle seul son
accès pendant un an.

## 3. Ce qui se passe à la publication

Clic sur « Publier » dans Telegram → `publication.py ecouter` → `linkedin.publier()` : envoi de la vidéo par
morceaux, attente du traitement, puis post au nom de la page (texte échappé au format « little text » de LinkedIn,
hashtags conservés). Le message de confirmation dit par où la vidéo est passée (« via LinkedIn » ou « via
Upload-Post »).
