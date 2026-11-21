"""Création et mise à jour des ressources MapStore (API GeoStore) : carte, application (contexte), fiche
de présentation (DETAILS) et vignette (THUMBNAIL), en lecture publique. Les ressources sont retrouvées par
catégorie et par nom : relancer met à jour sans dupliquer. Repris de la chaîne de la pile MapStore.
"""
import base64
import json
import math
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

from commun import ESPACE, GEOSERVER


def cdata(texte):
    return "<![CDATA[" + texte.replace("]]>", "]]]]><![CDATA[>") + "]]>"


class Ressources:
    def __init__(self, ms):
        self.ms = ms
        groupes = ms.json("GET", "/usergroups?all=true")["UserGroupList"]["UserGroup"]
        groupes = groupes if isinstance(groupes, list) else [groupes]
        self.tout_le_monde = next(g["id"] for g in groupes if g["groupName"] == "everyone")
        self.admin = ms.json("GET", "/users/user/details")["User"]["id"]

    def chercher(self, categorie, nom):
        statut, texte = self.ms.requete(
            "GET", f"/misc/category/name/{categorie}/resource/name/{urllib.parse.quote(nom)}", ok=None)
        return json.loads(texte)["Resource"]["id"] if statut == 200 else None

    def enregistrer(self, categorie, nom, description, donnees, attributs=None):
        """Crée ou met à jour une ressource ; renvoie son identifiant."""
        texte = donnees if isinstance(donnees, str) else json.dumps(donnees, ensure_ascii=False)
        rid = self.chercher(categorie, nom)
        if rid is None:
            attrs = "".join(f"<attribute><name>{escape(k)}</name><type>STRING</type><value>{escape(v)}</value>"
                            f"</attribute>" for k, v in (attributs or {}).items())
            xml = (f"<Resource><description>{escape(description)}</description><metadata></metadata>"
                   f"<name>{escape(nom)}</name><category><name>{categorie}</name></category>"
                   f"<store><data>{cdata(texte)}</data></store>"
                   f"{'<Attributes>' + attrs + '</Attributes>' if attrs else ''}</Resource>")
            _, rid = self.ms.requete("POST", "/resources", xml, type_contenu="application/xml", accepter="text/plain")
            rid = int(rid)
        else:
            self.ms.requete("PUT", f"/resources/resource/{rid}",
                            f"<Resource><description>{escape(description)}</description>"
                            f"<name>{escape(nom)}</name></Resource>", type_contenu="application/xml",
                            accepter="*/*", ok=(200, 201, 204))
            self.ms.requete("PUT", f"/data/{rid}", texte,
                            type_contenu="application/json" if not isinstance(donnees, str) else "text/plain",
                            accepter="*/*", ok=(200, 201, 204))
            for k, v in (attributs or {}).items():
                self.ms.requete("PUT", f"/resources/resource/{rid}/attributes/",
                                {"restAttribute": {"name": k, "value": v}}, accepter="*/*", ok=(200, 201, 204))
        self.public(rid)
        return rid

    def public(self, rid):
        """Lecture pour tous (groupe everyone, visiteurs anonymes compris), écriture pour l'administrateur."""
        xml = ("<SecurityRuleList>"
               f"<SecurityRule><canRead>true</canRead><canWrite>true</canWrite>"
               f"<user><id>{self.admin}</id><name>admin</name></user></SecurityRule>"
               f"<SecurityRule><canRead>true</canRead><canWrite>false</canWrite>"
               f"<group><id>{self.tout_le_monde}</id><groupName>everyone</groupName></group></SecurityRule>"
               "</SecurityRuleList>")
        self.ms.requete("POST", f"/resources/resource/{rid}/permissions", xml, type_contenu="application/xml",
                        accepter="*/*", ok=(200, 201, 204))

    @staticmethod
    def lien_donnees(rid):
        return f"rest/geostore/data/{rid}/raw?decode=datauri"

    def presentation(self, nom, html, a_l_ouverture=True):
        """Fiche de présentation (DETAILS) ; renvoie les attributs à poser sur la ressource."""
        rid = self.enregistrer("DETAILS", f"{nom} · présentation", "", html)
        return {"details": self.lien_donnees(rid),
                "detailsSettings": json.dumps({"showAsModal": False, "showAtStartup": a_l_ouverture})}

    def vignette(self, nom, couches, bbox, largeur=640, hauteur=400):
        """Vignette : rendu WMS du GeoServer de la pile, stocké en data URI. bbox en degrés (ouest, sud, est,
        nord), rendue en Web Mercator comme la carte et élargie aux proportions de l'image."""
        def merc(lon, lat):
            return lon * 20037508.34 / 180, math.log(math.tan(math.radians(90 + lat) / 2)) * 6378137
        (x0, y0), (x1, y1) = merc(bbox[0], bbox[1]), merc(bbox[2], bbox[3])
        cx, cy, dx, dy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        dx, dy = max(dx, dy * largeur / hauteur), max(dy, dx * hauteur / largeur)
        q = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "STYLES": "", "SRS": "EPSG:3857",
             "LAYERS": ",".join(f"{ESPACE}:{c}" for c in couches),
             "BBOX": ",".join(f"{v:.0f}" for v in (cx - dx, cy - dy, cx + dx, cy + dy)),
             "WIDTH": largeur, "HEIGHT": hauteur, "FORMAT": "image/png", "TRANSPARENT": "false",
             "BGCOLOR": "0xFAF8F3", "FORMAT_OPTIONS": "antialiasing:full"}
        with urllib.request.urlopen(f"{GEOSERVER}/wms?{urllib.parse.urlencode(q)}", timeout=180) as r:
            png = r.read()
        uri = "data:image/png;base64," + base64.b64encode(png).decode()
        rid = self.enregistrer("THUMBNAIL", f"{nom} · vignette", "", uri)
        return {"thumbnail": self.lien_donnees(rid)}
