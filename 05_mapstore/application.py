"""Application dédiée (contexte MapStore) : les outils du visualiseur standard de la version installée,
sans ceux qui ne servent pas ici, avec le bandeau, les couleurs et la légende du projet.
"""
import base64
import json
import urllib.request

from commun import MAPSTORE

NOM = "sig-chantier"

# Impression (module absent de l'image MapStore), 3D, temps, tutoriel, annotations, téléchargement WPS et
# enregistrement (l'application est en lecture ; l'administrateur garde la carte source)
RETIRES = {"Tutorial", "Print", "HelpLink", "Annotations", "GlobeViewSwitcher", "Timeline", "Playback",
           "LayerDownload", "CRSSelector", "Save", "SaveAs", "DeleteResource", "AutoMapUpdate"}

LEGENDE = {"WMSLegendOptions": "forceLabels:on;fontName:Segoe UI;fontSize:11;fontAntiAliasing:true;"
                               "fontColor:0x2F241D;dx:6;dy:0.2;mx:0.05;my:0.15;bgColor:0xFFFFFF",
           "scaleDependent": True, "legendWidth": 20, "legendHeight": 20}

# Encre sépia de la carte web, contrastes AA sur blanc
THEME = {"variables": {"ms-main-color": "#2f241d", "ms-main-bg": "#ffffff",
                       "ms-primary": "#2f241d", "ms-primary-contrast": "#faf8f3",
                       "ms-success": "#5d7d47", "ms-success-contrast": "#ffffff"}}


def logo():
    """Logotype du bandeau : le symbole du CNPE de la carte web et le titre du projet."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="440" height="44" viewBox="0 0 440 44">
<circle cx="20" cy="22" r="11" fill="#faf8f3" stroke="#2f241d" stroke-width="2"/>
<circle cx="20" cy="22" r="5" fill="#c8385a"/>
<text x="42" y="20" font-family="Segoe UI, Arial, sans-serif" font-size="17" font-weight="700" fill="#2f241d">SIG chantier</text>
<text x="42" y="37" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#5a4a3d">Contraintes autour du CNPE de Penly · Petit-Caux (76)</text>
</svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def plugins_standard():
    with urllib.request.urlopen(f"{MAPSTORE}/configs/localConfig.json", timeout=60) as r:
        return json.load(r)["plugins"]["desktop"]


def adapter(p, carte_id=None):
    p = {"name": p} if isinstance(p, str) else json.loads(json.dumps(p))
    cfg = p.setdefault("cfg", {})
    if p["name"] == "TOC":
        cfg.setdefault("layerOptions", {})["legendOptions"] = LEGENDE
    elif p["name"] == "BrandNavbar":
        cfg["logo"] = {"src": logo(), "href": f"#/context/{NOM}" + (f"/{carte_id}" if carte_id else ""),
                       "style": {"height": "2.4rem"}}
    elif p["name"] == "Identify":
        cfg["showEdit"] = False
        cfg["showHighlightFeatureButton"] = True
    elif p["name"] == "Measure":
        cfg.setdefault("defaultOptions", {})["showAddAsAnnotation"] = False
    if not cfg:
        p.pop("cfg")
    return p


def contexte(config_carte, carte_id=None):
    plugins = [adapter(p, carte_id) for p in plugins_standard()
               if (p if isinstance(p, str) else p["name"]) not in RETIRES]
    return {"windowTitle": "SIG chantier", "mapConfig": config_carte, "theme": THEME,
            "customVariablesEnabled": True, "plugins": {"desktop": plugins}, "userPlugins": [], "templates": []}
