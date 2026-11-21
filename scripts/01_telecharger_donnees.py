"""
01_telecharger_donnees.py : Téléchargement des données ouvertes autour du CNPE de Penly (Seine-Maritime).

Sources (toutes gratuites, Licence Ouverte Etalab sauf mention) :
  - EDF          opendata.edf.fr          centrales, indisponibilités, rejets thermiques, historiques
  - Enedis       opendata.enedis.fr       réseau HTA/BT aérien et souterrain, postes HTA/BT, poteaux
  - Agence ORE   opendata.agenceore.fr    registre national des installations de production
  - Koumoul      koumoul.com              ICPE (installations classées)
  - IGN          data.geopf.fr (WFS)      BD TOPO : lignes HTB, postes, pylônes, routes, bâti, hydro...
  - PatriNat     data.geopf.fr (WFS)      ZNIEFF 1/2, Natura 2000 (SIC/ZSC, ZPS), Conservatoire du littoral
  - Etalab       cadastre.data.gouv.fr    parcelles cadastrales de Petit-Caux (76618)

Usage (PowerShell, depuis le dossier du projet) :
    python scripts\\01_telecharger_donnees.py

Sortie : 01_donnees_brutes/<source>/*.geojson|*.csv + 01_donnees_brutes/manifeste.json
Python standard uniquement (pas de dépendance).
"""
import csv
import gzip
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BRUT = RACINE / "01_donnees_brutes"

# CNPE de Penly (coordonnées publiées par EDF, jeu « centrales de production nucléaire »)
PENLY_LAT, PENLY_LON = 49.976144, 1.210236

# Emprises (lon_min, lat_min, lon_max, lat_max) en WGS84
ZONE_20KM = (0.93, 49.80, 1.49, 50.16)   # contexte : cercle de 20 km (rayon PPI)
ZONE_5KM = (1.14, 49.93, 1.28, 50.02)    # abords du chantier : bâti, végétation

UA = {"User-Agent": "sig-chantier/1.0 (projet personnel open data)"}
MANIFESTE = []


def get(url, binaire=False, essais=4):
    for i in range(essais):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            return data if binaire else data.decode("utf-8")
        except Exception as e:  # réseau capricieux : on réessaie
            if i == essais - 1:
                raise
            print(f"    ! {e} : nouvel essai dans {5 * (i + 1)} s")
            time.sleep(5 * (i + 1))


def demojibake(v):
    """Certaines données EDF sont encodées deux fois (« NuclÃ©aire » -> « Nucléaire »)."""
    if isinstance(v, str) and ("Ã" in v or "Â" in v):
        try:
            return v.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return v
    return v


def nettoyer(props):
    return {k: demojibake(v) for k, v in props.items() if k not in ("_rand", "_score", "_i")}


def geom_depuis_ligne(r):
    g = r.get("geometry") or r.get("_geoshape")
    if isinstance(g, str):
        g = json.loads(g)
    if g:
        return g
    pt = r.get("_geopoint")
    if pt:
        lat, lon = [float(x) for x in pt.split(",")]
        return {"type": "Point", "coordinates": [lon, lat]}
    return None


def datafair(base, dataset, params=None, filtre=None):
    """Toutes les lignes d'un jeu Data Fair (pagination par lien « next »)."""
    p = {"size": 5000}
    p.update(params or {})
    url = f"{base}/data-fair/api/v1/datasets/{dataset}/lines?" + urllib.parse.urlencode(p)
    lignes = []
    while url:
        d = json.loads(get(url))
        lignes.extend(d.get("results", []))
        url = d.get("next") if d.get("results") else None
    if filtre:
        lignes = [r for r in lignes if filtre(r)]
    return lignes


def ecrire_geojson(chemin, lignes):
    feats = []
    for r in lignes:
        g = geom_depuis_ligne(r)
        if g is None:
            continue
        props = nettoyer({k: v for k, v in r.items() if k not in ("geometry", "_geoshape")})
        feats.append({"type": "Feature", "geometry": g, "properties": props})
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False), encoding="utf-8")
    return len(feats)


def ecrire_csv(chemin, lignes):
    lignes = [nettoyer(r) for r in lignes]
    champs = []
    for r in lignes:
        for k in r:
            if k not in champs:
                champs.append(k)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=champs, delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    return len(lignes)


def noter(source, fichier, url_page, nb, licence="Licence Ouverte / Open Licence v2.0 (Etalab)", note=""):
    MANIFESTE.append({
        "source": source, "fichier": str(fichier.relative_to(RACINE)).replace("\\", "/"),
        "page": url_page, "objets": nb, "licence": licence, "note": note,
        "telecharge_le": datetime.now().isoformat(timespec="seconds"),
    })
    print(f"  ok  {fichier.name:<55} {nb:>7} objets")


def bbox_str(b):
    return ",".join(str(x) for x in b)


# ---------------------------------------------------------------- EDF
def edf():
    print("EDF : opendata.edf.fr")
    base = "https://opendata.edf.fr"
    d = BRUT / "edf"
    geo = {
        "centrales-de-production-nucleaire-edf": "centrales_nucleaires",
        "centrales-de-production-hydraulique-de-edf-sa": "centrales_hydrauliques",
        "centrales-de-production-thermique-a-flamme-d-edf-sa-fioul-gaz-charbon": "centrales_thermiques",
    }
    for ds, nom in geo.items():
        f = d / f"{nom}.geojson"
        noter("EDF", f, f"{base}/datasets/{ds}", ecrire_geojson(f, datafair(base, ds)))

    est_penly = lambda r: "PENLY" in str(r.get("nom", "")).upper()
    tables = {
        "indisponibilites-des-moyens-de-production-edf-sa": ("indisponibilites", {"q": "PENLY"}, est_penly),
        "historique-des-indisponibilites-des-moyens-de-production-de-edf-sa-depuis-2015": ("indisponibilites_historique_2015", {"q": "PENLY"}, est_penly),
        "seuils-et-limites-des-rejets-thermiques-aux-abords-des-centrales-nucleaires-d-edf-sa": ("seuils_rejets_thermiques", None, None),
        "historique-des-productions-edf-sa": ("historique_productions_1948", None, None),
        "disponibilite-du-parc-nucleaire-d-edf-sa-depuis-2002": ("disponibilite_parc_nucleaire", None, None),
    }
    for ds, (nom, params, filtre) in tables.items():
        f = d / f"{nom}.csv"
        noter("EDF", f, f"{base}/datasets/{ds}", ecrire_csv(f, datafair(base, ds, params, filtre)))


# ---------------------------------------------------------------- Enedis
def enedis():
    print("Enedis : opendata.enedis.fr (emprise 20 km)")
    base = "https://opendata.enedis.fr"
    d = BRUT / "enedis"
    jeux = {
        "reseau-hta": "enedis_hta_aerien",
        "reseau-souterrain-hta": "enedis_hta_souterrain",
        "reseau-bt": "enedis_bt_aerien",
        "reseau-souterrain-bt": "enedis_bt_souterrain",
        "poste-electrique": "enedis_postes_hta_bt",
        "position-geographique-des-poteaux-hta-et-bt": "enedis_poteaux_hta_bt",
    }
    for ds, nom in jeux.items():
        f = d / f"{nom}.geojson"
        n = ecrire_geojson(f, datafair(base, ds, {"bbox": bbox_str(ZONE_20KM)}))
        noter("Enedis", f, f"{base}/datasets/{ds}", n)


# ---------------------------------------------------------------- Registre ORE + ICPE
def registre_et_icpe():
    print("Agence ORE / Koumoul (emprise 20 km)")
    f = BRUT / "ore" / "registre_installations_production_stockage.geojson"
    ds = "registre-national-installation-production-stockage-electricite-agrege"
    n = ecrire_geojson(f, datafair("https://opendata.agenceore.fr", ds, {"bbox": bbox_str(ZONE_20KM)}))
    noter("Agence ORE (RTE, Enedis, EDF SEI, ELD)", f, f"https://opendata.agenceore.fr/datasets/{ds}", n)

    f = BRUT / "icpe" / "icpe.geojson"
    n = ecrire_geojson(f, datafair("https://koumoul.com", "icpe", {"bbox": bbox_str(ZONE_20KM)}))
    noter("Géorisques via Koumoul", f, "https://koumoul.com/datasets/icpe", n)


# ---------------------------------------------------------------- IGN / PatriNat (WFS Géoplateforme)
def wfs(couche, emprise, chemin, source, note=""):
    lon1, lat1, lon2, lat2 = emprise
    feats, debut, pas = [], 0, 5000
    crs = None
    while True:
        p = {
            "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": couche,
            "SRSNAME": "EPSG:2154", "OUTPUTFORMAT": "application/json",
            "BBOX": f"{lat1},{lon1},{lat2},{lon2},urn:ogc:def:crs:EPSG::4326",
            "COUNT": pas, "STARTINDEX": debut,
        }
        d = json.loads(get("https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode(p)))
        lot = d.get("features", [])
        crs = d.get("crs", crs)
        feats.extend(lot)
        if len(lot) < pas:
            break
        debut += pas
    fc = {"type": "FeatureCollection", "features": feats}
    if crs:
        fc["crs"] = crs
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    page = "https://geoservices.ign.fr/bdtopo" if couche.startswith("BDTOPO") else "https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique"
    noter(source, chemin, page, len(feats), note=note or f"WFS {couche}")


def ign_patrinat():
    print("IGN BD TOPO / PatriNat : WFS data.geopf.fr")
    d = BRUT / "ign"
    for couche, emprise in [
        ("BDTOPO_V3:ligne_electrique", ZONE_20KM),
        ("BDTOPO_V3:poste_de_transformation", ZONE_20KM),
        ("BDTOPO_V3:pylone", ZONE_20KM),
        ("BDTOPO_V3:commune", ZONE_20KM),
        ("BDTOPO_V3:troncon_de_route", ZONE_20KM),
        ("BDTOPO_V3:troncon_de_voie_ferree", ZONE_20KM),
        ("BDTOPO_V3:cours_d_eau", ZONE_20KM),
        ("BDTOPO_V3:surface_hydrographique", ZONE_20KM),
        ("BDTOPO_V3:zone_d_activite_ou_d_interet", ZONE_20KM),
        ("BDTOPO_V3:batiment", ZONE_5KM),
        ("BDTOPO_V3:zone_de_vegetation", ZONE_5KM),
        ("BDTOPO_V3:haie", ZONE_5KM),
    ]:
        wfs(couche, emprise, d / f"bdtopo_{couche.split(':')[1]}.geojson", "IGN : BD TOPO V3")

    d = BRUT / "patrinat"
    for couche in ["patrinat_znieff1:znieff1", "patrinat_znieff2:znieff2", "patrinat_znieff1_mer:znieff1_mer",
                   "patrinat_znieff2_mer:znieff2_mer", "patrinat_sic:sic", "patrinat_zps:zps", "patrinat_cdl2:cdl"]:
        wfs(couche, ZONE_20KM, d / f"{couche.split(':')[1]}.geojson", "PatriNat (OFB-MNHN-CNRS-IRD)")


# ---------------------------------------------------------------- Cadastre
def cadastre():
    print("Cadastre Etalab : Petit-Caux (76618)")
    url = "https://cadastre.data.gouv.fr/bundler/cadastre-etalab/communes/76618/geojson/parcelles"
    f = BRUT / "cadastre" / "parcelles_76618_petit_caux.geojson"
    f.parent.mkdir(parents=True, exist_ok=True)
    data = get(url, binaire=True)
    f.write_bytes(data)
    noter("DGFiP / Etalab", f, "https://cadastre.data.gouv.fr/datasets/cadastre-etalab", len(json.loads(data)["features"]))


if __name__ == "__main__":
    t0 = time.time()
    for etape in (edf, enedis, registre_et_icpe, ign_patrinat, cadastre):
        try:
            etape()
        except Exception as e:
            print(f"  ERREUR {etape.__name__} : {e}")
            MANIFESTE.append({"source": etape.__name__, "erreur": str(e)})
    (BRUT / "manifeste.json").write_text(json.dumps(MANIFESTE, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Terminé en {time.time() - t0:.0f} s : {len(MANIFESTE)} fichiers, manifeste : 01_donnees_brutes/manifeste.json")
