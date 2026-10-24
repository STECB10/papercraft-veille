---
version: 1
name: "Papercraft.AI · Une étude par jour : frame de la série"
description: >
  Frame spec commun à toutes les vidéos quotidiennes de la page LinkedIn Papercraft.AI : une étude IA & santé expliquée
  en 45 à 60 s, en français, en 4:5. Direction retenue sur le pilote : « La feuille » (chaque étude est une feuille de
  papier, l'article lui-même) avec les « points-patients » pour chaque chiffre. Deux mondes : le CONSTAT se joue sur la
  feuille posée dans la nuit ; après le PIVOT (un pli qui balaie l'écran), L'ÉTUDE et ses résultats se jouent dans le
  monde papier ; la carte de fin revient à la nuit et replie la feuille en logo. Un seul accent, le carbone #5D68FF,
  réservé à la boîte du mot-clé de chaque sous-titre, aux 3 ou 4 traits de pic et au groupe « IA » des résultats.
  Chaque projet quotidien copie ce fichier en <projet>/frame.md et n'y ajoute que la géométrie de son monde.
unit: 1080×1350 (4:5), 30 i/s
principle: lisible sans le son · une seule chose à regarder à la fois · un accent, un mécanisme de surlignage · la voix déclenche chaque apparition · chaque chiffre vient de la fiche des faits

colors:
  canvas: "#0B0C10"          # nuit : monde du constat + carte de fin (le « night » du site)
  canvas-2: "#13141A"
  canvas-3: "#1B1D25"
  paper: "#ECE6DA"           # la feuille, et le sol plein cadre du monde de l'étude
  paper-2: "#DCD4C4"
  paper-3: "#C7BDA9"         # le coin plié, l'ombre du pli
  paper-hi: "#F7F3EC"        # texte dans la boîte d'accent
  paper-dim: "#9A958C"       # texte secondaire sur la nuit, points inactifs
  ink: "#16171C"             # encre sur papier
  ink-dim: "#57544E"         # encre secondaire, groupe témoin
  accent: "#5D68FF"          # LE carbone : boîte du mot-clé, traits de pic, groupe IA
  accent-soft: "#A3A9FF"     # carbone sur la nuit (petits éléments)
  accent-deep: "#3A44D6"     # carbone pour du texte sur papier
  hairline-dark: "rgba(236,230,218,.14)"
  hairline-light: "rgba(22,23,28,.16)"

# woff2 locaux uniquement (assets/fonts/), jamais d'@import réseau. Toutes SIL OFL (@fontsource).
fonts:
  Bodoni Moda: { files: ["assets/fonts/BodoniModa-400.woff2 (400)", "assets/fonts/BodoniModa-500.woff2 (500)", "assets/fonts/BodoniModa-400-italic.woff2 (400 italic)"] }
  Schibsted Grotesk: { files: ["assets/fonts/SchibstedGrotesk-400.woff2 (400)", "assets/fonts/SchibstedGrotesk-500.woff2 (500)", "assets/fonts/SchibstedGrotesk-600.woff2 (600)", "assets/fonts/SchibstedGrotesk-700.woff2 (700)"] }
  IBM Plex Mono: { files: ["assets/fonts/IBMPlexMono-400.woff2 (400)", "assets/fonts/IBMPlexMono-500.woff2 (500)"] }

layout:
  canvas: "1080 × 1350"
  side-margins: "64 px minimum, égales à gauche et à droite"
  title-safe: "rien d'important au-dessus de y 70"
  subtitle-band: "y 1108 à 1196 : le sous-titre seul, rien d'autre"
  bottom-safe: "y 1210 à 1350 : aucune information (l'interface LinkedIn mobile s'y superpose) ; seul le décor flou peut y passer"
  stage: "la scène utile est y 70 à 1090 : c'est là que la caméra cadre chaque sujet"

typography:
  subtitle:   { fontFamily: "Schibsted Grotesk", px: 54, weight: 600, lineHeight: 66, tracking: "-0.015em", note: "la phrase de la voix, centrée en BAS (bande y 1108 à 1196), 52 à 56 px, 32 caractères au plus par morceau (une phrase plus longue se découpe en morceaux qui se remplacent), mot à mot sur ses temps ; ombre légère ; papier sur la nuit, encre sur le papier. Jamais en haut à gauche." }
  type:       { fontFamily: "Bodoni Moda", px: 72, weight: 400, lineHeight: 1.08, tracking: "-0.03em", note: "SEULEMENT les 2 ou 3 moments typographiques du storyboard (le pivot, la nuance) : la phrase EST l'image, centrée, 72 px au plus, italique Bodoni pour le mot qui porte ; pas de sous-titre en bas pendant ce temps." }
  numeral:    { fontFamily: "Bodoni Moda", px: 260, weight: 400, lineHeight: 1, tracking: "-0.03em", note: "les chiffres clés (pourcentages, effectifs) ; le signe % à 0,5 em ; virgule décimale française ; chiffres tabulaires pendant le roulement." }
  numeral-mid: { fontFamily: "Bodoni Moda", px: 110, weight: 400, note: "chiffres au-dessus des barres ou des blocs de points" }
  label:      { fontFamily: "IBM Plex Mono", px: 17, weight: 400, tracking: "0.14em", upper: true, note: "étiquettes de figure, groupes, semaines (S+1), source" }
  body:       { fontFamily: "Schibsted Grotesk", px: 26, weight: 500, lineHeight: 1.35, note: "une ligne d'explication imprimée sur la feuille, rare" }
  italic-note: { fontFamily: "Bodoni Moda", px: 40, style: italic, note: "annotations à la main de la feuille : « plus tard », « des semaines après »" }

components:
  sheet:
    look: "feuille A4 (ratio 1:1,414) couleur paper, coin supérieur droit plié (triangle paper-3 de 64 px), pli diagonal du bas-gauche au haut-droit à peine visible (filet sombre 0,15 % + filet clair), ombre 0 60px 140px rgba(0,0,0,.6) sur la nuit. Elle est vue inclinée (rotateX 12 à 22°, rotateZ ±3 à 5°) : jamais de face et plate."
    content: "tout ce qui est imprimé dessus est à l'encre (ink, ink-dim) : en-tête mono (type d'étude · pays · années), figures au trait, chiffres Bodoni ; le carbone seulement pour ce que la voix désigne."
  fold (MÉCANISME SIGNATURE n° 1, transition d'acte):
    motion: "un reflet blanc (barre de 3 px floutée 1,5 px) glisse le long de la diagonale en 0,25 s, puis la moitié de la feuille se rabat (rotation 3D autour de la diagonale, 0,45 s expo.inOut) en emportant la caméra ; le flou de mouvement masque la couture. C'est le pivot de chaque film (nuit → papier) et la fin (papier → logo)."
    rule: "1 à 3 plis par film, jamais un pli « pour décorer »."
  patient-dots (MÉCANISME SIGNATURE n° 2, chaque chiffre):
    look: "un point = un patient ; grille régulière (pas de 22 à 38 px, rayon 7 à 9 px) ; inactifs ink à 20 % sur papier, paper à 28 % sur la nuit ; actifs ink (groupe témoin) ou accent (groupe IA)."
    motion: "les points arrivent en rafale (0,005 s d'écart), se partagent en deux au tirage au sort, s'allument un par un au rythme du chiffre qui roule, tombent (flou vertical) quand un patient décroche ; ils peuvent se regrouper en barre."
    rule: "le nombre de points et de points allumés est EXACTEMENT celui de la fiche des faits (85 sur 467, pas « environ »). Au-delà de 600 points, un point = 10 patients, et l'étiquette le dit."
  silhouettes:
    look: "personnage plat : tête ronde + corps en pilule (symbole #pers, viewBox 0 0 40 100), sans visage ; encre ou papier, une seule en accent quand la voix la désigne."
  line-icons:
    look: "icônes au trait (stroke 3 à 4 px, bouts ronds) : appareil photo, loupe, téléphone, porte, calendrier, fond d'œil… dessinées en SVG inline, une seule couleur ; jamais d'icône dans une pastille ronde, jamais d'emoji."
  key-word-box (LE mécanisme de surlignage, un par phrase):
    look: "petit rectangle accent, coins 3 px, qui déborde le mot de 0,14 em de chaque côté ; le mot passe en paper-hi dedans. Jamais une boîte noire."
    motion: "la boîte se trace depuis la gauche (scaleX 0 → 1, 0,16 s power3.out), 0 à 2 images avant que le mot soit dit."
    rule: "UNE boîte par phrase, sur le mot nommé [boîte : …] dans le storyboard."
  peak-stroke (les 3 ou 4 pics du film):
    look: "trait accent de 6 px, bouts ronds, légèrement montant (-1,2°), qui s'efface en fin de course, SOUS le mot-clé seulement."
    motion: "se trace depuis la gauche (0,3 à 0,5 s power2.out) pendant que le mot est dit."
  word-by-word:
    rule: "chaque mot du sous-titre apparaît SUR son temps, gris (35 %) : fromTo {opacity:0, y:6, blur 4px} → {opacity:1, y:0, blur 0} en 0,14 s, immediateRender:false, puis il passe à pleine couleur en 0,2 s. Avant une couture, le sous-titre sort : opacité 1 → 0 et flou 0 → 6 px en 0,14 s."
  counter:
    description: "chiffre Bodoni qui roule jusqu'à sa valeur (chiffres tabulaires, virgule française), ou qui fonce entier depuis la caméra (trop grand et flou, puis se pose). Jamais posé en fondu."
  bars:
    description: "barres de figure de revue : groupe témoin hachuré à l'encre (135°, 2 px / 12 px) avec contour ink-dim, groupe IA plein accent ; ligne de base ink 2 px ; étiquettes mono sous les barres ; les deux barres ont des marges égales."
  source-card:
    description: "carte imprimée sur la feuille : premier auteur et « et al. », revue en Bodoni italique, mois et année, DOI en mono 15 px, type d'étude (essai randomisé, étude observationnelle, préprint non relu)."
  end-card:
    description: "nuit ; la feuille se replie en glyphe Papercraft (le chemin M1.5 1.5H13L18.5 7V24.5H1.5Z + le coin + le pli en accent-soft, trait 1,5) ; « Papercraft.AI » en Bodoni ; la promesse « Une étude par jour, vérifiée à la source. » en type ; UN bouton « Suivre » (pilule paper, texte ink, Schibsted 600) ; le curseur arrive en un geste et clique ; 2 à 3 s de tenue vivante (dérive, grain) avant le noir."
  cursor:
    description: "flèche blanche à contour sombre et ombre ; elle arrive en UN mouvement courbe (0,4 à 0,5 s power3.out) et clique directement : pression (scale .85, 0,06 s) + anneau accent qui s'étend et s'efface. Jamais d'hésitation."
  ground-dark:
    background: "canvas plein + 1 halo accent doux (14 à 22 %, flou 110 px) derrière l'élément principal + grain 7 %. Couche class=\"clip\" sur toute la durée, jamais sur #root."
  ground-light:
    background: "paper plein + un halo accent très doux (8 à 10 %) + le pli diagonal à peine visible + le coin plié en haut à droite du cadre + grain 5 % en multiply. Texte en ink."

camera:
  rig: "#stage (1080×1350, overflow hidden, perspective 1600px) > #drift > #cam (échelle, rotation autour de 540 675) > #world (translation)"
  world: "la feuille est le monde : 1500 × 2120 px (ratio A4) dans la nuit ; les sujets y sont imprimés de HAUT en BAS, la caméra DESCEND la feuille (le format vertical s'y prête) ; après le pli, la caméra est DANS la feuille (papier plein cadre) et continue de descendre."
  drift: "dérive lente qui ne s'arrête jamais : 2 à 4 % d'échelle et 12 à 30 px par plan, alternée d'un plan à l'autre ; crans de 0,12 à 0,3 s (expo.inOut) vers le prochain sujet."
  depth: "trois niveaux : avant-plan flou (bord d'une autre feuille, points géants flous, silhouette floue), sujet net, fond flou (le reste de la feuille au-dessus)."

negative:
  - "Aucun chiffre, nom, date ou citation qui ne soit pas dans la fiche des faits du SCRIPT.md."
  - "Pas de « avant / après » pour comparer deux groupes tirés au sort : deux groupes côte à côte, marges égales."
  - "Pas de deuxième mécanisme de surlignage : la boîte du mot-clé est la SEULE façon de souligner un mot du sous-titre ; le trait marque les 3 ou 4 pics."
  - "Pas de grande phrase : sous-titre 52 à 56 px, moment typographique 72 px au plus ; pas de mot géant, pas de grosse boîte. Rien d'autre que le sous-titre dans la bande y 1108 à 1196 ; rien d'important sous y 1210."
  - "Une seule chose à regarder à la fois : la caméra isole le sujet de la phrase."
  - "Pas d'aller-retour de caméra ; pas d'hésitation du curseur."
  - "Pas de décor sans sens (barres grises « pour remplir », symboles abstraits, compteurs qui ne disent rien)."
  - "Pas d'autre teinte que l'accent ; pas de rouge « danger », pas de vert « succès »."
  - "Pas d'image médicale réelle, de logo d'hôpital, de figure copiée de l'article : tout est redessiné au trait."
  - "Pas d'Inter, Space Grotesk, Geist, system-ui. Pas d'emoji. Pas d'icône dans une pastille ronde."
  - "Pas d'easing élastique ou rebondissant ; pas de repeat:-1 ; pas de tween de letterSpacing."
---

# Papercraft.AI · Une étude par jour : frame de la série

**Le monde.** Chaque étude est une feuille de papier : l'article lui-même. Le film commence dans la nuit, sur la
feuille inclinée, imprimée à l'encre comme une figure de revue. La caméra descend la feuille, d'un sujet imprimé au
suivant (le terrain, le problème, le parcours actuel, le chiffre de départ). Au **pivot**, un reflet glisse le long de
la diagonale et la feuille se plie : on traverse le pli et l'on atterrit **dans** la feuille, papier plein cadre, où se
joue l'étude (la population en points, le tirage au sort, le résultat qui roule, la nuance). La **source** s'imprime en
bas de la feuille. À la **fin**, retour à la nuit : la feuille se replie en glyphe Papercraft, la promesse, le bouton
« Suivre ».

**La lecture.** Tout ce que l'on lit est en Schibsted Grotesk : la phrase de la voix en sous-titre centré en bas, mot
à mot, avec exactement un mot-clé par phrase dans une petite boîte carbone qui se trace d'abord. Un trait carbone sous
le mot-clé marque les 3 ou 4 pics. Les chiffres, les moments typographiques et les annotations « à la main » sont en
Bodoni Moda ; les étiquettes de figure, les groupes et la source en IBM Plex Mono.

**Les chiffres.** Chaque chiffre est montré deux fois : en Bodoni qui roule, et en points-patients qui s'allument.
Le nombre de points est exact. Le groupe témoin est à l'encre, le groupe IA en carbone : c'est la seule autre place
de l'accent.

**Images de référence** (pilote) : `pilote-tanzanie/styleframes/png/A1.png` (la feuille dans la nuit, le chiffre qui
arrive), `A2.png` (la caméra descend le parcours imprimé), `A3.png` (le monde papier, les barres), `C3.png` (les
points-patients comptés).

## Géométrie du monde (à remplir par chaque projet)

Chaque `<projet>/frame.md` ajoute ici les coordonnées de ses stations sur la feuille (x, y dans le monde de
1500 × 2120 px, la caméra cam(x, y, échelle) = point au centre du cadre) et, si le monde est complexe, un
`reference/feuille.html` exécutable que chaque plan copie à l'identique.
