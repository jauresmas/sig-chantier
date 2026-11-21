# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Site statique sans compilation : HTML, CSS et JavaScript, carte avec MapLibre GL JS (bibliothèque chargée depuis un CDN).
Données servies en GeoJSON depuis le dépôt. Déploiement : GitHub Pages, dépôt public `sig-chantier`.
Le reste du projet (préparation des données, projet QGIS, modèles du Modeleur) reste en Python / PyQGIS.

## Users

Recruteurs, managers et ingénieurs SIG qui évaluent le savoir-faire de l'auteur (portfolio).
Ils ouvrent le lien depuis un CV ou un profil, sur ordinateur le plus souvent, parfois sur téléphone.
Ils doivent comprendre en une trentaine de secondes le site étudié, les contraintes qui pèsent sur un chantier
à cet endroit et la qualité du travail, puis pouvoir explorer les couches en détail.

## Product Purpose

Démonstrateur d'un SIG de chantier construit uniquement avec des données ouvertes, autour de la centrale nucléaire
de Penly (Petit-Caux, Seine-Maritime), où deux nouvelles tranches sont en projet.
Il reproduit la chaîne de travail d'un SIG de chantier : collecte et contrôle des données, base structurée en
Lambert-93, modèle de données du plan d'installation de chantier (PIC), conversion CAO vers SIG, traitements
automatisés (Python et Modeleur graphique QGIS), plans à la demande et publication web.
Succès : le visiteur repart convaincu que l'auteur sait structurer, croiser et publier des données de chantier.

## Positioning

Projet de bout en bout et rejouable : chaque couche affichée vient d'une source ouverte citée, d'un script et d'un
modèle QGIS versionnés dans le même dépôt. La carte web est la vitrine d'une chaîne réelle, pas une maquette.

## Operating Context

- Données : `02_donnees/sig_chantier.gpkg` (Lambert-93), sources listées dans `01_donnees_brutes/manifeste.json`.
- Outils de l'auteur : QGIS 3.34, PostGIS, GeoServer et MapStore (pile Docker locale), Python.
- La carte web est autonome : elle ne dépend pas du GeoServer local et fonctionne sur GitHub Pages.

## Capabilities and Constraints

- Couches : réseaux électriques (lignes HTB 400 / 90 kV et postes, réseau HTA / BT et postes HTA/BT), installations
  de production, environnement (ZNIEFF, Natura 2000, Conservatoire du littoral), ICPE, référentiel (communes, routes,
  voies ferrées, hydrographie), zonages d'étude de 2, 5, 10 et 20 km autour du site.
- Fonds de plan IGN (Géoplateforme) : plan, orthophotographie.
- Fonctions attendues : panneau de couches groupées avec légende, fiches attributaires, mesure de distance,
  recherche d'adresse, fiche de synthèse du site.
- Terminologie : CNPE (centre nucléaire de production d'électricité), PIC, HTB / HTA / BT, PPI (plan particulier
  d'intervention, rayon de 20 km), DT-DICT, ZNIEFF, ICPE.
- Langue : français.

## Brand Commitments

- Nom du projet : « SIG chantier » (dépôt `sig-chantier`).
- Aucune marque, logo ou charte d'exploitant ou d'industriel : le projet n'est affilié à aucune entreprise.
  Les producteurs de données (EDF, Enedis, Agence ORE, IGN, PatriNat, Géorisques, DGFiP) apparaissent uniquement
  comme sources, comme l'exige la Licence Ouverte Etalab 2.0.

## Evidence on Hand

- Données réelles téléchargées le 21/11/2026 (36 jeux, manifeste avec URL et licences).
- Résultats des modèles testés sur ces données (voir LISEZMOI.md).
- Plan A3 exporté : `06_exports/plan_situation_A3.pdf`.
- Absences à ne pas combler : les emprises réelles du futur chantier ne sont pas publiques ; le plan DXF de
  `04_cao/` est fictif et ne doit jamais être présenté comme réel. Pas de témoignages, pas de clients.

## Product Principles

1. Toute information affichée est sourcée et datée.
2. La donnée d'abord : la carte montre les contraintes réelles du site, sans décor.
3. Lisible en 30 secondes, explorable en profondeur.
4. Rien de fictif présenté comme réel.
5. Rejouable : le dépôt suffit à reconstruire chaque couche.
