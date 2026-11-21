---
name: SIG chantier
description: Carte web des contraintes autour du CNPE de Penly, dessinée comme un plan cadastral à l'encre sépia sur papier.
colors:
  encre: "#2f241d"
  encre-2: "#5a4a3d"
  encre-3: "#6f5f51"
  papier: "#faf8f3"
  papier-2: "#f2eee5"
  papier-3: "#e9e3d6"
  filet: "#d8d1c4"
  carmin: "#c8385a"
  bleu: "#4f7fb0"
  vert: "#8fae74"
  vert-fonce: "#5d7d47"
  sepia: "#9a8470"
  bandeau-2: "#3b2e25"
  bandeau-filet: "#6b5848"
  bandeau-texte-2: "#d6cabb"
  mer-ortho: "#5f8584"
typography:
  chiffre-cle:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontFeature: "tnum"
  distance:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "tnum"
  headline:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "23px"
    fontWeight: 700
    lineHeight: 1.15
  title:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.2
  titre-bandeau:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 700
    letterSpacing: "0.005em"
  body:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  body-panneau:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
  legende:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.3
  label:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    letterSpacing: "0.08em"
  lieu:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 600
rounded:
  case: "2px"
  controle: "3px"
  max: "4px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  xxl: "24px"
components:
  bouton-bandeau:
    backgroundColor: "transparent"
    textColor: "{colors.papier}"
    rounded: "{rounded.controle}"
    padding: "0 12px"
    height: "34px"
  bouton-bandeau-hover:
    backgroundColor: "{colors.bandeau-2}"
    textColor: "{colors.papier}"
  bouton-bandeau-actif:
    backgroundColor: "{colors.papier}"
    textColor: "{colors.encre}"
    rounded: "{rounded.controle}"
  champ-recherche:
    backgroundColor: "{colors.bandeau-2}"
    textColor: "{colors.papier}"
    rounded: "{rounded.controle}"
    padding: "0 12px 0 36px"
    height: "34px"
  planche:
    backgroundColor: "{colors.papier}"
    textColor: "{colors.encre}"
    height: "30px"
  planche-hover:
    backgroundColor: "{colors.papier-3}"
  planche-active:
    backgroundColor: "{colors.encre}"
    textColor: "{colors.papier}"
  couche:
    backgroundColor: "transparent"
    textColor: "{colors.encre}"
    typography: "{typography.body-panneau}"
    padding: "4px 20px"
    height: "34px"
  couche-hover:
    backgroundColor: "{colors.papier-2}"
  bouton-papier:
    backgroundColor: "{colors.papier}"
    textColor: "{colors.encre}"
    rounded: "{rounded.controle}"
    padding: "0 12px"
    height: "30px"
  bouton-papier-hover:
    backgroundColor: "{colors.papier-3}"
  cadre-carte:
    backgroundColor: "{colors.papier}"
    textColor: "{colors.encre}"
    padding: "10px 12px"
---

# Design System: SIG chantier

## Overview

**Creative North Star: "Le plan cadastral"**

La carte se lit comme une planche de géomètre : encre sépia sur papier crème, cadres d'un seul filet, lavis transparents codés par réseau. Rien ne flotte, rien ne brille. Chaque élément d'interface est un cartouche posé sur la feuille : bandeau sépia en tête, panneau papier à gauche, encarts encadrés d'encre sur la carte. La densité est celle d'une légende de plan : des lignes de 34 px, des chiffres tabulaires, des comptes d'objets alignés à droite.

La donnée porte toute la couleur. Le fond IGN est désaturé et éclairci pour que le carmin, le bleu de Prusse et le vert pré ne désignent que des réseaux et des zonages. L'interface reste en encre et papier ; le carmin y revient seulement comme accent ponctuel (choix coché, survol de lien, écart, erreur). La sélection d'un objet se dessine à l'encre, jamais dans une teinte de donnée.

La signature du système est le tableau d'assemblage : un encart d'encre qui situe la vue courante et sert de navigateur entre planches fixes de 2, 5, 10 et 20 km. Le système refuse le visualiseur SIG par défaut : panneau blanc à cases génériques, boutons flottants bleus arrondis à ombre, galerie de fonds en vignettes.

**Key Characteristics:**
- Encre sépia sur papier, cadres de 1 px, angles vifs (4 px au plus).
- Aucune ombre portée ; la profondeur vient du filet d'encre et de l'ordre des couches.
- Lavis transparents codés : carmin pour le transport HTB, bleu de Prusse pour la distribution et l'eau, vert pré pour l'environnement.
- Une seule famille, Source Sans 3 : italique pour les lieux, chiffres tabulaires partout où l'on compte ou mesure.
- Pastilles de légende qui reproduisent exactement le symbole dessiné sur la carte.
- Nombres au format fr-FR, espace insécable U+00A0 pour les milliers et avant l'unité.

## Colors

Une encre brune et trois papiers pour l'interface, trois lavis de réseau pour la donnée, et un seul aplat marin réservé au fond aérien.

### Primary
- **Carmin** (carmin): la couleur du transport HTB sur la carte (lignes 400 kV et 90 kV, postes en lavis à 30 %, pylônes, cœur du symbole du CNPE). Dans l'interface, accent rare : pastille du fond choisi, survol des liens, curseur de saisie, sélection de texte à 22 %, note de qualité, écart de position ICPE, message d'erreur, rectangle de vue courante du tableau d'assemblage.

### Secondary
- **Bleu de Prusse** (bleu): la distribution Enedis (HTA, BT, postes HTA/BT, poteaux) et l'eau (mer du tableau d'assemblage à 20 %, hachures Natura 2000). N'apparaît jamais dans le chrome de l'interface.

### Tertiary
- **Vert pré** (vert): lavis des ZNIEFF (30 % pour le type 1, 13 % pour le type 2).
- **Vert de haie** (vert-fonce): trait des ZNIEFF, plein pour le type 1, tireté 3 2 pour le type 2.

### Neutral
- **Encre sépia** (encre): texte principal, tous les cadres structurants de 1 px, fond du bandeau, cercles de distance, limites communales, sélection et mesure sur la carte. Le bandeau utilise la même valeur.
- **Encre délavée** (encre-2): texte courant secondaire (paragraphes du projet, avertissements en italique, liens du pied).
- **Encre pâle** (encre-3): libellés de définition, légendes, sous-titres de couches, labels en capitales, comptes grisés. Reste lisible sur les trois papiers.
- **Papier** (papier): fond du panneau, des encarts de carte, des menus, de la carte elle-même ; texte clair du bandeau ; liseré sous les lignes de réseau.
- **Papier teinté** (papier-2): survol des lignes de couches, fond de la zone carte avant chargement des tuiles.
- **Papier ombré** (papier-3): survol des menus, boutons papier et planches ; commune survolée dans le tableau d'assemblage.
- **Filet** (filet): séparateurs internes de lignes (attributs, listes, chiffres clés, pied), jamais pour un cadre extérieur.
- **Sépia de lavis** (sepia): lavis à 20 % des terrains du Conservatoire du littoral. Couleur de carte uniquement, définie dans l'objet C du script.
- **Bandeau ombré, filet de bandeau, texte de bandeau secondaire** (bandeau-2, bandeau-filet, bandeau-texte-2): fond du champ de recherche et survol des boutons, contour des contrôles du bandeau, sous-titre et texte indicatif.
- **Mer d'aplat** (mer-ortho): lavis opaque posé sur la mer seulement quand le fond est la photographie aérienne.

### Named Rules
**The Lavis codés Rule.** Une teinte égale un réseau : carmin pour le transport HTB, bleu de Prusse pour la distribution et l'eau, vert pré pour l'environnement, sépia pour le foncier protégé. Une nouvelle couche prend la teinte de sa famille ; une nouvelle famille exige une teinte qui ne contredit aucune des quatre.

**The Encre qui désigne Rule.** La sélection et la mesure se dessinent à l'encre (lavis à 10 %, halo de 10 px à 22 %, trait de 2,2 px ; cercle de 13 px de rayon pour un point). Une teinte de donnée ne sert jamais à signaler un état.

**The Fond qui se tait Rule.** Le fond IGN est toujours atténué : plan à saturation -0,5, contraste -0,1, opacité 0,7 (0,6 sous le cadastre) ; photographies à saturation -0,3, opacité 0,92 ; cadastre PCI à 0,85 à partir du zoom 13. Les lavis doivent rester la couleur la plus forte de la planche.

## Typography

**Display Font:** Source Sans 3 (avec Source Sans Pro, system-ui, sans-serif)
**Body Font:** Source Sans 3
**Label/Mono Font:** Source Sans 3, capitales espacées pour les labels, chiffres tabulaires pour les nombres

**Character:** Une seule famille humaniste, sobre comme le lettrage d'un plan administratif. L'italique est réservé aux lieux et aux remarques ; la graisse 700 aux noms d'objets et aux chiffres.

### Hierarchy
- **Chiffres clés** (700, 28 px, 1 ; 24 px sous 760 px): les quatre valeurs du cartouche du site, avec leur définition en dessous en légende.
- **Distance** (700, 30 px, 1): distance de l'objet au CNPE dans sa fiche ; passe en 400, 20 px, encre pâle quand la position est douteuse. La mesure en cours sur la carte utilise 26 px.
- **Headline** (700, 23 px, 1,15): nom du site dans le cartouche.
- **Title** (700, 22 px, 1,2): nom de l'objet dans sa fiche, titre de la page projet.
- **Titre du bandeau** (700, 19 px ; 18 px sous 760 px): nom du projet, suivi du sous-titre à 14 px en texte de bandeau secondaire.
- **Body** (400, 15 px, 1,45): base du document. Le panneau descend à 14 et 14,5 px pour les lignes de couches, attributs et paragraphes.
- **Légende** (400, 12,5 à 13,5 px): définitions des chiffres, sources, sous-titres des entrées de menu, relevé de coordonnées.
- **Label** (600, 12 px, 0,08em, capitales): en-tête d'un bloc de contenu (groupe de couches avec sa source à droite, tableau d'assemblage, groupe de résultats). Les sections de fiche utilisent 13 px et 0,06em.
- **Lieu** (600 italique, 16 px): nom du site posé sur la carte, avec halo papier.

### Named Rules
**The Italique des lieux Rule.** Les noms de lieux posés sur la carte sont en italique, comme sur un plan. L'italique sert aussi aux remarques et aux conditions d'affichage (« visible à partir du 1:46 000 »), jamais à l'emphase.

**The Chiffres alignés Rule.** Tout nombre qui se compare ou se lit en colonne porte `font-variant-numeric: tabular-nums` : comptes de couches, chiffres clés, distances, coordonnées Lambert-93, échelle, planches, table des sources. Les nombres sont formatés en fr-FR ; le séparateur de milliers est l'espace insécable U+00A0 (l'espace fine U+202F d'Intl est remplacée, car elle disparaît en gras tabulaire) et une espace insécable sépare le nombre de son unité (« 1 330 MW », « 2,4 km »). Les distances sous 1 km s'arrondissent à 10 m ; de 1 à 10 km, une décimale ; au-delà, entier.

## Layout

Grille d'application plein écran sans défilement de page : une rangée de bandeau de 56 px (--h-bandeau) puis le plan. Sur ordinateur, le plan se partage entre un panneau fixe de 360 px (--l-panneau) à gauche, séparé par un filet d'encre, et la carte qui prend le reste.

Le panneau défile seul et empile trois vues interchangeables : couches (cartouche du site, groupes de couches, pied de sources), fiche d'objet, page projet. Les fiches et la page projet ont un en-tête collant avec le bouton de retour. Retrait horizontal constant de 20 px dans le panneau ; lignes de couches de 34 px minimum sur une grille 14 / 26 / libellé / compte.

Sur la carte, les encarts se posent à 16 px des bords (12 px sur téléphone) : zoom et recentrage en haut à droite, relevé des coordonnées et de l'échelle en bas à gauche, tableau d'assemblage de 262 px en bas à droite, mesure en haut à gauche, chargement centré en haut. Les planches se cadrent dans la partie libre de la carte, en laissant la largeur du tableau d'assemblage plus 40 px.

Rythme d'espacement observé : 4, 8, 12, 16, 20, 24 px, avec des réglages fins (6, 7, 10 px) dans les lignes denses.

**Téléphone (760 px et moins).** Le bandeau passe à 98 px sur deux rangées : titre et boutons réduits à leur icône sur la première, recherche pleine largeur sur la seconde ; le sous-titre disparaît. Le panneau devient un tiroir bas de hauteur min(78 %, 640 px), avec une poignée de 22 px, qui dépasse de 172 px (--peek) au repos et s'ouvre en translation. Le tableau d'assemblage se réduit à la rangée des quatre planches en haut, sans encart ni légende ; le relevé de coordonnées est masqué ; échelle et attributions remontent au-dessus du tiroir.

### Named Rules
**The Planche fixe Rule.** Une planche de 2, 5, 10 ou 20 km s'ouvre toujours au même cadrage autour du CNPE, quelle que soit la vue de départ.

## Elevation & Depth

Le système est plat. Aucune `box-shadow` n'existe dans l'interface : les encarts, menus, listes de résultats et le panneau se détachent par un cadre d'encre de 1 px sur papier opaque, et par leur ordre d'empilement. La profondeur de la carte est un ordre de couches dessinées de bas en haut : fond papier, fond IGN atténué, limites, lavis d'environnement, réseaux de distribution, transport HTB, cercles, points, puis sélection et mesure au sommet.

Deux halos papier existent et ne sont pas des ombres : le liseré papier sous les lignes (HTB à 75 %, HTA à 65 %, cercles à 45 %) qui détache le trait du fond, et le halo des étiquettes italiques (`text-shadow: 0 0 2px, 0 0 3px, 0 0 4px` en papier). Ce sont des réserves de cartographe, pas une élévation.

### Named Rules
**The Papier sans ombre Rule.** Un élément qui doit se détacher reçoit un cadre d'encre de 1 px, jamais une ombre portée.

**The Masques de l'ortho Rule.** Sur le fond photographique seulement, trois calques transforment l'image en planche : un lavis opaque de mer d'aplat sur la mer (les aplats pâles en escalier de la BD ORTHO transparaissent même à 0,9), du papier sur tout ce qui sort de l'emprise d'étude, et un filet d'encre de 1 px qui borde cette emprise comme un cadre de planche. Ces calques sont masqués sur les autres fonds.

## Shapes

Angles vifs. Le rayon le plus courant est de 3 px (boutons, champ de recherche, boutons papier, retour), 2 px pour les cases à cocher et la poignée du tiroir, 4 px au plus (pouce de la barre de défilement). Les encarts de carte, menus, listes et le panneau n'ont aucun arrondi. Le seul disque est la pastille carmin du choix coché et les symboles ponctuels de la carte.

Le filet est la forme de base : 1 px d'encre pour tout cadre extérieur ou séparation majeure (bord du panneau, haut des chiffres clés, haut du bloc distance, cadre des planches et séparations entre planches), 1 px de filet clair pour les séparations internes de lignes. Les icônes d'interface sont des traits de 1,6 px à bouts ronds, 18 px, dessinées au trait comme le reste.

## Components

### Buttons
- **Shape:** angles presque vifs (3 px), hauteur 34 px dans le bandeau, 30 px sur papier.
- **Bouton du bandeau:** transparent, texte papier, contour en filet de bandeau, icône au trait suivie du libellé à 14 px. Survol : fond bandeau ombré, contour en texte secondaire, transition de 0,15 s sur fond et contour. Actif (pressé ou menu ouvert) : s'inverse en papier sur encre.
- **Bouton papier:** fond papier, cadre d'encre, 13,5 px (Effacer, Terminer). Survol : papier ombré.
- **Retour:** sans cadre, icône et libellé en encre délavée ; survol en papier teinté et encre.
- **Focus:** contour de 2 px en encre décalé de 2 px ; contour papier dans le bandeau.

### Chips
- **Planches (sélecteur segmenté):** quatre cases égales de 30 px dans un cadre d'encre, séparées par des filets d'encre, sans arrondi, chiffres tabulaires. Survol papier ombré ; planche active en papier sur encre.

### Cards / Containers
- **Corner Style:** aucun arrondi.
- **Background:** papier opaque.
- **Shadow Strategy:** aucune (voir Elevation & Depth).
- **Border:** 1 px d'encre.
- **Internal Padding:** 10 px 12 px pour les encarts de carte, 16 à 20 px pour les vues du panneau.
- **Cartouche du site:** nom en headline, lieu en encre pâle, grille 2 × 2 de chiffres clés sous un filet d'encre, cellules séparées par des filets clairs, définition sous le chiffre, avertissement en italique.

### Inputs / Fields
- **Recherche:** champ de 34 px dans le bandeau, fond bandeau ombré, contour en filet de bandeau, loupe au trait à gauche, texte indicatif en texte secondaire, curseur carmin. Focus : le contour passe en papier, sans halo.
- **Résultats:** liste papier cadrée d'encre sous le champ, lignes de 7 px 12 px avec commune en légende et distance au CNPE alignée à droite en chiffres tabulaires ; ligne active ou survolée en papier ombré ; groupes en label.
- **Case de couche:** carré de 14 px, rayon 2 px, cadre d'encre ; cochée, elle se remplit d'encre avec une coche papier.

### Navigation
- **Menu des fonds:** liste papier cadrée d'encre, chaque entrée avec un sous-titre en légende qui dit à quoi sert le fond ; le choix courant porte une pastille carmin de 9 px. Pas de vignettes.
- **Commandes de carte:** colonne de trois boutons de 36 px (zoomer, dézoomer, recentrer) dans un cadre d'encre, séparés par des filets clairs.
- **Relevé:** bande papier cadrée d'encre, coordonnées Lambert-93, système et échelle 1 : n séparés par des points médians, chiffres tabulaires.
- **Tiroir mobile:** poignée de 22 px avec une barre de 44 × 4 px en encre pâle ; ouverture en 0,35 s sur la courbe easeOutExpo du thème.

### Ligne de couche
Grille case / pastille / libellé / compte, 34 px minimum. Le compte se lit « objets dans la vue / total », le premier en gras. Couche décochée : pastille, libellé et compte à 50 %. Couche hors échelle : pastille à 45 %, compte non gras en encre pâle, sous-titre italique « visible à partir du 1:n ». Les groupes portent un label en capitales avec le producteur de la donnée aligné à droite.

### Fiche d'objet
Titre de l'objet, rappel de sa couche avec sa pastille, bloc distance au CNPE entre un filet d'encre et un filet clair, puis table d'attributs en deux colonnes (38 %, minimum 110 px) séparée par des filets clairs. Une valeur en écart passe en carmin. Liens externes avec icône au trait, source en légende.

### Symbologie de la carte
Chaque symbole est défini une fois dans l'objet de couleurs C et réutilisé par la carte et sa pastille de légende (26 × 16 px).
- **Transport HTB:** lignes carmin, 400 kV de 2,2 à 4,5 px et 90 kV de 1,1 à 2,4 px entre les zooms 9 et 16, sur liseré papier ; postes en lavis carmin 30 % et trait 1,2 px ; pylônes en carré papier cerclé de carmin dès le zoom 12.
- **Distribution:** HTA bleue pleine en aérien, tiretée 3 2 en souterrain, liseré papier dès le zoom 11 ; BT dès le zoom 13, pleine ou tiretée 2 2, plus fine et à 70 ou 80 % ; postes HTA/BT en triangle papier cerclé de bleu dès 12,5 ; poteaux en point bleu de 2,2 px dès 14,5.
- **Environnement:** ZNIEFF en lavis vert pré et trait vert de haie ; Natura 2000 en hachures bleues à 45 °, sens opposés pour ZSC et ZPS, trait bleu de 1,2 px ; Conservatoire en lavis sépia 20 % et pointillé d'encre 1 2.
- **Site et repères:** CNPE en disque papier cerclé d'encre à cœur carmin ; cercles de 2, 5, 10 et 20 km en tireté d'encre 5 4 de 1,3 px, étiquetés dans une petite boîte papier cadrée d'encre ; limites communales en trait mixte 6 2 1 2 à 42 %.
- **ICPE:** losange plein d'encre pour l'autorisation, losange papier cerclé d'encre pour l'enregistrement, petit point d'encre pour les autres régimes ; anneau carmin de 9 px autour d'un point dont la position contredit la commune déclarée.
- **Production:** cercles proportionnels au logarithme de la puissance, papier à 55 %, trait d'encre de 1,4 px.

### Tableau d'assemblage
Encart de 262 px : label en capitales, mini-carte SVG (mer bleue à 20 %, communes en papier à filet d'encre 40 %, quatre anneaux tiretés, anneau actif plein de 2 px, site en point carmin), rangée des planches, puis une légende qui résume l'anneau choisi. Cliquer une commune cadre la carte sur elle et ouvre sa fiche ; cliquer un anneau ouvre sa planche. Le rectangle de la vue courante suit chaque déplacement : lavis carmin à 12 % et trait carmin de 1,5 px ; au-delà de 40 % de l'encart couvert, il ne garde que son trait ; au-delà de 90 %, il disparaît, l'anneau actif suffisant à situer la vue.

### Mouvement
Les vols de carte utilisent easeOutExpo : 1 400 ms pour une planche ou un résultat de recherche, 900 ms pour cadrer une commune. Le tiroir utilise `cubic-bezier(.16, 1, .3, 1)` en 0,35 s. Les survols changent seulement la couleur de fond, en 0,12 à 0,15 s. Avec `prefers-reduced-motion: reduce`, les vols sont instantanés et toutes les transitions CSS tombent à 0 s.

## Do's and Don'ts

### Do:
- **Do** encadrer tout encart, menu ou liste flottante d'un filet d'encre de 1 px sur papier opaque.
- **Do** garder les rayons à 2 ou 3 px, 4 px au plus.
- **Do** donner à chaque nouvelle couche une pastille de 26 × 16 px qui reproduit son symbole de carte, construite à partir des mêmes couleurs, épaisseurs et tirets.
- **Do** dessiner la sélection et la mesure à l'encre.
- **Do** formater chaque nombre en fr-FR avec U+00A0 pour les milliers et avant l'unité, en chiffres tabulaires.
- **Do** poser les noms de lieux en italique avec un halo papier.
- **Do** indiquer la source et le compte d'objets de chaque couche, et l'échelle à partir de laquelle elle s'affiche.
- **Do** respecter `prefers-reduced-motion` pour chaque animation nouvelle, en JS comme en CSS.

### Don't:
- **Don't** utiliser d'ombre portée ni de bouton flottant arrondi.
- **Don't** proposer les fonds sous forme de galerie de vignettes ; un menu de libellés avec leur usage suffit.
- **Don't** employer le bleu de Prusse ou le vert pré dans le chrome de l'interface ; ce sont des couleurs de donnée.
- **Don't** afficher le fond IGN à pleine saturation.
- **Don't** utiliser le label en capitales comme surtitre au-dessus d'un titre ; il ne sert qu'à nommer un bloc de contenu.
- **Don't** laisser l'espace fine U+202F d'Intl dans un nombre affiché.
