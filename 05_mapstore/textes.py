"""Textes affichés dans MapStore : fiche de présentation de la carte (panneau « Détails »)."""
from commun import CARTE_WEB, DEPOT

STYLE = "font-family:Segoe UI,Arial,sans-serif;font-size:14px;line-height:1.55;color:#2f241d"


def _chiffres(lignes):
    corps = "".join(
        f'<tr><td style="padding:3px 12px 3px 0;text-align:right;font-weight:700;font-size:16px;'
        f'color:{c};white-space:nowrap">{n}</td><td style="padding:3px 0">{lib}</td></tr>' for n, lib, c in lignes)
    return f'<table style="border-collapse:collapse;margin:8px 0 14px">{corps}</table>'


def _lien(url):
    return f'<a href="{url}" target="_blank" rel="noopener" style="color:#2f241d">{url.replace("https://", "")}</a>'


PRESENTATION_CARTE = f"""
<div style="{STYLE}">
<p style="margin:0;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#6f5f51">SIG de chantier · données ouvertes</p>
<h2 style="margin:4px 0 2px;font-size:22px">Contraintes autour du CNPE de Penly</h2>
<p style="margin:0 0 12px;color:#5a4a3d">Petit-Caux, Seine-Maritime · exploitant EDF</p>
<p>Ce qui entoure le site de Penly avant tout chantier : réseaux électriques de transport et de distribution,
installations classées, production d'électricité, zonages environnementaux et référentiel cadastral, dans des
cercles de 2, 5, 10 et 20 km.</p>
{_chiffres([
    ("2 × 1 330 MW", "deux tranches en service depuis 1990 et 1992", "#2f241d"),
    ("400 kV", "tension des lignes d'évacuation", "#c8385a"),
    ("9 ICPE", "à moins de 5 km, hors 1 position douteuse", "#2f241d"),
    ("20 km", "rayon du plan particulier d'intervention (PPI)", "#5a4a3d"),
])}
<h3 style="font-size:15px;margin:14px 0 4px">Lire la carte</h3>
<ul style="padding-left:18px;margin:0">
<li><b>Table des matières</b> : sept groupes, du site au référentiel. La légende de chaque couche s'affiche
sous son nom ; pylônes, réseau BT, poteaux, bâtiments et parcelles n'apparaissent qu'en zoomant.</li>
<li><b>Un clic</b> sur un objet ouvre sa fiche : distance au CNPE, tension, régime ICPE, lien Géorisques ou INPN.</li>
<li><b>Installations classées</b> : un anneau carmin signale une position douteuse (la commune déclarée au
registre n'est pas celle où tombe le point) ; sa distance au CNPE n'est alors pas fiable.</li>
<li>Les <b>signets</b> mènent aux cercles de 2, 5, 10 et 20 km, à Dieppe et au Tréport.</li>
</ul>
<p style="margin:12px 0;padding:8px 10px;background:#faf8f3;border-left:3px solid #9a8470;font-size:12.5px">
Deux réacteurs supplémentaires sont en projet sur le site (débat public CNDP 2022-2023). Leurs emprises de
chantier ne sont pas publiques : elles ne figurent pas sur la carte. Projet personnel de démonstration, sur
données ouvertes uniquement.</p>
<p style="font-size:12px;color:#5a4a3d;margin:0">Sources : EDF (opendata.edf.fr) ; IGN, BD TOPO et Géoplateforme ;
Enedis open data ; Agence ORE ; Géorisques ; INPN, PatriNat (MNHN) ; cadastre Etalab (DGFiP).<br>
Chaîne de traitement (QGIS, PostGIS, GeoServer) : {_lien(DEPOT)}<br>
Même carte en version web (MapLibre) : {_lien(CARTE_WEB)}</p>
</div>
"""
