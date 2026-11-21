"""Étape 3 : publie dans MapStore la carte du SIG chantier Penly et son application dédiée (contexte).

Carte : couches WMS du GeoServer de la pile (02_publier_geoserver.py), groupées comme la carte web, fonds IGN,
signets, fiches au clic, fiche de présentation et vignette. Application : visualiseur MapStore aux couleurs du
projet. Ressources en lecture publique. Idempotent : les ressources sont retrouvées par nom.

    python 05_mapstore/03_publier_mapstore.py            carte et application
    python 05_mapstore/03_publier_mapstore.py adresses   affiche les adresses des pages déjà publiées
"""
import json
import sys

import application
import carte
from catalogue import COUCHES
from commun import ENTREPOT, ESPACE, ICI, MAPSTORE, geoserver, mapstore
from ressources import Ressources
from textes import PRESENTATION_CARTE

NOM_CARTE = "SIG chantier Penly · carte"
COUCHES_VIGNETTE = ["communes", "znieff1", "natura2000_zsc", "natura2000_zps", "conservatoire", "hta",
                    "htb_lignes", "htb_postes", "production", "icpe", "cercles", "cnpe"]


def emprises():
    """Emprise WGS84 de chaque couche, lue dans GeoServer (zoom sur la couche dans MapStore)."""
    gs, e = geoserver(), {}
    for c in COUCHES:
        ft = gs.json("GET", f"/workspaces/{ESPACE}/datastores/{ENTREPOT}/featuretypes/{c['nom']}.json")["featureType"]
        b = ft["latLonBoundingBox"]
        e[c["nom"]] = (b["minx"], b["miny"], b["maxx"], b["maxy"])
    return e


def publier_carte(r, e):
    conf = carte.config_carte(e)
    attributs = {**r.presentation(NOM_CARTE, PRESENTATION_CARTE),
                 **r.vignette(NOM_CARTE, COUCHES_VIGNETTE, carte.emprise_cercle(10, 1.0))}
    rid = r.enregistrer("MAP", NOM_CARTE,
                        "Réseaux électriques, installations classées, production et zonages environnementaux "
                        "autour du CNPE de Penly (Petit-Caux), dans des cercles de 2 à 20 km.", conf, attributs)
    print(f"carte {rid} : #/viewer/{rid}")
    return rid, conf, attributs


def publier_application(r, conf, attributs_carte, carte_id):
    donnees = application.contexte(conf, carte_id)
    rid = r.enregistrer("CONTEXT", application.NOM,
                        "Application cartographique dédiée : SIG chantier Penly, contraintes autour du CNPE.",
                        donnees, {"thumbnail": attributs_carte["thumbnail"], "title": "SIG chantier Penly"})
    print(f"application {rid} : #/context/{application.NOM}/{carte_id}")
    return rid


def adresses(r):
    """Adresses des pages publiées (leurs identifiants dépendent de l'instance), affichées et écrites dans
    adresses.json pour l'outil de captures d'écran."""
    carte_id = r.chercher("MAP", NOM_CARTE)
    if not carte_id:
        sys.exit("carte absente : lancer d'abord python 05_mapstore/03_publier_mapstore.py")
    pages = {"application": f"#/context/{application.NOM}/{carte_id}", "carte": f"#/viewer/{carte_id}"}
    print("\nAdresses :")
    for nom, ancre in pages.items():
        print(f"  {nom:12} {MAPSTORE}/{ancre}")
    (ICI / "adresses.json").write_text(json.dumps({"base": f"{MAPSTORE}/", "pages": pages}, indent=2),
                                       encoding="utf-8")


def main(quoi="tout"):
    r = Ressources(mapstore())
    if quoi != "adresses":
        carte_id, conf, attributs = publier_carte(r, emprises())
        publier_application(r, conf, attributs, carte_id)
    adresses(r)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tout")
