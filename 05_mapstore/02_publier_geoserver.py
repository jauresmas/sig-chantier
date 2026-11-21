"""Étape 2 : publie les couches de sig_chantier.carto dans le GeoServer de la pile MapStore.

Espace de travail sig_chantier, entrepôt PostGIS carto, un style SLD par couche (styles.py), titres et résumés
(catalogue.py). Les tables restent en Lambert-93 : GeoServer les reprojette pour MapStore.
Idempotent : relancer met à jour sans dupliquer.

    python 05_mapstore/02_publier_geoserver.py
"""
from catalogue import COUCHES
from commun import DEPOT, ENTREPOT, ESPACE, PG, PG_DEPUIS_DOCKER, geoserver, mot_de_passe_base
from styles import styles

MOTS_CLES = ["Penly", "CNPE", "chantier", "réseaux électriques", "environnement", "open data"]


def espace(gs):
    ns = {"namespace": {"prefix": ESPACE, "uri": DEPOT}}
    if not gs.existe(f"/workspaces/{ESPACE}.json"):
        gs.requete("POST", "/namespaces", ns)
    gs.requete("PUT", f"/namespaces/{ESPACE}", ns)
    print(f"espace de travail {ESPACE}")


def entrepot(gs):
    parametres = {
        "dbtype": "postgis", "host": PG_DEPUIS_DOCKER, "port": str(PG["port"]), "database": PG["dbname"],
        "schema": "carto", "user": PG["user"], "passwd": mot_de_passe_base(),
        "Expose primary keys": "true", "Loose bbox": "true", "Estimated extends": "false",
        "encode functions": "true", "Support on the fly geometry simplification": "true",
        "validate connections": "true", "max connections": "10", "min connections": "1",
    }
    corps = {"dataStore": {"name": ENTREPOT, "description": "SIG chantier : couches publiées (PostGIS)",
                           "enabled": True, "connectionParameters": {
                               "entry": [{"@key": k, "$": v} for k, v in parametres.items()]}}}
    chemin = f"/workspaces/{ESPACE}/datastores"
    if gs.existe(f"{chemin}/{ENTREPOT}.json"):
        gs.requete("PUT", f"{chemin}/{ENTREPOT}", corps)
    else:
        gs.requete("POST", chemin, corps)
    print(f"entrepôt {ENTREPOT} -> {PG['dbname']}.carto sur {PG_DEPUIS_DOCKER}")


def publier_styles(gs):
    chemin = f"/workspaces/{ESPACE}/styles"
    tous = styles()
    for nom, sld in tous.items():
        if gs.existe(f"{chemin}/{nom}.json"):
            gs.requete("PUT", f"{chemin}/{nom}", sld, type_contenu="application/vnd.ogc.sld+xml")
        else:
            gs.requete("POST", f"{chemin}?name={nom}", sld, type_contenu="application/vnd.ogc.sld+xml")
    print(f"{len(tous)} styles")


def couche(gs, c):
    nom = c["nom"]
    ft = {"featureType": {
        "name": nom, "nativeName": nom, "enabled": True, "srs": "EPSG:2154", "projectionPolicy": "FORCE_DECLARED",
        "title": c["titre"], "abstract": c["resume"], "keywords": {"string": MOTS_CLES},
    }}
    chemin = f"/workspaces/{ESPACE}/datastores/{ENTREPOT}/featuretypes"
    if gs.existe(f"{chemin}/{nom}.json"):
        gs.requete("PUT", f"{chemin}/{nom}?recalculate=nativebbox,latlonbbox", ft)
    else:
        gs.requete("POST", chemin, ft)
    gs.requete("PUT", f"/layers/{ESPACE}:{nom}", {"layer": {
        "defaultStyle": {"name": c["style"], "workspace": ESPACE},
        "attribution": {"title": "SIG chantier · données ouvertes", "href": DEPOT}}})


def main():
    gs = geoserver()
    espace(gs)
    entrepot(gs)
    publier_styles(gs)
    for c in COUCHES:
        couche(gs, c)
        print(f"  couche {ESPACE}:{c['nom']} (style {c['style']})")


if __name__ == "__main__":
    main()
