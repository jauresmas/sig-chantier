---
version: 1
slug: "docs-index-html"
primary_target: "docs/index.html"
related_targets: ["docs/app.js","docs/style.css"]
---

# Carte web : SIG chantier Penly

## Scope

- Surface : `docs/index.html` (carte web autonome, GitHub Pages), avec `docs/app.js`, `docs/style.css`, `docs/data/`.
- Mode : Operate. Le visiteur explore une carte et lit des fiches d'objets.

## Audience and job

- Recruteurs et ingénieurs SIG arrivés depuis un CV ou un profil, sur ordinateur surtout, parfois sur téléphone.
- Tâche : comprendre en 30 s le site et ses contraintes, puis cliquer un objet, lire sa fiche, mesurer, changer de fond.
- Preuve : chaque couche donne sa source, sa date d'extraction et son nombre d'objets.
- Contraintes : site statique sans compilation, MapLibre GL JS par CDN, fonds IGN Géoplateforme, données GeoJSON du dépôt.

## Direction contract

THESIS: Le site lu comme un plan cadastral : encre sépia, lavis codés par réseau, et un tableau d'assemblage qui sert de navigateur. Refuse le visualiseur SIG par défaut : panneau blanc à cases à cocher, boutons flottants bleus arrondis à ombre, galerie de fonds en vignettes.

OWN-WORLD: Encre sépia #2f241d sur papier #faf8f3 ; lavis carmin #c8385a pour le transport HTB, bleu de Prusse #4f7fb0 pour la distribution et l'eau, vert pré #8fae74 pour l'environnement. Cadres d'encre de 1 px, angles vifs (rayon 4 px maximum), aucune ombre portée. Source Sans 3, italique pour les lieux, chiffres tabulaires. Fond IGN désaturé pour que les lavis portent la donnée.

STORY: Le visiteur voit le CNPE de Penly (2 × 1 330 MW, deux tranches en projet), les lignes 400 kV qui en partent, le réseau Enedis et les zones protégées qui encadrent un chantier ; il croit la carte parce que chaque couche est sourcée, datée et comptée ; il clique un objet, lit sa fiche et sa distance au CNPE, ou ouvre une planche à 2, 5, 10 ou 20 km.

FIRST VIEWPORT: Bandeau sépia de 56 px : nom du projet, sous-titre, recherche d'adresse, Mesurer, choix du fond. Panneau papier de 360 px à gauche : fiche du site avec quatre chiffres clés en 30 px, puis couches groupées (pastille d'encre, libellé, nombre d'objets), pied de sources et date. À droite, carte plein cadre : cercles en tirets d'encre, HTB carmin, HTA bleu, ZNIEFF en lavis vert. En bas à droite, le tableau d'assemblage ; en bas à gauche, coordonnées Lambert-93 et échelle. Action principale : cliquer un objet ou un anneau.

FORM: Le plan cadastral, carte assignée par le tirage (rang 7 de la liste ordonnée), seed:b3dc83b5354d298c. Interaction signature : le tableau d'assemblage. Un clic sur un anneau ouvre la planche 2 / 5 / 10 / 20 km toujours au même cadrage ; le rectangle de la vue courante suit sur l'encart ; l'objet sélectionné reste surligné avec sa distance au CNPE.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Memorable moment

Le tableau d'assemblage : un encart d'encre qui sert à la fois de carte de situation et de navigateur entre planches.

## Open decisions

- Réseau BT et poteaux : affichés seulement à grande échelle (zoom 14 et plus), découpés à 10 km du site.
- Plan cadastral PCI : fond optionnel au-dessus du plan IGN, pas de couche vecteur des parcelles.
