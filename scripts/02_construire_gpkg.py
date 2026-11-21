"""
02_construire_gpkg.py : Assemble les données brutes dans deux GeoPackages en Lambert-93 (EPSG:2154).

  02_donnees/sig_chantier.gpkg     données de référence (réseaux, production, environnement, zonages, tables de production)
  02_donnees/pic_chantier.gpkg  modèle vide du Plan d'Installation de Chantier (zones, accès, équipements)

Préfixes des couches :
  zon_   zonages d'étude (CNPE, cercles 2/5/10/20 km)
  prod_  production d'électricité
  res_   réseaux électriques (HTB IGN/RTE, HTA/BT Enedis)
  env_   environnement et risques (ZNIEFF, Natura 2000, Conservatoire du littoral, ICPE)
  ref_   référentiel topographique et foncier (BD TOPO, cadastre)
  tab_   tables de production (source EDF, sans géométrie)

Usage (PowerShell, depuis le dossier du projet) : avec le Python de QGIS :
    & "C:\\Program Files\\QGIS 3.34.12\\bin\\python-qgis-ltr.bat" scripts\\02_construire_gpkg.py
"""
from pathlib import Path

from osgeo import gdal, ogr, osr

gdal.UseExceptions()
ogr.UseExceptions()

RACINE = Path(__file__).resolve().parent.parent
BRUT = RACINE / "01_donnees_brutes"
SORTIE = RACINE / "02_donnees"
GPKG = SORTIE / "sig_chantier.gpkg"
PIC = SORTIE / "pic_chantier.gpkg"

PENLY_LAT, PENLY_LON = 49.976144, 1.210236

# couche de sortie : [fichiers sources] (plusieurs sources = fusion)
COUCHES = {
    # production
    "prod_centrales_nucleaires": ["edf/centrales_nucleaires.geojson"],
    "prod_centrales_hydrauliques": ["edf/centrales_hydrauliques.geojson"],
    "prod_centrales_thermiques": ["edf/centrales_thermiques.geojson"],
    "prod_registre_installations": ["ore/registre_installations_production_stockage.geojson"],
    # réseaux
    "res_htb_lignes": ["ign/bdtopo_ligne_electrique.geojson"],
    "res_htb_postes": ["ign/bdtopo_poste_de_transformation.geojson"],
    "res_htb_pylones": ["ign/bdtopo_pylone.geojson"],
    "res_hta_aerien": ["enedis/enedis_hta_aerien.geojson"],
    "res_hta_souterrain": ["enedis/enedis_hta_souterrain.geojson"],
    "res_bt_aerien": ["enedis/enedis_bt_aerien.geojson"],
    "res_bt_souterrain": ["enedis/enedis_bt_souterrain.geojson"],
    "res_postes_hta_bt": ["enedis/enedis_postes_hta_bt.geojson"],
    "res_poteaux_hta_bt": ["enedis/enedis_poteaux_hta_bt.geojson"],
    # environnement
    "env_znieff1": ["patrinat/znieff1.geojson", "patrinat/znieff1_mer.geojson"],
    "env_znieff2": ["patrinat/znieff2.geojson", "patrinat/znieff2_mer.geojson"],
    "env_natura2000_zsc_sic": ["patrinat/sic.geojson"],
    "env_natura2000_zps": ["patrinat/zps.geojson"],
    "env_conservatoire_littoral": ["patrinat/cdl.geojson"],
    "env_icpe": ["icpe/icpe.geojson"],
    # référentiel
    "ref_communes": ["ign/bdtopo_commune.geojson"],
    "ref_routes": ["ign/bdtopo_troncon_de_route.geojson"],
    "ref_voies_ferrees": ["ign/bdtopo_troncon_de_voie_ferree.geojson"],
    "ref_cours_eau": ["ign/bdtopo_cours_d_eau.geojson"],
    "ref_surfaces_eau": ["ign/bdtopo_surface_hydrographique.geojson"],
    "ref_zones_activite": ["ign/bdtopo_zone_d_activite_ou_d_interet.geojson"],
    "ref_batiments": ["ign/bdtopo_batiment.geojson"],
    "ref_vegetation": ["ign/bdtopo_zone_de_vegetation.geojson"],
    "ref_haies": ["ign/bdtopo_haie.geojson"],
    "ref_parcelles_petit_caux": ["cadastre/parcelles_76618_petit_caux.geojson"],
}

TABLES = {
    "tab_indisponibilites": "edf/indisponibilites.csv",
    "tab_indisponibilites_hist": "edf/indisponibilites_historique_2015.csv",
    "tab_seuils_rejets_thermiques": "edf/seuils_rejets_thermiques.csv",
    "tab_historique_productions": "edf/historique_productions_1948.csv",
    "tab_disponibilite_parc_nucleaire": "edf/disponibilite_parc_nucleaire.csv",
}


def lambert93():
    s = osr.SpatialReference()
    s.ImportFromEPSG(2154)
    s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return s


def compter(nom):
    ds = ogr.Open(str(GPKG))
    lyr = ds.GetLayerByName(nom)
    n = lyr.GetFeatureCount() if lyr else 0
    ds = None
    return n


def charger_couches():
    for nom, sources in COUCHES.items():
        n = 0
        for i, src in enumerate(sources):
            chemin = BRUT / src
            if not chemin.exists():
                print(f"  -- absent : {src}")
                continue
            out = gdal.VectorTranslate(
                str(GPKG), str(chemin), format="GPKG",
                accessMode="append" if (GPKG.exists() and i > 0) else ("update" if GPKG.exists() else None),
                layerName=nom, dstSRS="EPSG:2154", reproject=True,
                geometryType="PROMOTE_TO_MULTI", addFields=i > 0,
                layerCreationOptions=["SPATIAL_INDEX=YES"] if i == 0 else None,
            )
            out = None  # ferme et écrit sur disque
            n = compter(nom)
        print(f"  {nom:<34} {n:>7}")


def charger_tables():
    for nom, src in TABLES.items():
        out = gdal.VectorTranslate(
            str(GPKG), str(BRUT / src), format="GPKG", accessMode="update", layerName=nom,
            options=["-oo", "AUTODETECT_TYPE=YES", "-oo", "SEPARATOR=SEMICOLON", "-oo", "AUTODETECT_WIDTH=YES"],
        )
        out = None
        n = compter(nom)
        print(f"  {nom:<34} {n:>7}")


def zonages():
    """CNPE de Penly (point publié par EDF) et cercles de 2, 5, 10 et 20 km."""
    wgs = osr.SpatialReference()
    wgs.ImportFromEPSG(4326)
    wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    l93 = lambert93()
    tr = osr.CoordinateTransformation(wgs, l93)
    pt = ogr.Geometry(ogr.wkbPoint)
    pt.AddPoint_2D(PENLY_LON, PENLY_LAT)
    pt.Transform(tr)

    ds = ogr.Open(str(GPKG), 1)
    for nom in ("zon_cnpe", "zon_cercles"):
        if ds.GetLayerByName(nom):
            ds.DeleteLayer(nom)

    lyr = ds.CreateLayer("zon_cnpe", l93, ogr.wkbPoint)
    for champ in ("nom", "exploitant", "source"):
        lyr.CreateField(ogr.FieldDefn(champ, ogr.OFTString))
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetField("nom", "CNPE de Penly (tranches 1-2 en service, tranches 3-4 en projet)")
    f.SetField("exploitant", "EDF")
    f.SetField("source", "opendata.edf.fr, centrales de production nucléaire")
    f.SetGeometry(pt)
    lyr.CreateFeature(f)

    lyr = ds.CreateLayer("zon_cercles", l93, ogr.wkbMultiPolygon)
    lyr.CreateField(ogr.FieldDefn("rayon_km", ogr.OFTInteger))
    lyr.CreateField(ogr.FieldDefn("libelle", ogr.OFTString))
    libelles = {
        2: "2 km : abords immédiats du chantier",
        5: "5 km : zone d'étude rapprochée",
        10: "10 km : zone d'étude élargie",
        20: "20 km : rayon du PPI (plan particulier d'intervention)",
    }
    for r in (20, 10, 5, 2):
        f = ogr.Feature(lyr.GetLayerDefn())
        f.SetField("rayon_km", r)
        f.SetField("libelle", libelles[r])
        f.SetGeometry(ogr.ForceToMultiPolygon(pt.Buffer(r * 1000, 64)))
        lyr.CreateFeature(f)
    ds = None
    print("  zon_cnpe / zon_cercles          ok")


def modele_pic():
    """Modèle vide du Plan d'Installation de Chantier : à remplir dans QGIS (listes de valeurs dans le projet)."""
    if PIC.exists():
        print(f"  {PIC.name} existe déjà : conservé tel quel (pas d'écrasement des saisies)")
        return
    drv = ogr.GetDriverByName("GPKG")
    ds = drv.CreateDataSource(str(PIC))
    l93 = lambert93()
    communs = [
        ("lot", ogr.OFTString), ("phase", ogr.OFTString), ("statut", ogr.OFTString),
        ("date_debut", ogr.OFTDate), ("date_fin", ogr.OFTDate),
        ("source", ogr.OFTString), ("ref_document", ogr.OFTString),
        ("auteur", ogr.OFTString), ("date_maj", ogr.OFTDateTime), ("commentaire", ogr.OFTString),
    ]
    defs = {
        "pic_zone": (ogr.wkbMultiPolygon, [("code_zone", ogr.OFTString), ("type_zone", ogr.OFTString), ("libelle", ogr.OFTString)]),
        "pic_acces": (ogr.wkbMultiLineString, [("type_acces", ogr.OFTString), ("sens", ogr.OFTString), ("gabarit", ogr.OFTString), ("libelle", ogr.OFTString)]),
        "pic_equipement": (ogr.wkbPoint, [("type_equipement", ogr.OFTString), ("libelle", ogr.OFTString), ("rayon_action_m", ogr.OFTReal), ("hauteur_m", ogr.OFTReal)]),
    }
    for nom, (gtype, champs) in defs.items():
        lyr = ds.CreateLayer(nom, l93, gtype, options=["FID=fid", "SPATIAL_INDEX=YES"])
        for c, t in champs + communs:
            lyr.CreateField(ogr.FieldDefn(c, t))
    ds = None
    print(f"  {PIC.name} créé (pic_zone, pic_acces, pic_equipement)")


if __name__ == "__main__":
    SORTIE.mkdir(exist_ok=True)
    if GPKG.exists():
        GPKG.unlink()  # reconstruit à chaque fois à partir des données brutes
    print("Couches géographiques")
    charger_couches()
    print("Tables de production")
    charger_tables()
    print("Zonages")
    zonages()
    print("Modèle PIC")
    modele_pic()
    print(f"Terminé : {GPKG.relative_to(RACINE)}  ({GPKG.stat().st_size / 1e6:.1f} Mo)")
