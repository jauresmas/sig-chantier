"""Configuration MapStore de la carte (format de carte version 2) : couches WMS du GeoServer de la pile,
groupes, fonds IGN de la Géoplateforme, signets sur les cercles d'étude.
"""
import math
import urllib.parse

from catalogue import COUCHES, GROUPES
from commun import ESPACE

WMS = "/geoserver/wms"
WFS = "/geoserver/wfs"
GEOPF = "https://data.geopf.fr/wms-r/wms"
CNPE = (1.210236, 49.976144)

# Ordre d'affichage, du dessous vers le dessus (la table des matières le montre à l'envers)
ORDRE = ["referentiel", "environnement", "distribution", "htb", "production", "icpe", "site"]
DANS_GROUPE = {  # du dessous vers le dessus
    "referentiel": ["communes", "parcelles", "batiments"],
    "environnement": ["znieff2", "znieff1", "conservatoire", "natura2000_zsc", "natura2000_zps"],
    "distribution": ["bt", "hta", "poteaux", "postes_hta_bt"],
    "htb": ["htb_postes", "htb_lignes", "htb_pylones"],
    "site": ["cercles", "cnpe"],
}
OPACITE = {"znieff2": 0.9, "communes": 0.8}
LEGENDE_DEPLIEE = {"icpe", "production", "htb_lignes", "hta"}  # légende ouverte dans la table des matières


def emprise_cercle(r_km, marge=1.08):
    """Emprise WGS84 (ouest, sud, est, nord) d'un cercle de r_km autour du CNPE."""
    d_lat = r_km * marge / 111.2
    d_lon = r_km * marge / (111.32 * math.cos(math.radians(CNPE[1])))
    return CNPE[0] - d_lon, CNPE[1] - d_lat, CNPE[0] + d_lon, CNPE[1] + d_lat


SIGNETS = [("Abords du CNPE, 2 km", emprise_cercle(2)), ("Zone rapprochée, 5 km", emprise_cercle(5)),
           ("Zone élargie, 10 km", emprise_cercle(10)), ("Rayon du PPI, 20 km", emprise_cercle(20)),
           ("Dieppe", (1.03, 49.89, 1.13, 49.94)), ("Le Tréport et Eu", (1.34, 50.03, 1.45, 50.08))]


def couche_wms(c, emprises=None):
    nom = c["nom"]
    couche = {
        "id": f"{ESPACE}__{nom}", "type": "wms", "url": WMS, "name": f"{ESPACE}:{nom}",
        "title": c["titre"], "description": c["resume"], "group": c["groupe"],
        "visibility": c["visible"], "opacity": OPACITE.get(nom, 1), "expanded": nom in LEGENDE_DEPLIEE,
        "format": "image/png", "transparent": True, "tiled": True, "singleTile": False,
        "search": {"type": "wfs", "url": WFS},
        "featureInfo": {"format": "TEMPLATE", "template": c["fiche"]} if c.get("fiche") else {"format": "HIDDEN"},
        "params": {}, "dimensions": [],
        "allowedSRS": {"EPSG:3857": True, "EPSG:900913": True, "EPSG:4326": True},
    }
    if emprises and nom in emprises:
        o, s, e, n = emprises[nom]
        couche["bbox"] = {"crs": "EPSG:4326", "bounds": {"minx": o, "miny": s, "maxx": e, "maxy": n}}
    return couche


def _vignette_geopf(couche, fmt):
    return GEOPF + "?" + urllib.parse.urlencode({
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": couche, "STYLES": "",
        "CRS": "EPSG:4326", "BBOX": "49.94,1.15,50.01,1.27", "WIDTH": 120, "HEIGHT": 80, "FORMAT": fmt})


def fonds():
    """Fonds de plan : IGN par la Géoplateforme (WMS raster), puis fonds génériques."""
    return [
        {"id": "plan_ign", "type": "wms", "url": GEOPF, "name": "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2",
         "group": "background", "title": "Plan IGN", "format": "image/png", "transparent": False,
         "tiled": True, "opacity": 0.7, "version": "1.3.0", "visibility": True,
         "thumbURL": _vignette_geopf("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", "image/png"),
         "featureInfo": {"format": "HIDDEN"}, "dimensions": [], "params": {}},
        {"id": "ortho_ign", "type": "wms", "url": GEOPF, "name": "ORTHOIMAGERY.ORTHOPHOTOS",
         "group": "background", "title": "Photographies aériennes (IGN)", "format": "image/jpeg",
         "transparent": False, "tiled": True, "version": "1.3.0", "visibility": False,
         "thumbURL": _vignette_geopf("ORTHOIMAGERY.ORTHOPHOTOS", "image/jpeg"),
         "featureInfo": {"format": "HIDDEN"}, "dimensions": [], "params": {}},
        {"id": "carto_positron", "type": "tileprovider", "provider": "CartoDB.PositronNoLabels",
         "name": "PositronNoLabels", "source": "CartoDB", "group": "background",
         "title": "CARTO Positron (sans étiquettes)", "visibility": False},
        {"id": "osm", "type": "osm", "source": "osm", "name": "mapnik", "group": "background",
         "title": "OpenStreetMap", "visibility": False},
        {"id": "fond_vide", "type": "empty", "source": "ol", "name": "empty", "group": "background",
         "title": "Fond vide", "visibility": False},
    ]


def couches(emprises=None):
    par_nom = {c["nom"]: c for c in COUCHES}
    liste = []
    for g in ORDRE:
        noms = DANS_GROUPE.get(g, [c["nom"] for c in COUCHES if c["groupe"] == g])
        liste += [couche_wms(par_nom[n], emprises) for n in noms]
    return liste


def config_carte(emprises=None, centre=(1.31, 49.95), zoom=11):
    """Vue initiale : le cercle de 20 km entier, décalé vers l'ouest pour rester visible à côté du panneau
    de présentation ouvert au démarrage."""
    return {
        "version": 2,
        "map": {
            "projection": "EPSG:900913", "units": "m",
            "center": {"x": centre[0], "y": centre[1], "crs": "EPSG:4326"}, "zoom": zoom,
            "maxExtent": [-20037508.34, -20037508.34, 20037508.34, 20037508.34], "mapOptions": {},
            "layers": fonds() + couches(emprises),
            "groups": [{"id": gid, "title": titre, "expanded": deplie} for gid, titre, deplie in GROUPES],
            "backgrounds": [],
            "bookmark_search_config": {
                "bookmarks": [{"options": {"west": o, "south": s, "east": e, "north": n}, "title": t,
                               "layerVisibilityReload": False} for t, (o, s, e, n) in SIGNETS],
                "zoomOnSelect": True},
            "text_search_config": None,
        },
        "catalogServices": {
            "services": {"sig_chantier": {"url": f"/geoserver/{ESPACE}/wms", "type": "wms", "autoload": True,
                                   "title": "SIG chantier (GeoServer)"}},
            "selectedService": "sig_chantier",
        },
        "mapInfoConfiguration": {"trigger": "click", "infoFormat": "text/html", "showEmptyMessageGFI": False},
        "widgetsConfig": {"widgets": [], "layouts": {"md": [], "xxs": []}},
        "dimensionData": {}, "timelineData": {},
    }
