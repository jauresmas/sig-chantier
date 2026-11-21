"""Paramètres et outils communs à la publication du SIG chantier Penly dans MapStore.

La pile MapStore (MapStore + GeoServer + nginx sous Docker, PostgreSQL/PostGIS sur la machine) est un
dépôt à part : son dossier est donné par MAPSTORE_PILE (fichier 05_mapstore/.env). Ses comptes admin sont
lus dans son propre .env ; le mot de passe du rôle PostgreSQL « penly » est dans 05_mapstore/.env.
Aucun mot de passe n'est écrit dans ces scripts ni affiché. Bibliothèque standard uniquement.
"""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from functools import cache
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent                                   # racine du dépôt sig-chantier-penly
GPKG = RACINE / "02_donnees" / "penly_sig.gpkg"
ENV_LOCAL = ICI / ".env"


def lire_env(fichier):
    valeurs = {}
    if fichier.exists():
        for ligne in fichier.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if ligne and not ligne.startswith("#") and "=" in ligne:
                cle, val = ligne.split("=", 1)
                valeurs[cle.strip()] = val.strip()
    return valeurs


@cache
def env():
    """Variables de 05_mapstore/.env, puis celles du .env de la pile MapStore (comptes admin)."""
    local = lire_env(ENV_LOCAL)
    pile = os.environ.get("MAPSTORE_PILE") or local.get("MAPSTORE_PILE")
    return {**(lire_env(Path(pile) / ".env") if pile else {}), **local}


def compte_admin(cle):
    """Mot de passe admin de la pile (GEOSERVER_ADMIN_PASSWORD, MAPSTORE_ADMIN_PASSWORD)."""
    if not env().get(cle):
        sys.exit(f"{cle} introuvable : renseigner MAPSTORE_PILE (dossier de la pile et de son .env) "
                 f"dans {ENV_LOCAL}")
    return env()[cle]


def parametre(cle, defaut=None):
    return os.environ.get(cle) or env().get(cle) or defaut


def _version(chemin):
    return [int(n) for n in re.findall(r"\d+", chemin.name)] or [0]


def _qgis():
    if valeur := parametre("QGIS_DIR"):
        return Path(valeur)
    installes = sorted(Path(os.environ.get("ProgramFiles", r"C:\Program Files")).glob("QGIS 3*"), key=_version)
    return installes[-1] if installes else None


def _psql():
    if valeur := parametre("PSQL"):
        return Path(valeur)
    if chemin := shutil.which("psql"):
        return Path(chemin)
    racine = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "PostgreSQL"
    installes = sorted((p.parents[1] for p in racine.glob("*/bin/psql.exe")), key=_version)
    return installes[-1] / "bin" / "psql.exe" if installes else Path("psql")


QGIS = _qgis()
PSQL = _psql()

# Base des couches publiées (créée par 00_creer_base.py) : schéma brut = import du GeoPackage,
# schéma carto = tables mises en forme pour la carte (sql/carto.sql), seules publiées par GeoServer
PG = {"host": "localhost", "port": 5432, "dbname": "penly_carto", "user": "penly"}
PG_DEPUIS_DOCKER = "host.docker.internal"

BASE_URL = parametre("PILE_URL", "http://localhost:8097").rstrip("/")
GEOSERVER = f"{BASE_URL}/geoserver"
MAPSTORE = f"{BASE_URL}/mapstore"
ESPACE = "penly"                                      # espace de travail GeoServer
ENTREPOT = "carto"                                    # entrepôt PostGIS
DEPOT = "https://github.com/jauresmas/sig-chantier-penly"
CARTE_WEB = "https://jauresmas.github.io/sig-chantier-penly/"


def mot_de_passe_base():
    mdp = env().get("PENLY_DB_PASSWORD")
    if not mdp:
        sys.exit("PENLY_DB_PASSWORD absent : lancer d'abord python 05_mapstore/00_creer_base.py")
    return mdp


def psql(sql, base=None, utilisateur=None, variables=None):
    """Exécute du SQL (entrée standard, UTF-8 : un argument -c passerait par la page de code Windows)."""
    environnement = dict(os.environ, PGCLIENTENCODING="UTF8", **(variables or {}))
    if utilisateur is None:
        environnement["PGPASSWORD"] = mot_de_passe_base()
    r = subprocess.run([str(PSQL), "-h", PG["host"], "-p", str(PG["port"]), "-U", utilisateur or PG["user"],
                        "-d", base or PG["dbname"], "-v", "ON_ERROR_STOP=1", "-At", "-q", "-f", "-"],
                       input=sql, env=environnement, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(r.stderr)
    return r.stdout.strip()


def ogr2ogr(source, couches, schema, *options):
    environnement = dict(os.environ, PGPASSWORD=mot_de_passe_base(), PGCLIENTENCODING="UTF8")
    if QGIS:
        environnement.update(PATH=f"{QGIS / 'bin'}{os.pathsep}{os.environ['PATH']}",
                             GDAL_DATA=str(QGIS / "apps" / "gdal" / "share" / "gdal"),
                             PROJ_LIB=str(QGIS / "share" / "proj"))
        programme = str(QGIS / "bin" / "ogr2ogr.exe")
    else:
        programme = shutil.which("ogr2ogr") or sys.exit("ogr2ogr introuvable : installer QGIS ou renseigner QGIS_DIR")
    cible = f"PG:host={PG['host']} port={PG['port']} dbname={PG['dbname']} user={PG['user']}"
    subprocess.run([programme, "-f", "PostgreSQL", cible, str(source), *couches, "-overwrite",
                    "-lco", f"SCHEMA={schema}", "-lco", "GEOMETRY_NAME=geom", "-lco", "FID=fid",
                    "-lco", "SPATIAL_INDEX=GIST", "-lco", "PRECISION=NO", "--config", "PG_USE_COPY", "YES", *options],
                   env=environnement, check=True)


class Http:
    """Client REST minimal avec authentification Basic."""

    def __init__(self, base, utilisateur, mot_de_passe):
        self.base = base.rstrip("/")
        jeton = base64.b64encode(f"{utilisateur}:{mot_de_passe}".encode()).decode()
        self.entetes = {"Authorization": f"Basic {jeton}"}

    def requete(self, methode, chemin, corps=None, type_contenu="application/json", accepter="application/json",
                ok=(200, 201)):
        url = chemin if chemin.startswith("http") else f"{self.base}{chemin}"
        if isinstance(corps, (dict, list)):
            corps = json.dumps(corps, ensure_ascii=False)
        donnees = corps.encode("utf-8") if isinstance(corps, str) else corps
        entetes = dict(self.entetes, Accept=accepter)
        if donnees is not None:
            entetes["Content-Type"] = type_contenu
        req = urllib.request.Request(url, data=donnees, method=methode, headers=entetes)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                texte, statut = r.read().decode("utf-8", "replace"), r.status
        except urllib.error.HTTPError as e:
            texte, statut = e.read().decode("utf-8", "replace"), e.code
        if ok and statut not in ok:
            raise RuntimeError(f"{methode} {url} -> HTTP {statut}\n{texte[:1500]}")
        return statut, texte

    def json(self, methode, chemin, corps=None, **kw):
        _, texte = self.requete(methode, chemin, corps, **kw)
        return json.loads(texte) if texte.strip().startswith(("{", "[")) else texte

    def existe(self, chemin):
        statut, _ = self.requete("GET", chemin, ok=None)
        return statut == 200


def geoserver():
    return Http(f"{GEOSERVER}/rest", "admin", compte_admin("GEOSERVER_ADMIN_PASSWORD"))


def mapstore():
    return Http(f"{MAPSTORE}/rest/geostore", "admin", compte_admin("MAPSTORE_ADMIN_PASSWORD"))
