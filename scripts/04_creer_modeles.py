"""
04_creer_modeles.py : Crée les modèles du Modeleur graphique (.model3) qui reprennent les traitements du projet,
puis les teste sur les données du projet.

  03_qgis/modeles/01_integrer_couche_open_data.model3     URL API/WFS -> téléchargement -> Lambert-93 -> multi-géométries
  03_qgis/modeles/02_zonages_etude.model3                 site -> cercles de 2 / 5 / 10 / 20 km (rayons paramétrables)
  03_qgis/modeles/03_contraintes_emprise_chantier.model3  emprise -> conflits lignes aériennes, réseaux souterrains, zones protégées
  03_qgis/modeles/04_conversion_cao_vers_pic.model3       DXF -> calques PIC_ZONE_* -> polygones -> schéma pic_zone

Les modèles s'ouvrent dans QGIS : Boîte à outils de traitements > icône « Modèles » > « Ajouter un modèle à la boîte à outils »,
ou Traitement > Modeleur graphique > Ouvrir.

Usage (PowerShell, depuis le dossier du projet) :
    & "C:\\Program Files\\QGIS 3.34.12\\bin\\python-qgis-ltr.bat" scripts\\04_creer_modeles.py
"""
import re
import sys
import unicodedata
from pathlib import Path

from qgis.core import (
    QgsApplication, QgsCoordinateReferenceSystem, QgsProcessing, QgsProcessingModelAlgorithm,
    QgsProcessingModelChildAlgorithm, QgsProcessingModelChildParameterSource as Src, QgsProcessingModelOutput,
    QgsProcessingModelParameter, QgsProcessingParameterCrs, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterMultipleLayers, QgsProcessingParameterNumber, QgsProcessingParameterString,
    QgsProcessingModelComment,
)
from qgis.PyQt.QtCore import QPointF

RACINE = Path(__file__).resolve().parent.parent
MODELES = RACINE / "03_qgis" / "modeles"
GPKG = (RACINE / "02_donnees" / "penly_sig.gpkg").as_posix()
DXF = RACINE / "04_cao" / "exemple_fictif_PIC.dxf"
AUTEUR = "SIG chantier Penly"


class Modele:
    def __init__(self, nom, aide):
        self.m = QgsProcessingModelAlgorithm(nom, "SIG chantier Penly")
        self.m.setHelpContent({"ALG_DESC": aide, "ALG_CREATOR": AUTEUR, "ALG_VERSION": "1.0"})

    def entree(self, param, x, y):
        mp = QgsProcessingModelParameter(param.name())
        mp.setPosition(QPointF(x, y))
        mp.setDescription(param.description())
        self.m.addModelParameter(param, mp)

    def etape(self, cid, alg, desc, params, x, y, sorties=None, commentaire=None):
        c = QgsProcessingModelChildAlgorithm(alg)
        c.setChildId(cid)
        c.setDescription(desc)
        c.setPosition(QPointF(x, y))
        for k, v in params.items():
            c.addParameterSources(k, v if isinstance(v, list) else [v])
        if sorties:
            outs = {}
            for nom_sortie, libelle in sorties.items():
                ident = re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKD", libelle).encode("ascii", "ignore").decode().lower()).strip("_")
                o = QgsProcessingModelOutput(ident, libelle)
                o.setChildId(cid)
                o.setChildOutputName(nom_sortie)
                o.setPosition(QPointF(x + 190, y + 70))
                outs[ident] = o
            c.setModelOutputs(outs)
        if commentaire:
            com = QgsProcessingModelComment(commentaire)
            com.setPosition(QPointF(x + 200, y - 50))
            c.setComment(com)
        self.m.addChildAlgorithm(c)

    def enregistrer(self, fichier):
        MODELES.mkdir(parents=True, exist_ok=True)
        chemin = MODELES / fichier
        self.m.updateDestinationParameters()
        assert self.m.toFile(str(chemin)), chemin
        return chemin, self.m


S, P, C = Src.fromStaticValue, Src.fromModelParameter, Src.fromChildOutput
L93 = "EPSG:2154"


def modele_integration():
    k = Modele("01 · Intégrer une couche open data (API/WFS -> Lambert-93)",
               "Télécharge une couche GeoJSON depuis une API (Data Fair des portails open data, WFS Géoplateforme...), "
               "la reprojette en RGF93 / Lambert-93 et force des géométries multiples, prête à être enregistrée dans "
               "le GeoPackage du projet. Équivalent graphique des scripts 01 et 02 pour une couche.")
    k.entree(QgsProcessingParameterString(
        "url", "URL de la couche (GeoJSON)",
        defaultValue="https://opendata.enedis.fr/data-fair/api/v1/datasets/poste-electrique/lines"
                     "?bbox=1.18,49.96,1.24,49.99&format=geojson&size=10000"), 60, 60)
    k.etape("telecharger", "native:filedownloader", "Télécharger la couche",
            {"URL": P("url")}, 300, 60)
    k.etape("reprojeter", "native:reprojectlayer", "Reprojeter en Lambert-93",
            {"INPUT": C("telecharger", "OUTPUT"), "TARGET_CRS": S(L93)}, 300, 170)
    k.etape("multi", "native:promotetomulti", "Géométries multiples",
            {"INPUT": C("reprojeter", "OUTPUT")}, 300, 280, sorties={"OUTPUT": "Couche Lambert-93"})
    return k.enregistrer("01_integrer_couche_open_data.model3")


def modele_zonages():
    k = Modele("02 · Zonages d'étude autour d'un site",
               "Crée des cercles concentriques autour d'un site ponctuel (par défaut 2, 5, 10 et 20 km : abords du "
               "chantier, zone rapprochée, zone élargie, rayon du PPI) en Lambert-93, avec le champ rayon_km. "
               "Équivalent graphique de la fonction zonages() du script 02.")
    k.entree(QgsProcessingParameterFeatureSource("site", "Site (point)", [QgsProcessing.TypeVectorPoint]), 60, 60)
    for i, (d, y) in enumerate([(2000, 140), (5000, 200), (10000, 260), (20000, 320)], 1):
        k.entree(QgsProcessingParameterNumber(f"rayon_{i}", f"Rayon {i} (m)", QgsProcessingParameterNumber.Double, d, minValue=0), 60, y)
    k.etape("reprojeter", "native:reprojectlayer", "Reprojeter en Lambert-93",
            {"INPUT": P("site"), "TARGET_CRS": S(L93)}, 320, 60)
    for i in range(1, 5):
        k.etape(f"tampon_{i}", "native:buffer", f"Tampon rayon {i}",
                {"INPUT": C("reprojeter", "OUTPUT"), "DISTANCE": P(f"rayon_{i}"), "SEGMENTS": S(64),
                 "END_CAP_STYLE": S(0), "JOIN_STYLE": S(0), "MITER_LIMIT": S(2), "DISSOLVE": S(False)},
                320 + (i - 1) * 40, 130 + i * 60)
    k.etape("fusion", "native:mergevectorlayers", "Fusionner les cercles",
            {"LAYERS": [C(f"tampon_{i}", "OUTPUT") for i in range(1, 5)], "CRS": S(L93)}, 600, 300)
    k.etape("rayon", "native:fieldcalculator", "Calculer rayon_km",
            {"INPUT": C("fusion", "OUTPUT"), "FIELD_NAME": S("rayon_km"), "FIELD_TYPE": S(0), "FIELD_LENGTH": S(10),
             "FIELD_PRECISION": S(1), "FORMULA": S("round(sqrt($area / pi()) / 1000, 1)")},
            600, 410, sorties={"OUTPUT": "Cercles d'étude"},
            commentaire="rayon retrouvé depuis la surface du cercle")
    return k.enregistrer("02_zonages_etude.model3")


def modele_contraintes():
    k = Modele("03 · Contraintes d'une emprise de chantier",
               "Croise une emprise de chantier (zone du PIC, cercle d'étude...) avec : (1) les lignes électriques "
               "aériennes HTB/HTA élargies d'une distance de vigilance (engins de levage), (2) les réseaux souterrains "
               "à déclarer (DT-DICT), (3) les zones naturelles protégées (ZNIEFF, Natura 2000, Conservatoire du "
               "littoral). Chaque résultat porte le nom de la couche d'origine (champ « layer ») et sa surface.")
    k.entree(QgsProcessingParameterFeatureSource("emprise", "Emprise de chantier", [QgsProcessing.TypeVectorPolygon]), 60, 60)
    k.entree(QgsProcessingParameterMultipleLayers("lignes_aeriennes", "Lignes électriques aériennes (HTB, HTA, BT)",
                                                  QgsProcessing.TypeVectorLine), 60, 150)
    k.entree(QgsProcessingParameterNumber("distance", "Distance de vigilance autour des lignes aériennes (m)",
                                          QgsProcessingParameterNumber.Double, 30, minValue=0), 60, 210)
    k.entree(QgsProcessingParameterMultipleLayers("reseaux_souterrains", "Réseaux souterrains (HTA, BT...)",
                                                  QgsProcessing.TypeVectorLine), 60, 320)
    k.entree(QgsProcessingParameterMultipleLayers("zones_protegees", "Zones naturelles protégées",
                                                  QgsProcessing.TypeVectorPolygon), 60, 440)
    # lignes aériennes
    k.etape("fusion_aer", "native:mergevectorlayers", "Fusionner les lignes aériennes",
            {"LAYERS": P("lignes_aeriennes"), "CRS": S(L93)}, 340, 150)
    k.etape("tampon_aer", "native:buffer", "Tampon de vigilance",
            {"INPUT": C("fusion_aer", "OUTPUT"), "DISTANCE": P("distance"), "SEGMENTS": S(8), "END_CAP_STYLE": S(0),
             "JOIN_STYLE": S(0), "MITER_LIMIT": S(2), "DISSOLVE": S(False)}, 340, 230)
    k.etape("conf_aer", "native:intersection", "Emprise x lignes aériennes",
            {"INPUT": P("emprise"), "OVERLAY": C("tampon_aer", "OUTPUT"), "INPUT_FIELDS": S([]),
             "OVERLAY_FIELDS": S([]), "OVERLAY_FIELDS_PREFIX": S("")}, 600, 190)
    k.etape("surf_aer", "native:fieldcalculator", "Surface concernée",
            {"INPUT": C("conf_aer", "OUTPUT"), "FIELD_NAME": S("surface_m2"), "FIELD_TYPE": S(0), "FIELD_LENGTH": S(12),
             "FIELD_PRECISION": S(1), "FORMULA": S("$area")}, 860, 190,
            sorties={"OUTPUT": "Emprise sous lignes aériennes"})
    # réseaux souterrains
    k.etape("fusion_sout", "native:mergevectorlayers", "Fusionner les réseaux souterrains",
            {"LAYERS": P("reseaux_souterrains"), "CRS": S(L93)}, 340, 330)
    k.etape("conf_sout", "native:clip", "Découper par l'emprise",
            {"INPUT": C("fusion_sout", "OUTPUT"), "OVERLAY": P("emprise")}, 600, 330)
    k.etape("long_sout", "native:fieldcalculator", "Longueur concernée",
            {"INPUT": C("conf_sout", "OUTPUT"), "FIELD_NAME": S("longueur_m"), "FIELD_TYPE": S(0), "FIELD_LENGTH": S(12),
             "FIELD_PRECISION": S(1), "FORMULA": S("$length")}, 860, 330,
            sorties={"OUTPUT": "Réseaux souterrains dans l'emprise (DT-DICT)"})
    # zones protégées
    k.etape("fusion_env", "native:mergevectorlayers", "Fusionner les zones protégées",
            {"LAYERS": P("zones_protegees"), "CRS": S(L93)}, 340, 450)
    k.etape("conf_env", "native:intersection", "Emprise x zones protégées",
            {"INPUT": P("emprise"), "OVERLAY": C("fusion_env", "OUTPUT"), "INPUT_FIELDS": S([]),
             "OVERLAY_FIELDS": S([]), "OVERLAY_FIELDS_PREFIX": S("")}, 600, 450)
    k.etape("surf_env", "native:fieldcalculator", "Surface concernée",
            {"INPUT": C("conf_env", "OUTPUT"), "FIELD_NAME": S("surface_m2"), "FIELD_TYPE": S(0), "FIELD_LENGTH": S(12),
             "FIELD_PRECISION": S(1), "FORMULA": S("$area")}, 860, 450,
            sorties={"OUTPUT": "Emprise en zone protégée"})
    return k.enregistrer("03_contraintes_emprise_chantier.model3")


def modele_cao():
    k = Modele("04 · Conversion CAO (DXF) -> zones du PIC",
               "Intègre un plan CAO (DXF exporté d'AutoCAD/MicroStation) dans le modèle de données du PIC. "
               "Convention : les polylignes fermées des zones sont dessinées sur des calques PIC_ZONE_<TYPE> "
               "(ex. PIC_ZONE_BASE_VIE, PIC_ZONE_STOCKAGE) ; le suffixe donne le type de zone. "
               "Étapes : système de coordonnées du plan, filtre des calques, polylignes -> polygones, correction des "
               "géométries, Lambert-93, puis restructuration au schéma de la couche pic_zone (source = CAO).")
    k.entree(QgsProcessingParameterFeatureSource("dxf", "Plan CAO (DXF)", [QgsProcessing.TypeVectorLine]), 60, 60)
    k.entree(QgsProcessingParameterCrs("crs_cao", "Système de coordonnées du plan CAO", L93), 60, 130)
    k.entree(QgsProcessingParameterString("prefixe", "Préfixe des calques de zones", "PIC_ZONE_"), 60, 200)
    k.entree(QgsProcessingParameterString("ref_document", "Référence du plan (n° de plan, indice)", "PLAN-EXEMPLE-A"), 60, 270)
    k.etape("crs", "native:assignprojection", "Affecter le système du plan",
            {"INPUT": P("dxf"), "CRS": P("crs_cao")}, 320, 60)
    k.etape("filtre", "native:extractbyexpression", "Garder les calques de zones",
            {"INPUT": C("crs", "OUTPUT"),
             "EXPRESSION": Src.fromExpression("'\"Layer\" LIKE ' || '''' || @prefixe || '%' || ''''")}, 320, 150,
            commentaire="filtre construit depuis le paramètre « prefixe »")
    k.etape("polygones", "qgis:linestopolygons", "Polylignes fermées -> polygones",
            {"INPUT": C("filtre", "OUTPUT")}, 320, 240)
    k.etape("corriger", "native:fixgeometries", "Corriger les géométries",
            {"INPUT": C("polygones", "OUTPUT")}, 320, 330)
    k.etape("l93", "native:reprojectlayer", "Reprojeter en Lambert-93",
            {"INPUT": C("corriger", "OUTPUT"), "TARGET_CRS": S(L93)}, 320, 420)
    k.etape("type", "native:fieldcalculator", "Type de zone depuis le calque",
            {"INPUT": C("l93", "OUTPUT"), "FIELD_NAME": S("type_zone_cao"), "FIELD_TYPE": S(2), "FIELD_LENGTH": S(50),
             "FIELD_PRECISION": S(0),
             "FORMULA": Src.fromExpression("'lower(regexp_replace(\"Layer\", ''^' || @prefixe || ''', ''''))'")},
            600, 420)
    k.etape("ref", "native:fieldcalculator", "Référence du plan",
            {"INPUT": C("type", "OUTPUT"), "FIELD_NAME": S("ref_plan"), "FIELD_TYPE": S(2), "FIELD_LENGTH": S(100),
             "FIELD_PRECISION": S(0), "FORMULA": Src.fromExpression("'''' || @ref_document || ''''")}, 600, 510)
    t = {"chaine": 10, "date": 14, "dateheure": 16}
    mapping = [
        {"name": "code_zone", "type": t["chaine"], "length": 0, "precision": 0, "expression": "\"EntityHandle\""},
        {"name": "type_zone", "type": t["chaine"], "length": 0, "precision": 0, "expression": "\"type_zone_cao\""},
        {"name": "libelle", "type": t["chaine"], "length": 0, "precision": 0, "expression": "\"Layer\""},
        {"name": "lot", "type": t["chaine"], "length": 0, "precision": 0, "expression": "NULL"},
        {"name": "phase", "type": t["chaine"], "length": 0, "precision": 0, "expression": "NULL"},
        {"name": "statut", "type": t["chaine"], "length": 0, "precision": 0, "expression": "'projet'"},
        {"name": "date_debut", "type": t["date"], "length": 0, "precision": 0, "expression": "NULL"},
        {"name": "date_fin", "type": t["date"], "length": 0, "precision": 0, "expression": "NULL"},
        {"name": "source", "type": t["chaine"], "length": 0, "precision": 0, "expression": "'CAO'"},
        {"name": "ref_document", "type": t["chaine"], "length": 0, "precision": 0, "expression": "\"ref_plan\""},
        {"name": "auteur", "type": t["chaine"], "length": 0, "precision": 0, "expression": "@user_full_name"},
        {"name": "date_maj", "type": t["dateheure"], "length": 0, "precision": 0, "expression": "now()"},
        {"name": "commentaire", "type": t["chaine"], "length": 0, "precision": 0, "expression": "'Converti depuis DXF'"},
    ]
    k.etape("schema", "native:refactorfields", "Restructurer au schéma pic_zone",
            {"INPUT": C("ref", "OUTPUT"), "FIELDS_MAPPING": S(mapping)}, 860, 510,
            sorties={"OUTPUT": "Zones PIC issues de la CAO"},
            commentaire="à coller ensuite dans pic_zone (pic_chantier.gpkg)")
    return k.enregistrer("04_conversion_cao_vers_pic.model3")


def dxf_exemple():
    """Petit plan DXF FICTIF (4 zones + 1 accès) pour tester le modèle 04. Ce n'est pas l'implantation réelle du chantier."""
    from osgeo import ogr, osr
    ogr.UseExceptions()
    DXF.parent.mkdir(exist_ok=True)
    if DXF.exists():
        DXF.unlink()
    ds = ogr.GetDriverByName("DXF").CreateDataSource(str(DXF))
    lyr = ds.CreateLayer("entities", osr.SpatialReference(), ogr.wkbLineString)
    x0, y0 = 572150, 6987350  # plateau au sud-est du CNPE (positions fictives)
    rect = lambda x, y, w, h: f"LINESTRING ({x} {y}, {x + w} {y}, {x + w} {y + h}, {x} {y + h}, {x} {y})"
    objets = [
        ("PIC_ZONE_BASE_VIE", rect(x0, y0, 180, 90)),
        ("PIC_ZONE_STOCKAGE", rect(x0 + 220, y0, 160, 140)),
        ("PIC_ZONE_PREFABRICATION", rect(x0 + 220, y0 + 170, 120, 80)),
        ("PIC_ZONE_PARKING", rect(x0, y0 + 120, 150, 60)),
        ("PIC_ACCES", f"LINESTRING ({x0 - 60} {y0 - 40}, {x0 + 200} {y0 - 20}, {x0 + 420} {y0 - 30})"),
        ("CARTOUCHE", rect(x0 - 100, y0 - 100, 650, 450)),
    ]
    for calque, wkt in objets:
        f = ogr.Feature(lyr.GetLayerDefn())
        f.SetField("Layer", calque)
        f.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        lyr.CreateFeature(f)
    ds = None
    return DXF


def initialiser_traitements():
    """Le registre doit connaître les algorithmes avant de construire les modèles (paramètres de sortie)."""
    sys.path.append(str(Path(QgsApplication.prefixPath()) / "python" / "plugins"))
    from processing.core.Processing import Processing
    from qgis.analysis import QgsNativeAlgorithms
    Processing.initialize()
    if not QgsApplication.processingRegistry().providerById("native"):
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())


def tester(modeles):
    import processing

    def compte(res):
        out = {}
        for k, v in res.items():
            if hasattr(v, "featureCount"):
                out[k] = v.featureCount()
            elif isinstance(v, str) and v:
                from qgis.core import QgsVectorLayer
                lyr = QgsVectorLayer(v, "t", "ogr")
                out[k] = lyr.featureCount() if lyr.isValid() else v
        return out

    def run(m, params, champs=None):
        for p in m.destinationParameterDefinitions():
            params[p.name()] = "TEMPORARY_OUTPUT"
        res = processing.run(m, params)
        if champs:
            for v in res.values():
                if hasattr(v, "getFeatures"):
                    print("     ", [[f[c] for c in champs] for f in v.getFeatures()])
        return compte(res)

    m1, m2, m3, m4 = [m for _, m in modeles]
    print("  01 intégration :", run(m1, {"url": m1.parameterDefinition("url").defaultValue()}))
    print("  02 zonages     :", run(m2, {"site": f"{GPKG}|layername=zon_cnpe_penly",
                                         "rayon_1": 2000, "rayon_2": 5000, "rayon_3": 10000, "rayon_4": 20000}, ["rayon_km"]))
    print("  03 contraintes :", run(m3, {
        "emprise": f"{GPKG}|layername=zon_cercles|subset=\"rayon_km\" = 2",
        "lignes_aeriennes": [f"{GPKG}|layername=res_htb_lignes", f"{GPKG}|layername=res_hta_aerien",
                             f"{GPKG}|layername=res_bt_aerien"],
        "distance": 30,
        "reseaux_souterrains": [f"{GPKG}|layername=res_hta_souterrain", f"{GPKG}|layername=res_bt_souterrain"],
        "zones_protegees": [f"{GPKG}|layername=env_znieff1", f"{GPKG}|layername=env_znieff2",
                            f"{GPKG}|layername=env_natura2000_zsc_sic", f"{GPKG}|layername=env_natura2000_zps",
                            f"{GPKG}|layername=env_conservatoire_littoral"]}))
    print("  04 CAO -> PIC  :", run(m4, {"dxf": f"{DXF.as_posix()}|layername=entities", "crs_cao": L93,
                                         "prefixe": "PIC_ZONE_", "ref_document": "PLAN-EXEMPLE-A"},
                                         ["type_zone", "source", "ref_document", "statut"]))


if __name__ == "__main__":
    app = QgsApplication([], False)
    app.initQgis()
    initialiser_traitements()
    modeles = [modele_integration(), modele_zonages(), modele_contraintes(), modele_cao()]
    for chemin, _ in modeles:
        print("modèle :", chemin.relative_to(RACINE))
    print("DXF d'exemple :", dxf_exemple().relative_to(RACINE))
    if "--sans-test" not in sys.argv:
        print("Tests sur les données du projet (nombre d'objets en sortie) :")
        tester(modeles)
    app.exitQgis()
