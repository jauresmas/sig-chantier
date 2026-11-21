"""Catalogue des couches publiées : nom (table du schéma carto et couche GeoServer), style, titre et
résumé, groupe dans la carte MapStore, visibilité initiale et fiche d'information au clic.

Une seule source pour GeoServer (02_publier_geoserver.py) et MapStore (03_publier_mapstore.py).
Les groupes et leurs couleurs reprennent la carte web du dépôt.
"""
from styles import BLEU, CARMIN, ENCRE, ENCRE_3, SEPIA, VERT_FONCE

GROUPES = [  # id, titre, déplié ; ordre de la table des matières, de haut en bas
    ("site", "Site et zonages", True),
    ("icpe", "Installations classées", True),
    ("production", "Production d'électricité", False),
    ("htb", "Transport HTB", True),
    ("distribution", "Distribution", False),
    ("environnement", "Environnement", True),
    ("referentiel", "Référentiel", False),
]


def _ligne(libelle, champ):
    return (f'<tr><th style="text-align:left;font-weight:600;color:#5a4a3d;padding:3px 12px 3px 0;'
            f'vertical-align:top;white-space:nowrap">{libelle}</th><td style="padding:3px 0">'
            f'${{properties.{champ}}}</td></tr>')


def fiche(titre, couleur, lignes, note="", lien=None):
    """Gabarit HTML d'une fiche MapStore (format TEMPLATE) : filet de couleur de la couche, champs en tableau."""
    corps = "".join(_ligne(l, c) for l, c in lignes)
    n = f'<p style="margin:8px 0 0;font-size:11px;line-height:1.4;color:#6f5f51">{note}</p>' if note else ""
    a = (f'<p style="margin:8px 0 0"><a href="${{properties.{lien[1]}}}" target="_blank" rel="noopener" '
         f'style="color:#2f241d">{lien[0]}</a></p>') if lien else ""
    return (f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:13px;color:#2f241d;max-width:380px">'
            f'<div style="border-left:4px solid {couleur};padding-left:8px;margin-bottom:6px">'
            f'<strong style="font-size:14px">{titre}</strong></div>'
            f'<table style="border-collapse:collapse">{corps}</table>{n}{a}</div>')


SOURCE_IGN = "Source : IGN, BD TOPO (lignes électriques d'après RTE)."
SOURCE_ENEDIS = "Source : Enedis, open data. Linéaire au tronçon."
SOURCE_INPN = "Source : INPN, PatriNat (MNHN)."

COUCHES = [
    # --- Site et zonages
    dict(nom="cnpe", style="penly_cnpe", groupe="site", visible=True,
         titre="CNPE de Penly",
         resume="Centre nucléaire de production d'électricité de Penly (Petit-Caux), exploité par EDF.",
         fiche=fiche("${properties.nom}", CARMIN,
                     [("Exploitant", "exploitant"), ("Commune", "commune"), ("Tranches", "tranches"),
                      ("Puissance installée", "puissance"), ("Mise en service", "mise_en_service"),
                      ("Projet", "projet")], "Source : EDF, opendata.edf.fr.")),
    dict(nom="cercles", style="penly_cercles", groupe="site", visible=True,
         titre="Cercles de 2, 5, 10 et 20 km",
         resume="Zonages d'étude autour du CNPE ; 20 km est le rayon du plan particulier d'intervention (PPI).",
         fiche=None),  # disques emboîtés : une fiche répondrait à chaque clic de la carte
    # --- Installations classées
    dict(nom="icpe", style="penly_icpe", groupe="icpe", visible=True,
         titre="Installations classées (ICPE)",
         resume="Installations classées pour la protection de l'environnement, avec un contrôle de position : "
                "la commune déclarée au registre est comparée à la commune où tombe le point.",
         fiche=fiche("${properties.nom}", ENCRE,
                     [("Distance au CNPE", "distance"), ("Contrôle de position", "controle_position"),
                      ("Régime", "regime_libelle"), ("Activité", "activite"), ("Commune déclarée", "commune_declaree"),
                      ("Dernière inspection", "derniere_inspection"), ("Priorité nationale", "priorite_nationale"),
                      ("Code AIOT", "code_aiot")],
                     "Source : Géorisques (via Koumoul). Une position douteuse rend la distance non fiable.",
                     ("Fiche Géorisques", "fiche_georisques"))),
    # --- Production
    dict(nom="production", style="penly_production", groupe="production", visible=True,
         titre="Installations de production (par commune)",
         resume="Registre national des installations de production et de stockage (Agence ORE) : le registre "
                "place chaque installation au centre de sa commune, d'où un symbole par commune.",
         fiche=fiche("Production à ${properties.commune}", ENCRE,
                     [("Installations", "installations"), ("Puissance installée", "puissance"),
                      ("Filière principale", "filiere_principale"), ("Filières", "filieres"),
                      ("Distance au CNPE", "distance")],
                     "Source : Agence ORE, registre des installations. Position au centre de la commune.")),
    # --- Transport HTB
    dict(nom="htb_lignes", style="penly_htb_lignes", groupe="htb", visible=True,
         titre="Lignes 400 kV et 90 kV", resume="Lignes électriques à haute tension (réseau de transport).",
         fiche=fiche("Ligne ${properties.tension}", CARMIN,
                     [("État", "etat"), ("Longueur du tronçon", "longueur"), ("Distance au CNPE", "distance"),
                      ("Source", "source")], SOURCE_IGN)),
    dict(nom="htb_postes", style="penly_htb_postes", groupe="htb", visible=True,
         titre="Postes électriques HTB", resume="Postes de transformation du réseau de transport.",
         fiche=fiche("${properties.nom}", CARMIN, [("État", "etat"), ("Distance au CNPE", "distance")], SOURCE_IGN)),
    dict(nom="htb_pylones", style="penly_htb_pylones", groupe="htb", visible=True,
         titre="Pylônes", resume="Pylônes des lignes HTB, visibles à partir du 1:46 000.",
         fiche=fiche("Pylône", CARMIN, [("Numéro", "numero"), ("État", "etat")], SOURCE_IGN)),
    # --- Distribution
    dict(nom="hta", style="penly_hta", groupe="distribution", visible=True,
         titre="Réseau HTA", resume="Lignes moyenne tension (20 kV) aériennes et souterraines.",
         fiche=fiche("Réseau HTA, pose ${properties.pose}", BLEU,
                     [("Commune", "commune"), ("Longueur du tronçon", "longueur")], SOURCE_ENEDIS)),
    dict(nom="postes_hta_bt", style="penly_postes_hta_bt", groupe="distribution", visible=True,
         titre="Postes HTA/BT", resume="Postes de distribution publique, visibles à partir du 1:33 000.",
         fiche=fiche("Poste HTA/BT", BLEU, [("Commune", "commune")], SOURCE_ENEDIS)),
    dict(nom="bt", style="penly_bt", groupe="distribution", visible=True,
         titre="Réseau BT", resume="Lignes basse tension aériennes et souterraines, visibles à partir du 1:23 000.",
         fiche=fiche("Réseau BT, pose ${properties.pose}", BLEU,
                     [("Commune", "commune"), ("Longueur du tronçon", "longueur")], SOURCE_ENEDIS)),
    dict(nom="poteaux", style="penly_poteaux", groupe="distribution", visible=True,
         titre="Poteaux HTA et BT", resume="Supports des lignes aériennes, visibles à partir du 1:8 200.",
         fiche=fiche("Poteau", BLEU, [("Commune", "commune")], SOURCE_ENEDIS)),
    # --- Environnement
    dict(nom="natura2000_zps", style="penly_natura2000_zps", groupe="environnement", visible=True,
         titre="Natura 2000, directive Oiseaux (ZPS)", resume="Zones de protection spéciale.",
         fiche=fiche("${properties.nom}", VERT_FONCE, [("Type", "type_zone"), ("Code", "code"), ("Surface", "surface")],
                     SOURCE_INPN, ("Fiche INPN", "fiche_inpn"))),
    dict(nom="natura2000_zsc", style="penly_natura2000_zsc", groupe="environnement", visible=True,
         titre="Natura 2000, directive Habitats (ZSC)", resume="Zones spéciales de conservation.",
         fiche=fiche("${properties.nom}", VERT_FONCE, [("Type", "type_zone"), ("Code", "code"), ("Surface", "surface")],
                     SOURCE_INPN, ("Fiche INPN", "fiche_inpn"))),
    dict(nom="conservatoire", style="penly_conservatoire", groupe="environnement", visible=True,
         titre="Conservatoire du littoral", resume="Terrains acquis par le Conservatoire du littoral.",
         fiche=fiche("${properties.nom}", SEPIA, [("Type", "type_zone"), ("Code", "code"), ("Surface", "surface")],
                     SOURCE_INPN, ("Fiche INPN", "fiche_inpn"))),
    dict(nom="znieff1", style="penly_znieff1", groupe="environnement", visible=True,
         titre="ZNIEFF de type I", resume="Zones naturelles d'intérêt écologique, faunistique et floristique de type I.",
         fiche=fiche("${properties.nom}", VERT_FONCE, [("Type", "type_zone"), ("Code", "code"), ("Surface", "surface")],
                     SOURCE_INPN, ("Fiche INPN", "fiche_inpn"))),
    dict(nom="znieff2", style="penly_znieff2", groupe="environnement", visible=False,
         titre="ZNIEFF de type II", resume="Grands ensembles naturels riches et peu modifiés (ZNIEFF de type II).",
         fiche=fiche("${properties.nom}", VERT_FONCE, [("Type", "type_zone"), ("Code", "code"), ("Surface", "surface")],
                     SOURCE_INPN, ("Fiche INPN", "fiche_inpn"))),
    # --- Référentiel
    dict(nom="communes", style="penly_communes", groupe="referentiel", visible=True,
         titre="Communes", resume="Limites et noms des communes (IGN, BD TOPO).",
         fiche=fiche("${properties.nom}", ENCRE_3,
                     [("Code INSEE", "code_insee"), ("Code postal", "code_postal"), ("Population", "population")],
                     "Source : IGN, BD TOPO ; population INSEE.")),
    dict(nom="batiments", style="penly_batiments", groupe="referentiel", visible=False,
         titre="Bâtiments", resume="Bâtiments de la BD TOPO à 10 km autour du CNPE, visibles à partir du 1:20 000.",
         fiche=fiche("Bâtiment", ENCRE_3, [("Nature", "nature"), ("Usage", "usage"), ("Hauteur", "hauteur"),
                                           ("Logements", "logements")], "Source : IGN, BD TOPO.")),
    dict(nom="parcelles", style="penly_parcelles", groupe="referentiel", visible=False,
         titre="Parcelles cadastrales de Petit-Caux", resume="Plan cadastral (Etalab), visible à partir du 1:12 000.",
         fiche=fiche("Parcelle ${properties.identifiant}", SEPIA,
                     [("Section", "section"), ("Numéro", "numero"), ("Contenance", "contenance")],
                     "Source : cadastre Etalab (DGFiP).")),
]
