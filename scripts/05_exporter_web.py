"""Export des couches de la carte web (docs/data/) depuis le GeoPackage Lambert-93.

Produit des GeoJSON WGS84 allégés (champs utiles renommés, coordonnées à 6 décimales,
géométries simplifiées et découpées autour du site), avec pour chaque objet sa distance
au CNPE calculée en Lambert-93, ainsi que deux fichiers de synthèse :
  - meta.json : source, date d'extraction, licence et nombre d'objets de chaque couche ;
  - site.json : fiche du CNPE et bilan des contraintes par anneau (2, 5, 10, 20 km).

Exécution (Python de QGIS, GDAL requis) :
    python-qgis-ltr.bat scripts/05_exporter_web.py
"""
import json
from pathlib import Path

from osgeo import ogr, osr

ogr.UseExceptions()
osr.UseExceptions()

RACINE = Path(__file__).resolve().parent.parent
GPKG = RACINE / "02_donnees" / "sig_chantier.gpkg"
MANIFESTE = RACINE / "01_donnees_brutes" / "manifeste.json"
SORTIE = RACINE / "docs" / "data"

ANNEAUX_KM = [2, 5, 10, 20]
DECOUPE_KM = 21  # emprise d'affichage : un peu au-delà du cercle de 20 km

SOURCES = {
    "edf": ("EDF", "https://opendata.edf.fr", "edf/centrales_nucleaires"),
    "ore": ("Agence ORE", "https://opendata.agenceore.fr", "ore/registre"),
    "bdtopo": ("IGN, BD TOPO V3", "https://geoservices.ign.fr/bdtopo", "ign/bdtopo_ligne"),
    "bdtopo_com": ("IGN, BD TOPO V3", "https://geoservices.ign.fr/bdtopo", "ign/bdtopo_commune"),
    "enedis": ("Enedis", "https://opendata.enedis.fr", "enedis/enedis_hta"),
    "patrinat": ("PatriNat (OFB, MNHN, CNRS, IRD)", "https://inpn.mnhn.fr", "patrinat/znieff1"),
    "icpe": ("Géorisques, via Koumoul", "https://www.georisques.gouv.fr", "icpe/icpe"),
    "projet": ("Calcul du projet (scripts/02_construire_gpkg.py)", "", None),
}

REGIME_ICPE = {
    "A": "Autorisation",
    "E": "Enregistrement",
    "AUTRE": "Autre régime (déclaration surtout)",
    "NEANT": "Non classé ICPE (site inspecté)",
}

# id, titre, source, [(table, {champ_sortie: expression SQL}, attributs fixes)], options
COUCHES = [
    ("cercles", "Cercles d'étude 2 / 5 / 10 / 20 km", "projet",
     [("zon_cercles", {"rayon_km": "rayon_km", "libelle": "libelle"}, {})], {}),
    ("cnpe", "CNPE de Penly", "edf",
     [("zon_cnpe", {"nom": "nom", "source": "source"}, {})], {}),
    ("production", "Installations de production et de stockage", "ore",
     [("prod_registre_installations", {
         "nom": "nominstallation", "filiere": "filiere", "technologie": "technologie",
         "puissance_kw": "puismaxinstallee", "commune": "commune",
         "mise_en_service": "datemiseenservice", "tension_raccordement": "tensionraccordement",
         "gestionnaire": "gestionnaire"}, {})], {}),
    ("htb_lignes", "Lignes électriques HTB", "bdtopo",
     [("res_htb_lignes", {"tension": "voltage", "gestionnaire": "gestionnaire",
                          "etat": "etat_de_l_objet", "id_ign": "cleabs"}, {})],
     {"simplifier": 2}),
    ("htb_postes", "Postes électriques HTB", "bdtopo",
     [("res_htb_postes", {"nom": "toponyme", "importance": "importance", "id_ign": "cleabs"}, {})],
     {"simplifier": 1}),
    ("htb_pylones", "Pylônes HTB", "bdtopo",
     [("res_htb_pylones", {"numero": "numero", "hauteur_m": "hauteur", "id_ign": "cleabs"}, {})], {}),
    ("hta", "Réseau HTA", "enedis",
     [("res_hta_aerien", {"commune": "nom_commune"}, {"pose": "aérien"}),
      ("res_hta_souterrain", {"commune": "nom_commune"}, {"pose": "souterrain"})],
     {"simplifier": 1, "decouper_km": DECOUPE_KM}),
    ("postes_hta_bt", "Postes HTA/BT", "enedis",
     [("res_postes_hta_bt", {"commune": "nom_commune"}, {})], {"decouper_km": DECOUPE_KM}),
    ("bt", "Réseau BT", "enedis",
     [("res_bt_aerien", {"commune": "nom_commune"}, {"pose": "aérien"}),
      ("res_bt_souterrain", {"commune": "nom_commune"}, {"pose": "souterrain"})],
     {"simplifier": 1, "decouper_km": 10}),
    ("poteaux", "Poteaux HTA et BT", "enedis",
     [("res_poteaux_hta_bt", {"commune": "nom_commune"}, {})], {"decouper_km": 10}),
    ("znieff1", "ZNIEFF de type 1", "patrinat",
     [("env_znieff1", {"nom": "nom_site", "id_mnhn": "id_mnhn", "fiche": "url_fiche"}, {})],
     {"simplifier": 5, "decouper_km": DECOUPE_KM}),
    ("znieff2", "ZNIEFF de type 2", "patrinat",
     [("env_znieff2", {"nom": "nom_site", "id_mnhn": "id_mnhn", "fiche": "url_fiche"}, {})],
     {"simplifier": 5, "decouper_km": DECOUPE_KM}),
    ("natura2000", "Natura 2000", "patrinat",
     [("env_natura2000_zsc_sic", {"nom": "nom_site", "id_mnhn": "id_mnhn", "fiche": "url_fiche"},
       {"directive": "Habitats (ZSC / SIC)"}),
      ("env_natura2000_zps", {"nom": "nom_site", "id_mnhn": "id_mnhn", "fiche": "url_fiche"},
       {"directive": "Oiseaux (ZPS)"})],
     {"simplifier": 5, "decouper_km": DECOUPE_KM}),
    ("conservatoire", "Terrains du Conservatoire du littoral", "patrinat",
     [("env_conservatoire_littoral", {"nom": "nom_site", "id_mnhn": "id_mnhn"}, {})],
     {"simplifier": 3, "decouper_km": DECOUPE_KM}),
    ("icpe", "Installations classées (ICPE)", "icpe",
     [("env_icpe", {"nom": "nom_ets", "regime": "regime", "activite": "lib_naf",
                    "commune": "commune", "adresse": "adresse", "fiche": "url_fiche",
                    "priorite_nationale": "priorite_nationale",
                    "derniere_inspection": "derniere_inspection", "code_aiot": "code_aiot"}, {})], {}),
    ("communes", "Communes", "bdtopo_com",
     [("ref_communes", {"nom": "nom_officiel", "code_insee": "code_insee",
                        "population": "population"}, {})],
     {"simplifier": 8, "decouper_km": DECOUPE_KM}),
]

# Couches dont on mesure la longueur (km) dans chaque anneau
LONGUEURS = {"htb_lignes", "hta", "bt"}


def date_extraction(manifeste, motif):
    if not motif:
        return None
    dates = [e["telecharge_le"] for e in manifeste if motif in e["fichier"]]
    return min(dates)[:10] if dates else None


def arrondir(valeur):
    if isinstance(valeur, float):
        return round(valeur, 2)
    if isinstance(valeur, str):
        valeur = valeur.strip()
        return valeur or None
    return valeur


def cle_commune(nom):
    """Nom de commune comparable : sans accents, casse, tirets ni article de liaison."""
    import unicodedata
    s = unicodedata.normalize("NFD", nom or "").encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum())


def regrouper_par_commune(entites):
    """Le registre ORE agrégé place chaque installation au centre de sa commune.

    On publie donc un objet par commune (somme des puissances, liste des installations),
    plutôt que des points superposés qui laisseraient croire à une localisation précise.
    """
    groupes = {}
    for e in entites:
        cle = json.dumps(e["geometry"]["coordinates"])
        groupes.setdefault(cle, []).append(e)
    sortie = []
    for i, membres in enumerate(groupes.values(), start=1):
        membres.sort(key=lambda e: -(e["properties"]["puissance_kw"] or 0))
        puissance = sum(e["properties"]["puissance_kw"] or 0 for e in membres)
        filieres = {}
        for e in membres:
            f = e["properties"]["filiere"]
            filieres[f] = filieres.get(f, 0) + (e["properties"]["puissance_kw"] or 0)
        sortie.append({
            "type": "Feature",
            "id": i,
            "properties": {
                "commune": membres[0]["properties"]["commune"],
                "installations": len(membres),
                "puissance_kw": round(puissance, 1),
                "filiere_principale": max(filieres, key=filieres.get),
                "dist_cnpe_m": membres[0]["properties"]["dist_cnpe_m"],
                "liste": [{k: e["properties"][k] for k in
                           ("nom", "filiere", "technologie", "puissance_kw", "mise_en_service",
                            "tension_raccordement", "gestionnaire")} for e in membres],
            },
            "geometry": membres[0]["geometry"],
        })
    return sortie


def main():
    manifeste = json.loads(MANIFESTE.read_text(encoding="utf-8"))
    SORTIE.mkdir(parents=True, exist_ok=True)
    ds = ogr.Open(str(GPKG))

    l93 = osr.SpatialReference()
    l93.ImportFromEPSG(2154)
    wgs = osr.SpatialReference()
    wgs.ImportFromEPSG(4326)
    wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    vers_wgs = osr.CoordinateTransformation(l93, wgs)

    cnpe_lyr = ds.GetLayerByName("zon_cnpe")
    cnpe_entite = cnpe_lyr.GetNextFeature()  # l'entité doit rester référencée
    centre = cnpe_entite.GetGeometryRef().Clone()
    centre.FlattenTo2D()
    disques = {r: centre.Buffer(r * 1000, 64) for r in ANNEAUX_KM + [10, DECOUPE_KM]}

    # Communes en Lambert-93, pour le contrôle de cohérence des ICPE
    communes_l93 = []
    for f in ds.GetLayerByName("ref_communes"):
        g = f.GetGeometryRef().Clone()
        g.FlattenTo2D()
        communes_l93.append((f.GetField("nom_officiel"), g))
    ecarts_icpe = 0

    meta = {"genere_le": None, "couches": {}}
    bilan = {str(r): {} for r in ANNEAUX_KM}

    for ident, titre, cle_source, tables, opts in COUCHES:
        tol = opts.get("simplifier")
        decoupe = disques[opts["decouper_km"]] if opts.get("decouper_km") else None
        entites, n = [], 0
        longueurs = {str(r): 0.0 for r in ANNEAUX_KM}
        comptes = {str(r): 0 for r in ANNEAUX_KM}
        douteuses = {str(r): 0 for r in ANNEAUX_KM}
        for table, champs, fixes in tables:
            lyr = ds.GetLayerByName(table)
            geomcol = lyr.GetGeometryColumn()
            select = ", ".join(f'"{src}" AS "{dst}"' for dst, src in champs.items())
            res = ds.ExecuteSQL(f'SELECT {select}, "{geomcol}" FROM "{table}"')
            for f in res:
                g = f.GetGeometryRef()
                if g is None:
                    continue
                g = g.Clone()
                g.FlattenTo2D()
                if decoupe is not None:
                    if not g.Intersects(decoupe):
                        continue
                    if g.GetGeometryType() not in (ogr.wkbPoint, ogr.wkbMultiPoint):
                        g = g.Intersection(decoupe)
                        if g is None or g.IsEmpty():
                            continue
                commune_position, douteux = None, False
                if ident == "icpe":
                    commune_position = next((nom for nom, cg in communes_l93 if g.Within(cg)), None)
                    douteux = (commune_position is not None
                               and cle_commune(commune_position) != cle_commune(f.GetField("commune")))
                dist = g.Distance(centre)
                for r in ANNEAUX_KM:
                    if dist <= r * 1000:
                        # Une position douteuse ne compte pas dans le bilan : elle est comptée à part.
                        if douteux:
                            douteuses[str(r)] += 1
                            continue
                        comptes[str(r)] += 1
                        if ident in LONGUEURS:
                            longueurs[str(r)] += g.Intersection(disques[r]).Length()
                if tol:
                    g = g.SimplifyPreserveTopology(tol)
                g.Transform(vers_wgs)
                props = {dst: arrondir(f.GetField(dst)) for dst in champs}
                props.update(fixes)
                if ident == "icpe":
                    props["regime_libelle"] = REGIME_ICPE.get(props.get("regime"), props.get("regime"))
                    # Contrôle qualité : la position tombe-t-elle dans la commune déclarée ?
                    props["commune_position"] = commune_position
                    if commune_position is None:
                        props["controle_position"] = "hors de l'emprise des communes chargées"
                    elif cle_commune(commune_position) == cle_commune(props.get("commune")):
                        props["controle_position"] = "conforme"
                    else:
                        props["controle_position"] = "écart"
                        ecarts_icpe += 1
                if ident == "htb_lignes" and props.get("tension"):
                    props["tension_kv"] = int(props["tension"].split()[0])
                props["dist_cnpe_m"] = round(dist)
                n += 1
                entites.append({
                    "type": "Feature",
                    "id": n,
                    "properties": props,
                    "geometry": json.loads(g.ExportToJson(["COORDINATE_PRECISION=6"])),
                })
            ds.ReleaseResultSet(res)

        if ident == "production":
            entites = regrouper_par_commune(entites)

        chemin = SORTIE / f"{ident}.geojson"
        chemin.write_text(json.dumps({"type": "FeatureCollection", "features": entites},
                                     ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        nom_src, url_src, motif = SOURCES[cle_source]
        meta["couches"][ident] = {
            "titre": titre,
            "source": nom_src,
            "url_source": url_src,
            "date": date_extraction(manifeste, motif),
            "licence": "Licence Ouverte Etalab 2.0",
            "objets": len(entites),
            "decoupe_km": opts.get("decouper_km"),
            "octets": chemin.stat().st_size,
        }
        if ident == "icpe":
            meta["couches"][ident]["note"] = (
                f"Contrôle de position : {ecarts_icpe} établissements sur {n} sont positionnés hors de "
                "leur commune déclarée (erreur de géocodage ou fusion de communes).")
            meta["couches"][ident]["ecarts_position"] = ecarts_icpe
        if ident == "production":
            meta["couches"][ident]["note"] = (
                f"{n} installations du registre agrégé, localisées au centre de leur commune "
                f"et regroupées en {len(entites)} communes.")
        for r in ANNEAUX_KM:
            # Au-delà de l'emprise de découpe, un bilan serait faux : on le laisse vide.
            hors = opts.get("decouper_km") and r > opts["decouper_km"]
            entree = None if hors else {"objets": comptes[str(r)]}
            if entree is not None and ident in LONGUEURS:
                entree["km"] = round(longueurs[str(r)] / 1000, 1)
            if entree is not None and douteuses[str(r)]:
                entree["positions_douteuses"] = douteuses[str(r)]
            bilan[str(r)][ident] = entree
        print(f"{ident:16} {n:6} objets  {chemin.stat().st_size / 1024:8.0f} Ko", flush=True)

    # Masque de mer : la BD ORTHO peint le large d'un aplat pâle ; la carte le recouvre d'un lavis.
    # Mer = emprise des communes chargées moins leur union (les limites communales suivent le trait de côte).
    union = ogr.Geometry(ogr.wkbMultiPolygon)
    for _, g in communes_l93:
        for i in range(g.GetGeometryCount()) if g.GetGeometryType() == ogr.wkbMultiPolygon else [None]:
            union.AddGeometry(g.GetGeometryRef(i).Clone() if i is not None else g.Clone())
    terre = union.UnionCascaded()
    xmin, xmax, ymin, ymax = terre.GetEnvelope()
    cadre = ogr.CreateGeometryFromWkt(
        f"POLYGON(({xmin} {ymin},{xmax} {ymin},{xmax} {ymax},{xmin} {ymax},{xmin} {ymin}))")
    mer = cadre.Difference(terre)
    morceaux = [mer.GetGeometryRef(i).Clone() for i in range(mer.GetGeometryCount())] \
        if mer.GetGeometryType() == ogr.wkbMultiPolygon else [mer]
    # Les coins du cadre qu'aucune commune ne couvre sont aussi « hors terre » : on ne garde
    # que le morceau qui contient un point au large (Manche, au nord de Penly).
    large = ogr.CreateGeometryFromWkt("POINT (1.10 50.05)")
    large.AssignSpatialReference(wgs)
    large.Transform(osr.CoordinateTransformation(wgs, l93))
    mer = ogr.Geometry(ogr.wkbMultiPolygon)
    for m in morceaux:
        if m.Contains(large):
            mer.AddGeometry(m)
    if mer.GetGeometryCount() != 1:
        raise RuntimeError(f"masque de mer : {mer.GetGeometryCount()} morceau(x) au large, 1 attendu")
    mer = mer.SimplifyPreserveTopology(5)
    mer.Transform(vers_wgs)
    cadre.Transform(vers_wgs)
    (SORTIE / "mer.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [{
        "type": "Feature", "id": 1, "properties": {},
        "geometry": json.loads(mer.ExportToJson(["COORDINATE_PRECISION=6"]))}]},
        separators=(",", ":")), encoding="utf-8")
    emprise_terre = [round(v, 4) for v in (cadre.GetEnvelope()[0], cadre.GetEnvelope()[2],
                                           cadre.GetEnvelope()[1], cadre.GetEnvelope()[3])]
    print(f"mer              emprise {emprise_terre}  {(SORTIE / 'mer.geojson').stat().st_size / 1024:.0f} Ko", flush=True)

    # Fiche du site, depuis les données EDF
    tranches = []
    res = ds.ExecuteSQL("SELECT tranche, puissance_installee, date_de_mise_en_service_industrielle, "
                        "commune FROM prod_centrales_nucleaires WHERE upper(centrale) = 'PENLY' "
                        "ORDER BY tranche")
    for f in res:
        tranches.append({"tranche": f.GetField(0), "puissance_mw": f.GetField(1),
                         "mise_en_service": f.GetField(2).replace("/", "-"), "commune": f.GetField(3)})
    ds.ReleaseResultSet(res)
    centre_wgs = centre.Clone()
    centre_wgs.Transform(vers_wgs)
    site = {
        "nom": "CNPE de Penly",
        "commune": tranches[0]["commune"] if tranches else None,
        "departement": "Seine-Maritime (76)",
        "centre": [round(centre_wgs.GetX(), 6), round(centre_wgs.GetY(), 6)],
        "centre_l93": [round(centre.GetX()), round(centre.GetY())],
        "tranches": tranches,
        "emprise": emprise_terre,
        "anneaux": bilan,
    }
    (SORTIE / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=1), encoding="utf-8")
    meta["genere_le"] = max(e["telecharge_le"] for e in manifeste)[:10]
    (SORTIE / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(c["octets"] for c in meta["couches"].values())
    print(f"Total : {total / 1024 / 1024:.1f} Mo dans {SORTIE}", flush=True)


if __name__ == "__main__":
    main()
