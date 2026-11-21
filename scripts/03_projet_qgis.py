"""
03_projet_qgis.py : Construit le projet QGIS 03_qgis/sig_chantier_penly.qgz (couches, styles, formulaires PIC, fonds IGN, mise en page).

Deux façons de le lancer :
  - dans QGIS (console Python) :  exec(open(r"<dossier>\\scripts\\03_projet_qgis.py", encoding="utf-8").read())
  - hors QGIS (PowerShell)     :  & "C:\\Program Files\\QGIS 3.34.12\\bin\\python-qgis-ltr.bat" scripts\\03_projet_qgis.py
"""
import os
import sys
from pathlib import Path

from qgis.core import (
    Qgis, QgsApplication, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem, QgsDataSourceUri,
    QgsDefaultValue, QgsEditorWidgetSetup, QgsFieldConstraints, QgsFillSymbol, QgsLayerTree, QgsLayoutExporter,
    QgsLayoutItemLabel, QgsLayoutItemLegend, QgsLayoutItemMap, QgsLayoutItemPicture, QgsLayoutItemScaleBar,
    QgsLayoutPoint, QgsLayoutSize, QgsLineSymbol, QgsMarkerSymbol, QgsPalLayerSettings, QgsPrintLayout,
    QgsProject, QgsRasterLayer, QgsRectangle, QgsReferencedRectangle, QgsRendererCategory, QgsSymbolLayerUtils,
    QgsTextBufferSettings, QgsTextFormat, QgsUnitTypes, QgsVectorLayer, QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont

RACINE = Path(globals().get("__file__", Path.cwd() / "scripts" / "x.py")).resolve().parent.parent
GPKG = (RACINE / "02_donnees" / "penly_sig.gpkg").as_posix()
PIC = (RACINE / "02_donnees" / "pic_chantier.gpkg").as_posix()
QGZ = (RACINE / "03_qgis" / "sig_chantier_penly.qgz").as_posix()
L93 = QgsCoordinateReferenceSystem("EPSG:2154")
EMPRISE_5KM = QgsRectangle()  # calculée depuis le cercle de 5 km dans construire()
POLICE = "Segoe UI"

# ------------------------------------------------------------------ listes de valeurs du PIC
VAL_TYPE_ZONE = [
    ("Base vie", "base_vie", "#7b3294"), ("Stockage matériaux", "stockage", "#e66101"),
    ("Préfabrication / ferraillage", "prefabrication", "#fdb863"), ("Parking", "parking", "#999999"),
    ("Zone de travaux", "zone_travaux", "#d7191c"), ("Plateforme de levage", "plateforme_levage", "#a6611a"),
    ("Dépôt déblais / remblais", "deblais_remblais", "#8c6d31"), ("Zone de sécurité / exclusion", "securite", "#ff00ff"),
    ("Zone environnementale à préserver", "environnement", "#1a9641"), ("Autre", "autre", "#636363"),
]
VAL_TYPE_ACCES = [
    ("Route de chantier", "route_chantier", "#d7191c"), ("Piste", "piste", "#a6611a"),
    ("Cheminement piéton", "pieton", "#2c7bb6"), ("Itinéraire convoi exceptionnel", "convoi", "#7b3294"),
    ("Accès secours", "secours", "#1a9641"),
]
VAL_TYPE_EQUIP = [
    ("Grue à tour", "grue_tour", "#d7191c"), ("Grue mobile", "grue_mobile", "#fdae61"),
    ("Centrale à béton", "centrale_beton", "#636363"), ("Bungalow / bureau", "bungalow", "#7b3294"),
    ("Poste de garde", "poste_garde", "#2c7bb6"), ("Poste électrique de chantier", "poste_elec", "#ffd700"),
    ("Point d'eau / borne incendie", "eau_incendie", "#00bfff"), ("Bassin de rétention", "bassin", "#1a9641"),
    ("Autre", "autre", "#999999"),
]
VAL_LOT = [("Génie civil principal", "GCP"), ("Infrastructures", "INFRA"), ("OPC", "OPC"), ("Logistique", "LOG"),
           ("Sécurité", "SECU"), ("Environnement", "ENV"), ("Ingénierie de chantier", "ING")]
VAL_PHASE = [("0 : Travaux préparatoires", "P0"), ("1 : Terrassements", "P1"), ("2 : Génie civil", "P2"),
             ("3 : Montage", "P3"), ("4 : Essais", "P4")]
VAL_STATUT = [("En projet", "projet"), ("Validé", "valide"), ("Actif", "actif"), ("Libéré", "libere")]
VAL_SOURCE = [("CAO (DWG/DXF)", "CAO"), ("BIM (IFC)", "BIM"), ("Relevé terrain", "TERRAIN"),
              ("Drone (orthophoto)", "DRONE"), ("Saisie SIG", "SIG")]


# ------------------------------------------------------------------ outils de symbologie
def col(c):
    """'#RRGGBB' ou '#RRGGBBAA' (CSS) -> 'r,g,b,a' : Qt lirait '#AARRGGBB' sinon."""
    c = c.lstrip("#")
    if len(c) == 6:
        c += "ff"
    r, g, b, a = (int(c[i:i + 2], 16) for i in (0, 2, 4, 6))
    return f"{r},{g},{b},{a}"


def ligne(couleur, largeur=0.4, style="solid"):
    return QgsLineSymbol.createSimple({"line_color": col(couleur), "line_width": str(largeur), "line_style": style,
                                       "capstyle": "round", "joinstyle": "round"})


def surface(fond, contour="#00000000", epaisseur=0.3, style="solid", style_contour="solid"):
    return QgsFillSymbol.createSimple({"color": col(fond), "outline_color": col(contour), "outline_width": str(epaisseur),
                                       "style": style, "outline_style": style_contour})


def point(forme, couleur, taille=2.0, contour="#ffffff", ep=0.2):
    return QgsMarkerSymbol.createSimple({"name": forme, "color": col(couleur), "size": str(taille),
                                         "outline_color": col(contour), "outline_width": str(ep)})


def symbole_unique(couche, sym):
    couche.renderer().setSymbol(sym)


def categories(couche, champ, items):
    """items : [(valeur, symbole, libellé)] ; une valeur '' = « toutes les autres valeurs »."""
    couche.setRenderer(QgsCategorizedSymbolRenderer(champ, [QgsRendererCategory(v, s, l) for v, s, l in items]))


def etiquettes(couche, expr, taille=8, couleur="#222222", gras=False, echelle_max=None, placement=None, italique=False):
    s = QgsPalLayerSettings()
    s.fieldName = expr
    s.isExpression = True
    fmt = QgsTextFormat()
    f = QFont(POLICE)
    f.setBold(gras)
    f.setItalic(italique)
    fmt.setFont(f)
    fmt.setSize(taille)
    fmt.setColor(QColor(couleur))
    b = QgsTextBufferSettings()
    b.setEnabled(True)
    b.setSize(0.8)
    b.setColor(QColor("white"))
    fmt.setBuffer(b)
    s.setFormat(fmt)
    if placement is not None:
        s.placement = placement
    if echelle_max:
        s.scaleVisibility = True
        s.minimumScale = echelle_max
        s.maximumScale = 1
    couche.setLabeling(QgsVectorLayerSimpleLabeling(s))
    couche.setLabelsEnabled(True)


def visible_sous(couche, echelle):
    couche.setScaleBasedVisibility(True)
    couche.setMinimumScale(echelle)
    couche.setMaximumScale(1)


# ------------------------------------------------------------------ couches
class Constructeur:
    def __init__(self, projet):
        self.p = projet
        self.racine = projet.layerTreeRoot()
        self.c = {}

    def groupe(self, nom, ouvert=False):
        g = self.racine.addGroup(nom)
        g.setExpanded(ouvert)
        return g

    def vecteur(self, groupe, table, alias, visible=True, gpkg=GPKG):
        lyr = QgsVectorLayer(f"{gpkg}|layername={table}", alias, "ogr")
        if not lyr.isValid():
            raise RuntimeError(f"Couche invalide : {table}")
        self.p.addMapLayer(lyr, False)
        n = groupe.addLayer(lyr)
        n.setItemVisibilityChecked(visible)
        n.setExpanded(False)
        self.c[table] = lyr
        return lyr

    def xyz(self, groupe, nom, couche_ign, style, fmt, visible=True, zmax=19, opacite=1.0):
        url = ("https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
               f"&LAYER={couche_ign}&STYLE={style}&TILEMATRIXSET=PM&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&FORMAT={fmt}")
        uri = QgsDataSourceUri()
        uri.setParam("type", "xyz")
        uri.setParam("url", url)
        uri.setParam("zmin", "0")
        uri.setParam("zmax", str(zmax))
        lyr = QgsRasterLayer(bytes(uri.encodedUri()).decode(), nom, "wms")
        lyr.renderer().setOpacity(opacite)
        self.p.addMapLayer(lyr, False)
        n = groupe.addLayer(lyr)
        n.setItemVisibilityChecked(visible)
        return lyr


def formulaire_pic(lyr, champ_type, valeurs_type):
    """Listes de valeurs, alias, valeurs par défaut et contraintes des couches PIC."""
    def liste(champ, valeurs):
        i = lyr.fields().indexOf(champ)
        if i >= 0:
            lyr.setEditorWidgetSetup(i, QgsEditorWidgetSetup("ValueMap", {"map": [{lib: val} for lib, val, *_ in valeurs]}))

    liste(champ_type, valeurs_type)
    liste("lot", VAL_LOT)
    liste("phase", VAL_PHASE)
    liste("statut", VAL_STATUT)
    liste("source", VAL_SOURCE)
    alias = {champ_type: "Type", "libelle": "Libellé", "code_zone": "Code zone", "lot": "Lot responsable",
             "phase": "Phase", "statut": "Statut", "date_debut": "Début", "date_fin": "Fin", "source": "Source de la donnée",
             "ref_document": "Référence document (plan, IFC...)", "auteur": "Auteur", "date_maj": "Mise à jour",
             "commentaire": "Commentaire", "rayon_action_m": "Rayon d'action (m)", "hauteur_m": "Hauteur (m)",
             "sens": "Sens", "gabarit": "Gabarit"}
    for champ, a in alias.items():
        i = lyr.fields().indexOf(champ)
        if i >= 0:
            lyr.setFieldAlias(i, a)
    defauts = {"statut": "'projet'", "source": "'SIG'", "auteur": "@user_full_name", "date_maj": "now()"}
    for champ, expr in defauts.items():
        i = lyr.fields().indexOf(champ)
        if i >= 0:
            lyr.setDefaultValueDefinition(i, QgsDefaultValue(expr, champ == "date_maj"))
    for champ in (champ_type, "lot", "statut"):
        i = lyr.fields().indexOf(champ)
        if i >= 0:
            lyr.setFieldConstraint(i, QgsFieldConstraints.ConstraintNotNull, QgsFieldConstraints.ConstraintStrengthHard)


def construire(projet):
    projet.clear()
    projet.setCrs(L93)
    projet.setTitle("SIG chantier Penly : démonstrateur open data")
    k = Constructeur(projet)

    # 1 · PIC ---------------------------------------------------------------
    g = k.groupe("1 · Chantier : plan d'installation (à saisir)", ouvert=True)
    eq = k.vecteur(g, "pic_equipement", "Équipements de chantier", gpkg=PIC)
    ac = k.vecteur(g, "pic_acces", "Accès et circulations", gpkg=PIC)
    zo = k.vecteur(g, "pic_zone", "Zones d'installation", gpkg=PIC)
    categories(zo, "type_zone", [(v, surface(c + "66", c, 0.5), l) for l, v, c in VAL_TYPE_ZONE])
    categories(ac, "type_acces", [(v, ligne(c, 0.8), l) for l, v, c in VAL_TYPE_ACCES])
    categories(eq, "type_equipement", [(v, point("square" if "grue" not in v else "cross2", c, 3.0, "#000000"), l) for l, v, c in VAL_TYPE_EQUIP])
    formulaire_pic(zo, "type_zone", VAL_TYPE_ZONE)
    formulaire_pic(ac, "type_acces", VAL_TYPE_ACCES)
    formulaire_pic(eq, "type_equipement", VAL_TYPE_EQUIP)
    etiquettes(zo, "coalesce(\"code_zone\", '') || ' ' || coalesce(\"libelle\", '')", 8, "#000000", gras=True)

    # 2 · zonages -------------------------------------------------------------
    g = k.groupe("2 · Zonages d'étude", ouvert=True)
    cnpe = k.vecteur(g, "zon_cnpe_penly", "CNPE de Penly")
    symbole_unique(cnpe, point("star", "#d7191c", 7, "#ffffff", 0.4))
    etiquettes(cnpe, "'CNPE de Penly'", 10, "#a50f15", gras=True)
    cer = k.vecteur(g, "zon_cercles", "Cercles 2 / 5 / 10 / 20 km")
    symbole_unique(cer, surface("#00000000", "#a50f15", 0.5, "no", "dash"))
    etiquettes(cer, "\"rayon_km\" || ' km'", 9, "#a50f15", gras=True, placement=Qgis.LabelPlacement.Line)
    for f in cer.getFeatures():
        if f["rayon_km"] == 5:
            r = f.geometry().boundingBox()
            r.scale(1.12)
            EMPRISE_5KM.set(r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum())

    # 3 · production ----------------------------------------------------------
    g = k.groupe("3 · Production d'électricité")
    nuc = k.vecteur(g, "prod_centrales_nucleaires", "Centrales nucléaires (tranches)")
    symbole_unique(nuc, point("circle", "#d7191c", 4, "#ffffff", 0.4))
    reg = k.vecteur(g, "prod_registre_installations", "Registre des installations (ORE)")
    categories(reg, "filiere", [
        ("Solaire", point("circle", "#f2c12e", 2.2, "#7f6000"), "Solaire"),
        ("Eolien", point("triangle", "#4fa3d1", 3.2, "#08306b"), "Éolien"),
        ("Nucléaire", point("circle", "#d7191c", 2.2), "Nucléaire"),
        ("", point("circle", "#969696", 2.0), "Autres filières"),
    ])
    hyd = k.vecteur(g, "prod_centrales_hydrauliques", "Centrales hydrauliques", visible=False)
    symbole_unique(hyd, point("circle", "#2b83ba", 3))
    th = k.vecteur(g, "prod_centrales_thermiques", "Centrales thermiques", visible=False)
    symbole_unique(th, point("circle", "#525252", 3))

    # 4 · HTB -----------------------------------------------------------------
    g = k.groupe("4 · Réseau de transport HTB (BD TOPO, gestion RTE)")
    po = k.vecteur(g, "res_htb_postes", "Postes électriques HTB")
    symbole_unique(po, surface("#7b329499", "#4d004b", 0.4))
    etiquettes(po, "\"toponyme\"", 8, "#4d004b", italique=True)
    py = k.vecteur(g, "res_htb_pylones", "Pylônes")
    symbole_unique(py, point("square", "#252525", 1.2, "#ffffff", 0.1))
    visible_sous(py, 30000)
    li = k.vecteur(g, "res_htb_lignes", "Lignes HTB aériennes")
    categories(li, "voltage", [
        ("400 kV", ligne("#e31a1c", 1.1), "400 kV"),
        ("225 kV", ligne("#33a02c", 0.9), "225 kV"),
        ("90 kV", ligne("#ff7f00", 0.7), "90 kV"),
        ("63 kV", ligne("#b15928", 0.6), "63 kV"),
        ("", ligne("#6a3d9a", 0.5), "Autre tension"),
    ])

    # 5 · Enedis --------------------------------------------------------------
    g = k.groupe("5 · Réseau de distribution (Enedis)")
    pst = k.vecteur(g, "res_postes_hta_bt", "Postes HTA/BT")
    symbole_unique(pst, point("triangle", "#ffd700", 2.4, "#5c4400", 0.3))
    pot = k.vecteur(g, "res_poteaux_hta_bt", "Poteaux HTA/BT", visible=False)
    symbole_unique(pot, point("circle", "#5c4400", 0.8, "#5c4400", 0))
    visible_sous(pot, 15000)
    hta = k.vecteur(g, "res_hta_aerien", "HTA aérien")
    symbole_unique(hta, ligne("#1f78b4", 0.5))
    htas = k.vecteur(g, "res_hta_souterrain", "HTA souterrain")
    symbole_unique(htas, ligne("#1f78b4", 0.4, "dash"))
    bt = k.vecteur(g, "res_bt_aerien", "BT aérien", visible=False)
    symbole_unique(bt, ligne("#6a3d9a", 0.3))
    bts = k.vecteur(g, "res_bt_souterrain", "BT souterrain", visible=False)
    symbole_unique(bts, ligne("#6a3d9a", 0.25, "dot"))
    for lyr in (bt, bts):
        visible_sous(lyr, 25000)

    # 6 · environnement -----------------------------------------------------
    g = k.groupe("6 · Environnement et risques")
    icpe = k.vecteur(g, "env_icpe", "ICPE (installations classées)")
    categories(icpe, "regime", [
        ("A", point("diamond", "#b2182b", 3.0, "#ffffff"), "Autorisation"),
        ("E", point("diamond", "#ef8a62", 2.6, "#ffffff"), "Enregistrement"),
        ("", point("diamond", "#bababa", 2.0, "#ffffff"), "Autre / non renseigné"),
    ])
    cdl = k.vecteur(g, "env_conservatoire_littoral", "Conservatoire du littoral")
    symbole_unique(cdl, surface("#8c510a33", "#8c510a", 0.5))
    zps = k.vecteur(g, "env_natura2000_zps", "Natura 2000 ZPS (oiseaux)")
    symbole_unique(zps, surface("#762a83", "#762a83", 0.5, "b_diagonal"))
    sic = k.vecteur(g, "env_natura2000_zsc_sic", "Natura 2000 ZSC/SIC (habitats)")
    symbole_unique(sic, surface("#2166ac", "#2166ac", 0.5, "f_diagonal"))
    z1 = k.vecteur(g, "env_znieff1", "ZNIEFF de type 1")
    symbole_unique(z1, surface("#1a964140", "#1a9641", 0.4))
    z2 = k.vecteur(g, "env_znieff2", "ZNIEFF de type 2")
    symbole_unique(z2, surface("#a6d96a26", "#66bd63", 0.3, "solid", "dash"))
    for lyr in (cdl, zps, sic, z1, z2):
        lyr.setOpacity(0.9)

    # 7 · référentiel -------------------------------------------------------
    g = k.groupe("7 · Référentiel (BD TOPO IGN, cadastre)")
    com = k.vecteur(g, "ref_communes", "Communes")
    symbole_unique(com, surface("#00000000", "#525252", 0.4, "no", "dash"))
    etiquettes(com, "coalesce(\"nom_officiel\", \"nom\")", 8, "#525252", italique=True, echelle_max=60000)
    par = k.vecteur(g, "ref_parcelles_petit_caux", "Parcelles cadastrales (Petit-Caux)", visible=False)
    symbole_unique(par, surface("#00000000", "#bf812d", 0.15, "no"))
    visible_sous(par, 10000)
    bat = k.vecteur(g, "ref_batiments", "Bâtiments")
    symbole_unique(bat, surface("#9e9e9e", "#6e6e6e", 0.1))
    visible_sous(bat, 30000)
    rou = k.vecteur(g, "ref_routes", "Routes")
    categories(rou, "importance", [
        ("1", ligne("#636363", 1.0), "Importance 1"), ("2", ligne("#737373", 0.8), "Importance 2"),
        ("3", ligne("#858585", 0.6), "Importance 3"), ("4", ligne("#969696", 0.45), "Importance 4"),
        ("", ligne("#bdbdbd", 0.25), "Importance 5-6"),
    ])
    vf = k.vecteur(g, "ref_voies_ferrees", "Voies ferrées")
    symbole_unique(vf, ligne("#000000", 0.5, "dash"))
    ce = k.vecteur(g, "ref_cours_eau", "Cours d'eau")
    symbole_unique(ce, ligne("#4393c3", 0.6))
    se = k.vecteur(g, "ref_surfaces_eau", "Surfaces en eau")
    symbole_unique(se, surface("#92c5de", "#4393c3", 0.1))
    za = k.vecteur(g, "ref_zones_activite", "Zones d'activité ou d'intérêt", visible=False)
    symbole_unique(za, surface("#fdae6133", "#e08214", 0.2))
    hai = k.vecteur(g, "ref_haies", "Haies", visible=False)
    symbole_unique(hai, ligne("#33a02c", 0.5))
    veg = k.vecteur(g, "ref_vegetation", "Végétation", visible=False)
    symbole_unique(veg, surface("#b8e18680", "#4d9221", 0.1))

    # 8 · tables de production ----------------------------------------------------------
    g = k.groupe("8 · Tables de production (sans géométrie)")
    for t, a in [("tab_indisponibilites_penly", "Indisponibilités Penly (en cours)"),
                 ("tab_indisponibilites_penly_hist", "Indisponibilités Penly (historique depuis 2015)"),
                 ("tab_historique_productions", "Productions nationales depuis 1948"),
                 ("tab_disponibilite_parc_nucleaire", "Disponibilité du parc nucléaire"),
                 ("tab_seuils_rejets_thermiques", "Seuils de rejets thermiques")]:
        k.vecteur(g, t, a)

    # 9 · fonds de plan -----------------------------------------------------
    g = k.groupe("9 · Fonds de plan IGN (Géoplateforme)")
    k.xyz(g, "Cadastre (PCI)", "CADASTRALPARCELS.PARCELLAIRE_EXPRESS", "PCI%20vecteur", "image/png", visible=False)
    k.xyz(g, "Plan IGN v2", "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", "normal", "image/png", opacite=0.75)
    k.xyz(g, "Ombrage du relief", "ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW", "estompage_grayscale", "image/png", visible=False, zmax=18)
    k.xyz(g, "Orthophotographie", "ORTHOIMAGERY.ORTHOPHOTOS", "normal", "image/jpeg", visible=False)

    projet.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(EMPRISE_5KM, L93))
    mise_en_page(projet, k)
    return k


def mise_en_page(projet, k):
    """Plan de situation A3 paysage."""
    gest = projet.layoutManager()
    for old in [l for l in gest.printLayouts() if l.name() == "Plan de situation A3"]:
        gest.removeLayout(old)
    mp = QgsPrintLayout(projet)
    mp.initializeDefaults()
    mp.setName("Plan de situation A3")
    page = mp.pageCollection().page(0)
    page.setPageSize("A3", page.Landscape)

    carte = QgsLayoutItemMap(mp)
    carte.attemptMove(QgsLayoutPoint(8, 24, QgsUnitTypes.LayoutMillimeters))
    carte.attemptResize(QgsLayoutSize(312, 265, QgsUnitTypes.LayoutMillimeters))
    carte.setCrs(L93)
    carte.setFrameEnabled(True)
    mp.addLayoutItem(carte)
    carte.zoomToExtent(EMPRISE_5KM)

    titre = QgsLayoutItemLabel(mp)
    titre.setText("Chantier de Penly : plan de situation et contraintes du site")
    fmt = QgsTextFormat()
    fmt.setFont(QFont(POLICE, 20, QFont.Bold))
    fmt.setSize(20)
    titre.setTextFormat(fmt)
    titre.attemptMove(QgsLayoutPoint(8, 6, QgsUnitTypes.LayoutMillimeters))
    titre.attemptResize(QgsLayoutSize(400, 14, QgsUnitTypes.LayoutMillimeters))
    mp.addLayoutItem(titre)

    leg = QgsLayoutItemLegend(mp)
    leg.setTitle("Légende")
    leg.setLinkedMap(carte)
    leg.setAutoUpdateModel(False)
    racine = leg.model().rootGroup()
    racine.removeAllChildren()
    for t in ["zon_cnpe_penly", "zon_cercles", "prod_registre_installations", "res_htb_postes", "res_htb_lignes",
              "res_postes_hta_bt", "res_hta_aerien", "res_hta_souterrain", "env_icpe", "env_conservatoire_littoral",
              "env_natura2000_zps", "env_natura2000_zsc_sic", "env_znieff1", "env_znieff2", "ref_voies_ferrees", "ref_cours_eau"]:
        racine.addLayer(k.c[t])
    leg.setLegendFilterByMapEnabled(True)
    leg.setSymbolHeight(3.5)
    leg.setSymbolWidth(6)
    leg.attemptMove(QgsLayoutPoint(326, 24, QgsUnitTypes.LayoutMillimeters))
    mp.addLayoutItem(leg)

    eb = QgsLayoutItemScaleBar(mp)
    eb.setStyle("Single Box")
    eb.setLinkedMap(carte)
    eb.applyDefaultSize()
    eb.setUnits(QgsUnitTypes.DistanceKilometers)
    eb.setUnitLabel("km")
    eb.setNumberOfSegments(4)
    eb.setNumberOfSegmentsLeft(0)
    eb.setUnitsPerSegment(1)
    eb.setBackgroundEnabled(True)
    eb.attemptMove(QgsLayoutPoint(12, 274, QgsUnitTypes.LayoutMillimeters))
    mp.addLayoutItem(eb)

    nord = QgsLayoutItemPicture(mp)
    nord.setPicturePath(QgsSymbolLayerUtils.svgSymbolNameToPath("arrows/NorthArrow_02.svg", projet.pathResolver()))
    nord.attemptMove(QgsLayoutPoint(302, 28, QgsUnitTypes.LayoutMillimeters))
    nord.attemptResize(QgsLayoutSize(14, 14, QgsUnitTypes.LayoutMillimeters))
    mp.addLayoutItem(nord)

    src = QgsLayoutItemLabel(mp)
    src.setText(
        "Sources (données ouvertes, Licence Ouverte Etalab 2.0) : EDF (opendata.edf.fr), Enedis (opendata.enedis.fr), "
        "Agence ORE, IGN BD TOPO et Plan IGN (Géoplateforme), PatriNat/INPN, Géorisques (ICPE), DGFiP/Etalab (cadastre).\n"
        "Projection : RGF93 / Lambert-93. Réalisation : [% @user_full_name %], [% format_date(now(), 'dd/MM/yyyy') %]. "
        "Document de démonstration : les emprises du futur chantier ne sont pas représentées."
    )
    f2 = QgsTextFormat()
    f2.setFont(QFont(POLICE, 7))
    f2.setSize(7)
    src.setTextFormat(f2)
    src.attemptMove(QgsLayoutPoint(326, 252, QgsUnitTypes.LayoutMillimeters))
    src.attemptResize(QgsLayoutSize(88, 38, QgsUnitTypes.LayoutMillimeters))
    mp.addLayoutItem(src)

    gest.addLayout(mp)
    return mp


def exporter(projet, dossier):
    mp = projet.layoutManager().layoutByName("Plan de situation A3")
    ex = QgsLayoutExporter(mp)
    s = QgsLayoutExporter.ImageExportSettings()
    s.dpi = 120
    r1 = ex.exportToImage(str(Path(dossier) / "plan_situation_A3.png"), s)
    r2 = ex.exportToPdf(str(Path(dossier) / "plan_situation_A3.pdf"), QgsLayoutExporter.PdfExportSettings())
    return r1, r2


if __name__ == "__main__":
    app = QgsApplication([], False)
    app.initQgis()
    p = QgsProject.instance()
    construire(p)
    p.write(QGZ)
    print("Projet écrit :", QGZ, "| export (0 = ok) :", exporter(p, RACINE / "06_exports"), flush=True)
    # exitQgis() peut bloquer après des accès réseau (tuiles IGN) : sortie directe, tout est déjà écrit
    sys.stdout.flush()
    os._exit(0)
