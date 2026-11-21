"""Étape 1 : charge le GeoPackage du projet dans PostGIS, puis construit les couches de la carte.

  schéma brut  : copie des couches de 02_donnees/penly_sig.gpkg (ogr2ogr de QGIS), en Lambert-93, 2D
  schéma carto : tables mises en forme par sql/carto.sql (libellés français, distance au CNPE, contrôle
                 de position des ICPE...), seules publiées par GeoServer

Relancer après une reconstruction du GeoPackage (scripts/02_construire_gpkg.py).

    python 05_mapstore/01_charger_postgis.py
"""
import sys

from commun import GPKG, ICI, PG, geoserver, ogr2ogr, psql

COUCHES = [
    "zon_cnpe_penly", "zon_cercles", "prod_centrales_nucleaires", "prod_registre_installations",
    "res_htb_lignes", "res_htb_postes", "res_htb_pylones",
    "res_hta_aerien", "res_hta_souterrain", "res_bt_aerien", "res_bt_souterrain",
    "res_postes_hta_bt", "res_poteaux_hta_bt",
    "env_znieff1", "env_znieff2", "env_natura2000_zsc_sic", "env_natura2000_zps", "env_conservatoire_littoral",
    "env_icpe", "ref_communes", "ref_batiments", "ref_parcelles_petit_caux",
]


def main():
    if not GPKG.exists():
        sys.exit(f"{GPKG} absent : le reconstruire avec scripts/02_construire_gpkg.py")
    print(f"ogr2ogr {GPKG.name} -> {PG['dbname']}.brut ({len(COUCHES)} couches)")
    ogr2ogr(GPKG, COUCHES, "brut", "-dim", "XY")
    psql((ICI / "sql" / "carto.sql").read_text(encoding="utf-8"))
    print(psql("SELECT string_agg(c.relname || ' ' || c.reltuples::bigint, ', ' ORDER BY c.relname) "
               "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
               "WHERE n.nspname = 'carto' AND c.relkind = 'r'"))
    # Tables remplacées : GeoServer doit oublier ses schémas et connexions en cache
    try:
        geoserver().requete("POST", "/reset", ok=(200,))
        print("cache GeoServer vidé")
    except (OSError, RuntimeError, SystemExit):
        print("GeoServer injoignable : cache non vidé")


if __name__ == "__main__":
    main()
