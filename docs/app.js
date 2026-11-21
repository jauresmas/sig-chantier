/* SIG chantier : carte web (MapLibre GL JS, sans compilation).
   Données : docs/data/*.geojson, produites par scripts/05_exporter_web.py. */
"use strict";

const C = {
  encre: "#2f241d", papier: "#faf8f3", carmin: "#c8385a", bleu: "#4f7fb0",
  vert: "#8fae74", vertFonce: "#5d7d47", sepia: "#9a8470",
};
const ANNEAUX = [2, 5, 10, 20];
const MOUVEMENT_REDUIT = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const ECRAN_ETROIT = window.matchMedia("(max-width: 760px)");
const easeOutExpo = (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));

// Séparateur de milliers en espace insécable classique : l'espace fine (U+202F) d'Intl disparaît en gras tabulaire.
const formateur = (options) => {
  const f = new Intl.NumberFormat("fr-FR", options);
  return { format: (v) => f.format(v).replace(/ /g, " ") };
};
const nf0 = formateur({ maximumFractionDigits: 0 });
const nf1 = formateur({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
const NBSP = " ";
const $ = (sel) => document.querySelector(sel);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const sansAccents = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function distanceTexte(m) {
  if (m == null) return "";
  if (m < 1000) return `${nf0.format(Math.round(m / 10) * 10)}${NBSP}m`;
  return `${(m < 10000 ? nf1 : nf0).format(m / 1000)}${NBSP}km`;
}
function puissanceTexte(kw) {
  if (kw == null) return "non renseignée";
  const [v, u] = kw >= 1000 ? [kw / 1000, "MW"] : [kw, "kW"];
  return `${(v >= 100 ? nf0 : nf1).format(v)}${NBSP}${u}`;
}
const POSE = { "aérien": "aérienne", souterrain: "souterraine" };
function dateTexte(v) {
  const m = /^(\d{4})[-/](\d{2})[-/](\d{2})/.exec(String(v ?? ""));
  return m ? `${m[3]}/${m[2]}/${m[1]}` : v || "non renseignée";
}
function ouiNon(v) {
  if (v === true || v === 1 || v === "1" || v === "true") return "oui";
  if (v === false || v === 0 || v === "0" || v === "false") return "non";
  return "non renseigné";
}

/* Lambert-93 (RGF93, conique conforme sécante, ellipsoïde GRS80) */
const L93 = (() => {
  const a = 6378137, e = 0.0818191910428158, rad = Math.PI / 180;
  const m = (p) => Math.cos(p) / Math.sqrt(1 - e * e * Math.sin(p) ** 2);
  const t = (p) => Math.tan(Math.PI / 4 - p / 2) / Math.pow((1 - e * Math.sin(p)) / (1 + e * Math.sin(p)), e / 2);
  const p1 = 49 * rad, p2 = 44 * rad, p0 = 46.5 * rad, l0 = 3 * rad;
  const n = Math.log(m(p1) / m(p2)) / Math.log(t(p1) / t(p2));
  const F = m(p1) / (n * Math.pow(t(p1), n));
  const r0 = a * F * Math.pow(t(p0), n);
  return (lon, lat) => {
    const r = a * F * Math.pow(t(lat * rad), n), th = n * (lon * rad - l0);
    return [700000 + r * Math.sin(th), 6600000 + r0 - r * Math.cos(th)];
  };
})();

function haversine([lon1, lat1], [lon2, lat2]) {
  const R = 6371008.8, rad = Math.PI / 180;
  const dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

function echelleDenominateur(zoom, lat) {
  const mpp = (40075016.686 * Math.cos((lat * Math.PI) / 180)) / (512 * 2 ** zoom);
  const d = mpp / (0.0254 / 96);
  const p = 10 ** Math.floor(Math.log10(d) - 1);
  return Math.round(d / p) * p;
}

/* Fonds IGN (Géoplateforme, WMTS en tuiles XYZ) */
function wmts(couche, style, format) {
  return "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0" +
    `&LAYER=${couche}&STYLE=${encodeURIComponent(style)}&TILEMATRIXSET=PM&FORMAT=${format}` +
    "&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}";
}
const ATTRIB_IGN = 'Fonds © <a href="https://geoservices.ign.fr/" target="_blank" rel="noopener">IGN, Géoplateforme</a>';
const FONDS = {
  plan: { nom: "Plan IGN", calques: ["fond-plan"] },
  ortho: { nom: "Photographies aériennes", calques: ["fond-ortho"] },
  cadastre: { nom: "Plan cadastral", calques: ["fond-plan", "fond-cadastre"] },
};

/* Pastilles de légende : chaque pastille reprend le symbole dessiné sur la carte */
const P = {
  ligne: (c, w, dash = "") => `<svg viewBox="0 0 26 16" aria-hidden="true"><path d="M2 8h22" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${dash ? `stroke-dasharray="${dash}"` : ""} fill="none"/></svg>`,
  double: (c1, w1, c2, w2, dash2) => `<svg viewBox="0 0 26 16" aria-hidden="true"><path d="M2 5h22" stroke="${c1}" stroke-width="${w1}" stroke-linecap="round"/><path d="M2 11h22" stroke="${c2}" stroke-width="${w2}" stroke-dasharray="${dash2}" stroke-linecap="round"/></svg>`,
  lavis: (c, o, trait, dash = "") => `<svg viewBox="0 0 26 16" aria-hidden="true"><rect x="2" y="2" width="22" height="12" fill="${c}" fill-opacity="${o}" stroke="${trait}" stroke-width="1.2" ${dash ? `stroke-dasharray="${dash}"` : ""}/></svg>`,
  hachures: () => `<svg viewBox="0 0 26 16" aria-hidden="true"><defs><pattern id="ph" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0v5" stroke="${C.bleu}" stroke-width="1.4"/></pattern></defs><rect x="2" y="2" width="22" height="12" fill="url(#ph)" stroke="${C.bleu}" stroke-width="1.2"/></svg>`,
  cercles: () => `<svg viewBox="0 0 26 16" aria-hidden="true"><circle cx="13" cy="8" r="6" fill="none" stroke="${C.encre}" stroke-width="1.2" stroke-dasharray="3 2"/></svg>`,
  site: () => `<svg viewBox="0 0 26 16" aria-hidden="true"><circle cx="13" cy="8" r="6.5" fill="${C.papier}" stroke="${C.encre}" stroke-width="1.4"/><circle cx="13" cy="8" r="3.2" fill="${C.carmin}"/></svg>`,
  triangle: () => `<svg viewBox="0 0 26 16" aria-hidden="true"><path d="M13 3.5 18 12.5H8z" fill="${C.papier}" stroke="${C.bleu}" stroke-width="1.5" stroke-linejoin="round"/></svg>`,
  carre: (c) => `<svg viewBox="0 0 26 16" aria-hidden="true"><rect x="10.5" y="5.5" width="5" height="5" fill="${C.papier}" stroke="${c}" stroke-width="1.4"/></svg>`,
  point: (c) => `<svg viewBox="0 0 26 16" aria-hidden="true"><circle cx="13" cy="8" r="2.4" fill="${c}" stroke="${C.papier}" stroke-width=".8"/></svg>`,
  losanges: () => `<svg viewBox="0 0 26 16" aria-hidden="true"><path d="M8 3.5l4.5 4.5L8 12.5 3.5 8z" fill="${C.encre}"/><path d="M18 3.5l4.5 4.5-4.5 4.5L13.5 8z" fill="${C.papier}" stroke="${C.encre}" stroke-width="1.4"/></svg>`,
  proportionnels: () => `<svg viewBox="0 0 26 16" aria-hidden="true"><circle cx="9" cy="8" r="6" fill="${C.papier}" fill-opacity=".6" stroke="${C.encre}" stroke-width="1.3"/><circle cx="20" cy="10" r="3" fill="${C.papier}" fill-opacity=".6" stroke="${C.encre}" stroke-width="1.3"/></svg>`,
  limite: () => `<svg viewBox="0 0 26 16" aria-hidden="true"><path d="M2 8h22" stroke="${C.encre}" stroke-opacity=".6" stroke-width="1" stroke-dasharray="5 2 1 2"/></svg>`,
};

/* Catalogue des couches : libellés, symboles, calques MapLibre, contenu des fiches */
const COUCHES = {
  cnpe: {
    libelle: "CNPE de Penly", pastille: P.site(), calques: ["cnpe-point"],
    titre: () => "CNPE de Penly",
  },
  cercles: {
    libelle: "Cercles 2 / 5 / 10 / 20 km", pastille: P.cercles(), calques: ["cercles-trait"],
    titre: (p) => `Cercle de ${p.rayon_km} km`,
    champs: [["libelle", "Usage"]],
    pasDeDistance: true,
  },
  htb_lignes: {
    libelle: "Lignes 400 kV et 90 kV", pastille: P.double(C.carmin, 3.2, C.carmin, 1.6, "0"), calques: ["htb-lignes"],
    titre: (p) => `Ligne électrique ${p.tension || "HTB"}`,
    champs: [["tension", "Tension"], ["gestionnaire", "Gestionnaire"], ["etat", "État"], ["id_ign", "Identifiant BD TOPO"]],
  },
  htb_postes: {
    libelle: "Postes électriques HTB", pastille: P.lavis(C.carmin, 0.3, C.carmin), calques: ["htb-postes-lavis"],
    titre: (p) => p.nom || "Poste électrique HTB",
    champs: [["importance", "Importance BD TOPO (1 à 5)"], ["id_ign", "Identifiant BD TOPO"]],
  },
  htb_pylones: {
    libelle: "Pylônes", pastille: P.carre(C.carmin), calques: ["htb-pylones-point"], minzoom: 12,
    titre: (p) => (p.numero ? `Pylône n° ${p.numero}` : "Pylône HTB"),
    champs: [["hauteur_m", "Hauteur (m)"], ["id_ign", "Identifiant BD TOPO"]],
  },
  hta: {
    libelle: "Réseau HTA", pastille: P.double(C.bleu, 2.2, C.bleu, 1.6, "3 2.5"), calques: ["hta-aerien", "hta-souterrain"],
    titre: (p) => `Ligne HTA ${POSE[p.pose] || ""}`,
    champs: [["pose", "Pose"], ["commune", "Commune"]],
  },
  postes_hta_bt: {
    libelle: "Postes HTA/BT", pastille: P.triangle(), calques: ["postes-hta-bt-point"], minzoom: 12.5,
    titre: () => "Poste HTA/BT",
    champs: [["commune", "Commune"]],
  },
  bt: {
    libelle: "Réseau BT", pastille: P.double(C.bleu, 1.2, C.bleu, 1, "2 2"), calques: ["bt-aerien", "bt-souterrain"], minzoom: 13,
    titre: (p) => `Ligne BT ${POSE[p.pose] || ""}`,
    champs: [["pose", "Pose"], ["commune", "Commune"]],
  },
  poteaux: {
    libelle: "Poteaux HTA et BT", pastille: P.point(C.bleu), calques: ["poteaux-point"], minzoom: 14.5,
    titre: () => "Poteau HTA ou BT",
    champs: [["commune", "Commune"]],
  },
  production: {
    libelle: "Puissance installée par commune", pastille: P.proportionnels(), calques: ["production-cercle"],
    titre: (p) => `Production à ${p.commune}`,
    distanceLibelle: "du centre de la commune au CNPE",
  },
  znieff1: {
    libelle: "ZNIEFF de type 1", pastille: P.lavis(C.vert, 0.45, C.vertFonce), calques: ["znieff1-lavis"],
    titre: (p) => p.nom || "ZNIEFF de type 1",
    champs: [["id_mnhn", "Identifiant national"]], lien: (p) => [p.fiche, "Fiche INPN"],
  },
  znieff2: {
    libelle: "ZNIEFF de type 2", pastille: P.lavis(C.vert, 0.18, C.vertFonce, "3 2"), calques: ["znieff2-lavis"],
    titre: (p) => p.nom || "ZNIEFF de type 2",
    champs: [["id_mnhn", "Identifiant national"]], lien: (p) => [p.fiche, "Fiche INPN"],
  },
  natura2000: {
    libelle: "Natura 2000", pastille: P.hachures(), calques: ["natura2000-hachures"],
    titre: (p) => p.nom || "Site Natura 2000",
    champs: [["directive", "Directive"], ["id_mnhn", "Identifiant national"]], lien: (p) => [p.fiche, "Fiche INPN"],
  },
  conservatoire: {
    libelle: "Conservatoire du littoral", pastille: P.lavis(C.sepia, 0.3, C.encre, "1 2"), calques: ["conservatoire-lavis"],
    titre: (p) => p.nom || "Terrain du Conservatoire du littoral",
    champs: [["id_mnhn", "Identifiant"]],
  },
  icpe: {
    libelle: "Installations classées (ICPE)", pastille: P.losanges(), calques: ["icpe-point"],
    titre: (p) => p.nom || "Installation classée",
    champs: [["regime_libelle", "Régime"], ["activite", "Activité"], ["adresse", "Adresse"], ["commune", "Commune"],
      ["derniere_inspection", "Dernière inspection", dateTexte], ["priorite_nationale", "Priorité nationale", ouiNon],
      ["code_aiot", "Code AIOT"],
      ["controle_position", "Contrôle de position", (v, p) => (v === "écart" ? `écart : le point tombe à ${p.commune_position}` : v === "conforme" ? "conforme à la commune déclarée" : v || "non contrôlé")]],
    lien: (p) => [p.fiche, "Fiche Géorisques"],
  },
  communes: {
    libelle: "Limites communales", pastille: P.limite(), calques: ["communes-limite"], interrogeable: ["communes-prise"],
    titre: (p) => p.nom,
    champs: [["code_insee", "Code INSEE"], ["population", "Population", (v) => (v == null ? "non renseignée" : nf0.format(v))]],
    distanceLibelle: "de la limite communale au CNPE",
  },
};

const GROUPES = [
  { titre: "Site et zonages", couches: ["cnpe", "cercles"] },
  { titre: "Transport HTB", couches: ["htb_lignes", "htb_postes", "htb_pylones"] },
  { titre: "Distribution", couches: ["hta", "postes_hta_bt", "bt", "poteaux"] },
  { titre: "Production", couches: ["production"] },
  { titre: "Environnement et risques", couches: ["znieff1", "znieff2", "natura2000", "conservatoire", "icpe"] },
  { titre: "Référentiel", couches: ["communes"] },
];

/* Priorité de sélection au clic : les points d'abord, les surfaces ensuite */
const ORDRE_CLIC = ["cnpe", "icpe", "production", "htb_pylones", "postes_hta_bt", "poteaux", "htb_postes",
  "htb_lignes", "hta", "bt", "conservatoire", "natura2000", "znieff1", "znieff2", "cercles", "communes"];

/* Calques de la carte, de bas en haut */
function calquesDonnees() {
  const rond = { "line-cap": "round", "line-join": "round" };
  const poly = ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]];
  const pts = ["in", ["geometry-type"], ["literal", ["Point", "MultiPoint"]]];
  const pose = (v) => ["==", ["get", "pose"], v];
  return [
    { id: "communes-prise", type: "fill", source: "communes", paint: { "fill-color": C.encre, "fill-opacity": 0 } },
    { id: "communes-limite", type: "line", source: "communes", paint: { "line-color": C.encre, "line-opacity": 0.42, "line-width": 0.9, "line-dasharray": [6, 2, 1, 2] } },
    { id: "znieff2-lavis", type: "fill", source: "znieff2", paint: { "fill-color": C.vert, "fill-opacity": 0.13 } },
    { id: "znieff2-trait", type: "line", source: "znieff2", paint: { "line-color": C.vertFonce, "line-width": 1, "line-opacity": 0.75, "line-dasharray": [3, 2] } },
    { id: "znieff1-lavis", type: "fill", source: "znieff1", paint: { "fill-color": C.vert, "fill-opacity": 0.3 } },
    { id: "znieff1-trait", type: "line", source: "znieff1", paint: { "line-color": C.vertFonce, "line-width": 1.1, "line-opacity": 0.85 } },
    { id: "natura2000-hachures", type: "fill", source: "natura2000", paint: { "fill-pattern": ["match", ["get", "directive"], "Oiseaux (ZPS)", "hachure-zps", "hachure-zsc"] } },
    { id: "natura2000-trait", type: "line", source: "natura2000", paint: { "line-color": C.bleu, "line-width": 1.2 } },
    { id: "conservatoire-lavis", type: "fill", source: "conservatoire", paint: { "fill-color": C.sepia, "fill-opacity": 0.2 } },
    { id: "conservatoire-trait", type: "line", source: "conservatoire", paint: { "line-color": C.encre, "line-width": 1.1, "line-dasharray": [1, 2] }, layout: rond },
    { id: "htb-postes-lavis", type: "fill", source: "htb_postes", paint: { "fill-color": C.carmin, "fill-opacity": 0.3 } },
    { id: "htb-postes-trait", type: "line", source: "htb_postes", paint: { "line-color": C.carmin, "line-width": 1.2 } },
    { id: "bt-souterrain", type: "line", source: "bt", minzoom: 13, filter: pose("souterrain"), layout: rond,
      paint: { "line-color": C.bleu, "line-opacity": 0.7, "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.6, 17, 1.4], "line-dasharray": [2, 2] } },
    { id: "bt-aerien", type: "line", source: "bt", minzoom: 13, filter: pose("aérien"), layout: rond,
      paint: { "line-color": C.bleu, "line-opacity": 0.8, "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.7, 17, 1.6] } },
    { id: "hta-liseré", type: "line", source: "hta", minzoom: 11, layout: rond,
      paint: { "line-color": C.papier, "line-opacity": 0.65, "line-width": ["interpolate", ["linear"], ["zoom"], 11, 3, 16, 5.5] } },
    { id: "hta-souterrain", type: "line", source: "hta", filter: pose("souterrain"), layout: { "line-join": "round" },
      paint: { "line-color": C.bleu, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.6, 12, 1.2, 16, 2.2], "line-dasharray": [3, 2] } },
    { id: "hta-aerien", type: "line", source: "hta", filter: pose("aérien"), layout: rond,
      paint: { "line-color": C.bleu, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.8, 12, 1.6, 16, 2.8] } },
    { id: "htb-liseré", type: "line", source: "htb_lignes", layout: rond,
      paint: { "line-color": C.papier, "line-opacity": 0.75, "line-width": ["interpolate", ["linear"], ["zoom"], 9, ["case", [">=", ["get", "tension_kv"], 400], 4.5, 3], 16, ["case", [">=", ["get", "tension_kv"], 400], 9, 6]] } },
    { id: "htb-lignes", type: "line", source: "htb_lignes", layout: rond,
      paint: { "line-color": C.carmin, "line-width": ["interpolate", ["linear"], ["zoom"], 9, ["case", [">=", ["get", "tension_kv"], 400], 2.2, 1.1], 16, ["case", [">=", ["get", "tension_kv"], 400], 4.5, 2.4]] } },
    { id: "cercles-liseré", type: "line", source: "cercles", paint: { "line-color": C.papier, "line-width": 3.5, "line-opacity": 0.45 } },
    { id: "cercles-trait", type: "line", source: "cercles", paint: { "line-color": C.encre, "line-width": 1.3, "line-dasharray": [5, 4] } },
    { id: "poteaux-point", type: "circle", source: "poteaux", minzoom: 14.5,
      paint: { "circle-radius": 2.2, "circle-color": C.bleu, "circle-stroke-color": C.papier, "circle-stroke-width": 0.8 } },
    { id: "htb-pylones-point", type: "symbol", source: "htb_pylones", minzoom: 12,
      layout: { "icon-image": "pylone", "icon-allow-overlap": true, "icon-ignore-placement": true } },
    { id: "postes-hta-bt-point", type: "symbol", source: "postes_hta_bt", minzoom: 12.5,
      layout: { "icon-image": "poste-hta-bt", "icon-allow-overlap": true, "icon-ignore-placement": true } },
    { id: "production-cercle", type: "circle", source: "production",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["ln", ["max", ["get", "puissance_kw"], 1]], 2, 3, 15, 21],
        "circle-color": C.papier, "circle-opacity": 0.55, "circle-stroke-color": C.encre, "circle-stroke-width": 1.4,
      } },
    { id: "icpe-ecart", type: "circle", source: "icpe", minzoom: 10, filter: ["==", ["get", "controle_position"], "écart"],
      paint: { "circle-radius": 9, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": C.carmin, "circle-stroke-width": 1.5 } },
    { id: "icpe-point", type: "symbol", source: "icpe",
      layout: {
        "icon-image": ["match", ["get", "regime"], "A", "icpe-a", "E", "icpe-e", "icpe-autre"],
        "symbol-sort-key": ["match", ["get", "regime"], "A", 3, "E", 2, 1],
        "icon-allow-overlap": true, "icon-ignore-placement": true,
      } },
    { id: "cnpe-point", type: "symbol", source: "cnpe", layout: { "icon-image": "site", "icon-allow-overlap": true, "icon-ignore-placement": true } },
    { id: "selection-lavis", type: "fill", source: "selection", filter: poly, paint: { "fill-color": C.encre, "fill-opacity": 0.1 } },
    { id: "selection-halo", type: "line", source: "selection", layout: rond, paint: { "line-color": C.encre, "line-opacity": 0.22, "line-width": 10 } },
    { id: "selection-trait", type: "line", source: "selection", layout: rond, paint: { "line-color": C.encre, "line-width": 2.2 } },
    { id: "selection-point", type: "circle", source: "selection", filter: pts,
      paint: { "circle-radius": 13, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": C.encre, "circle-stroke-width": 2.2 } },
    { id: "mesure-trait", type: "line", source: "mesure", layout: rond, paint: { "line-color": C.encre, "line-width": 2, "line-dasharray": [2, 1.5] } },
    { id: "mesure-points", type: "circle", source: "mesure", filter: pts,
      paint: { "circle-radius": 4.5, "circle-color": C.papier, "circle-stroke-color": C.encre, "circle-stroke-width": 2 } },
  ];
}

/* Symboles ponctuels dessinés en canevas (pas de police de glyphes requise) */
function ajouterSymboles(map) {
  const r = 2;
  const icone = (nom, l, h, dessin) => {
    const c = document.createElement("canvas");
    c.width = l * r; c.height = h * r;
    const x = c.getContext("2d");
    x.scale(r, r);
    dessin(x);
    map.addImage(nom, x.getImageData(0, 0, c.width, c.height), { pixelRatio: r });
  };
  icone("site", 24, 24, (x) => {
    x.fillStyle = C.papier; x.strokeStyle = C.encre; x.lineWidth = 1.8;
    x.beginPath(); x.arc(12, 12, 9.5, 0, 2 * Math.PI); x.fill(); x.stroke();
    x.fillStyle = C.carmin; x.beginPath(); x.arc(12, 12, 5, 0, 2 * Math.PI); x.fill();
  });
  icone("poste-hta-bt", 13, 12, (x) => {
    x.fillStyle = C.papier; x.strokeStyle = C.bleu; x.lineWidth = 1.6; x.lineJoin = "round";
    x.beginPath(); x.moveTo(6.5, 1.5); x.lineTo(11.5, 10.5); x.lineTo(1.5, 10.5); x.closePath(); x.fill(); x.stroke();
  });
  icone("pylone", 8, 8, (x) => {
    x.fillStyle = C.papier; x.strokeStyle = C.carmin; x.lineWidth = 1.5;
    x.fillRect(1.5, 1.5, 5, 5); x.strokeRect(1.5, 1.5, 5, 5);
  });
  const losange = (nom, plein, t) => icone(nom, t, t, (x) => {
    const m = t / 2, d = t / 2 - 1.2;
    x.beginPath(); x.moveTo(m, m - d); x.lineTo(m + d, m); x.lineTo(m, m + d); x.lineTo(m - d, m); x.closePath();
    x.lineWidth = 1.5; x.strokeStyle = C.encre; x.fillStyle = plein ? C.encre : C.papier;
    x.fill(); x.stroke();
  });
  losange("icpe-a", true, 12);
  losange("icpe-e", false, 12);
  icone("icpe-autre", 7, 7, (x) => {
    x.fillStyle = C.encre; x.strokeStyle = C.papier; x.lineWidth = 1;
    x.beginPath(); x.arc(3.5, 3.5, 2.4, 0, 2 * Math.PI); x.fill(); x.stroke();
  });
  const hachure = (nom, sens) => icone(nom, 8, 8, (x) => {
    x.strokeStyle = "rgba(79,127,176,.55)"; x.lineWidth = 1;
    x.beginPath();
    if (sens > 0) { x.moveTo(0, 8); x.lineTo(8, 0); x.moveTo(-2, 2); x.lineTo(2, -2); x.moveTo(6, 10); x.lineTo(10, 6); }
    else { x.moveTo(0, 0); x.lineTo(8, 8); x.moveTo(-2, 6); x.lineTo(2, 10); x.moveTo(6, -2); x.lineTo(10, 2); }
    x.stroke();
  });
  hachure("hachure-zsc", 1);
  hachure("hachure-zps", -1);
}

/* ---------------------------------------------------------------- État */
const etat = {
  donnees: {}, index: {}, emprises: {}, meta: null, site: null,
  planche: null, fond: "plan", mesure: { active: false, points: [], curseur: null },
  repere: null, selection: null,
};

function emprise(geom) {
  let w = 180, s = 90, e = -180, n = -90;
  const visiter = (c) => {
    if (typeof c[0] === "number") {
      if (c[0] < w) w = c[0]; if (c[0] > e) e = c[0];
      if (c[1] < s) s = c[1]; if (c[1] > n) n = c[1];
    } else c.forEach(visiter);
  };
  visiter(geom.coordinates);
  return [w, s, e, n];
}

/* La BD ORTHO peint le large d'aplats pâles en escalier. Sur ce fond seulement, la mer reçoit
   un lavis (polygone exporté : emprise des communes moins leur union) et tout ce qui sort de
   l'emprise d'étude redevient du papier, bordé d'un filet d'encre comme une planche. */
const MASQUES_ORTHO = ["mer-masque", "hors-emprise", "emprise-filet"];
function ajouterMasquesOrtho(mer, [o, s, e, n]) {
  const [[bo, bs], [be, bn]] = map.getMaxBounds().toArray();
  const cadre = [[o, s], [o, n], [e, n], [e, s], [o, s]];
  map.addSource("mer", { type: "geojson", data: mer });
  map.addSource("emprise", { type: "geojson", data: { type: "Feature", properties: {}, geometry: {
    type: "Polygon", coordinates: [[[bo, bs], [be, bs], [be, bn], [bo, bn], [bo, bs]], cadre] } } });
  const cache = { visibility: etat.fond === "ortho" ? "visible" : "none" };
  map.addLayer({ id: "mer-masque", type: "fill", source: "mer", layout: cache,
    paint: { "fill-color": "#5f8584" } }); // opaque : à 0,9 les marches pâles transparaissent
  map.addLayer({ id: "hors-emprise", type: "fill", source: "emprise", layout: cache,
    paint: { "fill-color": C.papier } });
  map.addLayer({ id: "emprise-filet", type: "line", source: "emprise", layout: cache,
    paint: { "line-color": C.encre, "line-width": 1 } });
}

async function chargerJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} : ${r.status}`);
  return r.json();
}

/* ---------------------------------------------------------------- Carte */
const centreInitial = [1.210236, 49.976144];
const vueInitialeDansUrl = /[#&]vue=/.test(location.hash); // lu avant que la carte n'écrive l'URL
const map = new maplibregl.Map({
  container: "map",
  style: {
    version: 8,
    sources: {
      plan: { type: "raster", tiles: [wmts("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", "normal", "image/png")], tileSize: 256, maxzoom: 19, attribution: ATTRIB_IGN },
      ortho: { type: "raster", tiles: [wmts("ORTHOIMAGERY.ORTHOPHOTOS", "normal", "image/jpeg")], tileSize: 256, maxzoom: 19, attribution: ATTRIB_IGN },
      cadastre: { type: "raster", tiles: [wmts("CADASTRALPARCELS.PARCELLAIRE_EXPRESS", "PCI vecteur", "image/png")], tileSize: 256, maxzoom: 19, attribution: ATTRIB_IGN },
    },
    layers: [
      { id: "papier", type: "background", paint: { "background-color": C.papier } },
      { id: "fond-plan", type: "raster", source: "plan", paint: { "raster-saturation": -0.5, "raster-contrast": -0.1, "raster-opacity": 0.7 } },
      { id: "fond-ortho", type: "raster", source: "ortho", layout: { visibility: "none" }, paint: { "raster-saturation": -0.3, "raster-opacity": 0.92 } },
      { id: "fond-cadastre", type: "raster", source: "cadastre", minzoom: 13, layout: { visibility: "none" }, paint: { "raster-opacity": 0.85 } },
    ],
  },
  center: centreInitial,
  zoom: 11.6,
  minZoom: 8,
  maxZoom: 18.5,
  maxBounds: [[0.2, 49.4], [2.2, 50.55]],
  hash: "vue",
  attributionControl: false,
  dragRotate: false,
  pitchWithRotate: false,
  touchPitch: false,
  locale: { "AttributionControl.ToggleAttribution": "Afficher les attributions", "ScaleControl.Meters": "m", "ScaleControl.Kilometers": "km" },
});
map.touchZoomRotate.disableRotation();
map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }), "bottom-left");
map.addControl(new maplibregl.AttributionControl({
  compact: true,
  customAttribution: "Données : EDF, Enedis, Agence ORE, IGN, PatriNat, Géorisques (Licence Ouverte Etalab 2.0)",
}), "bottom-right");

map.on("load", async () => {
  ajouterSymboles(map);
  const ids = Object.keys(COUCHES);
  try {
    const [meta, site, mer, ...collections] = await Promise.all([
      chargerJson("data/meta.json"), chargerJson("data/site.json"), chargerJson("data/mer.geojson"),
      ...ids.map((id) => chargerJson(`data/${id}.geojson`)),
    ]);
    etat.meta = meta; etat.site = site;
    ajouterMasquesOrtho(mer, site.emprise);
    ids.forEach((id, i) => {
      const fc = collections[i];
      etat.donnees[id] = fc;
      etat.index[id] = new Map(fc.features.map((f) => [f.id, f]));
      etat.emprises[id] = fc.features.map((f) => emprise(f.geometry));
      map.addSource(id, { type: "geojson", data: fc });
    });
  } catch (err) {
    const el = $("#chargement");
    el.textContent = "Les couches n'ont pas pu être chargées. Recharger la page ; si le problème persiste, la carte doit être servie par un serveur web (pas en fichier local).";
    el.classList.add("erreur");
    console.error(err);
    return;
  }
  map.addSource("selection", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  map.addSource("mesure", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  calquesDonnees().forEach((c) => map.addLayer(c));

  remplirCartouche();
  construirePanneauCouches();
  construireSources();
  poserEtiquettes();
  construireAssemblage();
  majComptes();
  majEchelles();
  $("#chargement").hidden = true;
  if (ECRAN_ETROIT.matches) document.querySelector(".maplibregl-ctrl-attrib")?.classList.remove("maplibregl-compact-show");

  if (!vueInitialeDansUrl) ouvrirPlanche(5, false);
});

/* ---------------------------------------------------------------- Cartouche du site */
function remplirCartouche() {
  const s = etat.site;
  const tr = s.tranches || [];
  const annees = tr.map((t) => t.mise_en_service.slice(0, 4));
  const mw = tr.length && tr.every((t) => t.puissance_mw === tr[0].puissance_mw) ? `${tr.length} × ${nf0.format(tr[0].puissance_mw)} MW` : "";
  const icpe5 = s.anneaux["5"].icpe?.objets;
  const douteuses5 = s.anneaux["5"].icpe?.positions_douteuses || 0;
  const htb400 = etat.donnees.htb_lignes.features.some((f) => f.properties.tension_kv === 400);
  const cases = [
    [mw, `${tr.length} tranches en service depuis ${annees.join(" et ")}`],
    [htb400 ? "400 kV" : "", "tension des lignes d'évacuation"],
    [`${icpe5}${NBSP}ICPE`, douteuses5 ? `à moins de 5${NBSP}km, hors ${douteuses5} position${douteuses5 > 1 ? "s" : ""} douteuse${douteuses5 > 1 ? "s" : ""}` : `installations classées à moins de 5${NBSP}km`],
    ["20 km", "rayon du plan particulier d'intervention"],
  ];
  $("#chiffres").innerHTML = cases.filter(([v]) => v)
    .map(([v, l]) => `<div><dt>${esc(l)}</dt><dd>${esc(v)}</dd></div>`).join("");
  $("#site-nom").textContent = s.nom;
  const d = dateTexte(etat.meta.genere_le);
  $("#pied").innerHTML = `Données ouvertes extraites le ${esc(d)} · Licence Ouverte Etalab 2.0 · <button type="button" data-apropos>Sources et méthode</button>`;
  $("#date-extraction").textContent = d;
}

/* ---------------------------------------------------------------- Panneau des couches */
const CASE = '<span class="case"><svg viewBox="0 0 10 10" aria-hidden="true"><path d="M2 5.2 4.2 7.4 8 2.8"/></svg></span>';

function sourcesDuGroupe(g) {
  return [...new Set(g.couches.map((id) => etat.meta.couches[id]?.source).filter((s) => s && !s.startsWith("Calcul")))]
    .map((s) => s.replace(/,? ?BD TOPO V3/, "").replace(/ \(.*\)/, "").replace(", via Koumoul", ""))
    .filter((s, i, a) => a.indexOf(s) === i).join(", ");
}

function construirePanneauCouches() {
  const html = GROUPES.map((g) => {
    const lignes = g.couches.map((id) => {
      const c = COUCHES[id], m = etat.meta.couches[id];
      const total = m ? nf0.format(m.objets) : "";
      const qualite = m?.ecarts_position ? `<small class="note-qualite">${m.ecarts_position} positions hors de la commune déclarée, cerclées de carmin</small>` : "";
      return `<button type="button" class="couche" role="switch" aria-checked="true" data-couche="${id}"
        title="${esc(m ? `${m.titre} · ${m.source} · ${m.objets} objets${m.decoupe_km ? ` (découpé à ${m.decoupe_km} km du site)` : ""}` : c.libelle)}">
        ${CASE}<span class="pastille">${c.pastille}</span>
        <span class="nom">${esc(c.libelle)}${qualite}<small data-echelle hidden></small></span>
        <span class="compte" data-compte><b>0</b><span> / ${total}</span></span>
      </button>`;
    }).join("");
    const src = sourcesDuGroupe(g);
    return `<section class="groupe-couches"><h3>${esc(g.titre)}${src ? `<span>${esc(src)}</span>` : ""}</h3>${lignes}</section>`;
  }).join("");
  $("#couches").innerHTML = html;
  $("#couches").addEventListener("click", (e) => {
    const b = e.target.closest("[data-couche]");
    if (!b) return;
    const visible = b.getAttribute("aria-checked") !== "true";
    b.setAttribute("aria-checked", String(visible));
    basculerCouche(b.dataset.couche, visible);
  });
}

function basculerCouche(id, visible) {
  const c = COUCHES[id];
  const v = visible ? "visible" : "none";
  const lies = {
    znieff1: ["znieff1-trait"], znieff2: ["znieff2-trait"], natura2000: ["natura2000-trait"],
    conservatoire: ["conservatoire-trait"], htb_postes: ["htb-postes-trait"], htb_lignes: ["htb-liseré"], icpe: ["icpe-ecart"],
    hta: ["hta-liseré"], communes: ["communes-prise"], cercles: ["cercles-liseré"],
  };
  [...c.calques, ...(lies[id] || [])].forEach((l) => map.getLayer(l) && map.setLayoutProperty(l, "visibility", v));
  if (id === "cercles") document.querySelectorAll(".etiquette-anneau").forEach((el) => (el.style.visibility = visible ? "" : "hidden"));
  if (id === "cnpe") document.querySelectorAll(".etiquette-site").forEach((el) => (el.style.visibility = visible ? "" : "hidden"));
}

function coucheVisible(id) {
  const b = document.querySelector(`[data-couche="${id}"]`);
  return !b || b.getAttribute("aria-checked") === "true";
}

/* Comptes « dans la vue » : état honnête de chaque couche */
function majComptes() {
  if (!etat.meta) return;
  const b = map.getBounds();
  const W = b.getWest(), S = b.getSouth(), E = b.getEast(), N = b.getNorth();
  const z = map.getZoom();
  for (const id of Object.keys(COUCHES)) {
    const ligne = document.querySelector(`[data-couche="${id}"]`);
    if (!ligne) continue;
    let n = 0;
    for (const bb of etat.emprises[id]) if (bb[0] <= E && bb[2] >= W && bb[1] <= N && bb[3] >= S) n++;
    const mz = COUCHES[id].minzoom;
    const note = ligne.querySelector("[data-echelle]");
    const hors = mz && z < mz;
    // Hors échelle, rien n'est dessiné : le compte « dans la vue » serait trompeur.
    ligne.querySelector("[data-compte] b").textContent = hors ? "—" : nf0.format(n);
    ligne.classList.toggle("hors-echelle", !!hors);
    note.hidden = !hors;
    if (hors) note.textContent = `visible à partir du 1:${nf0.format(echelleDenominateur(mz, map.getCenter().lat))}`;
  }
}

function majEchelles() {
  const c = map.getCenter();
  $("#releve-echelle").textContent = `1 : ${nf0.format(echelleDenominateur(map.getZoom(), c.lat))}`;
  if (!etat.pointeurSurCarte) afficherXY(c.lng, c.lat);
}
function afficherXY(lon, lat) {
  const [x, y] = L93(lon, lat);
  $("#releve-xy").textContent = `X ${nf0.format(x)} · Y ${nf0.format(y)}`;
}

map.on("move", () => { majEchelles(); majCadreAssemblage(); });
map.on("moveend", majComptes);
map.on("mousemove", (e) => { etat.pointeurSurCarte = true; afficherXY(e.lngLat.lng, e.lngLat.lat); });
map.getCanvas().addEventListener("mouseleave", () => { etat.pointeurSurCarte = false; majEchelles(); });

/* ---------------------------------------------------------------- Étiquettes en italique */
function poserEtiquettes() {
  const [lon0, lat0] = etat.site.centre;
  const el = document.createElement("div");
  el.className = "etiquette etiquette-site";
  el.textContent = etat.site.nom;
  new maplibregl.Marker({ element: el, anchor: "left", offset: [15, -12] }).setLngLat([lon0, lat0]).addTo(map);
  for (const r of ANNEAUX) {
    const e = document.createElement("div");
    e.className = "etiquette etiquette-anneau";
    e.textContent = `${r} km`;
    new maplibregl.Marker({ element: e, anchor: "center" }).setLngLat([lon0, lat0 - r / 111.2]).addTo(map);
  }
}

/* ---------------------------------------------------------------- Sélection et fiche d'objet */
function calquesInterrogeables() {
  return ORDRE_CLIC.flatMap((id) => (COUCHES[id].interrogeable || COUCHES[id].calques))
    .filter((l) => map.getLayer(l) && map.getLayoutProperty(l, "visibility") !== "none");
}
const coucheDuCalque = (calque) => Object.keys(COUCHES).find((id) => (COUCHES[id].interrogeable || COUCHES[id].calques).includes(calque));

function objetsSous(point) {
  const t = 6;
  const trouves = map.queryRenderedFeatures([[point.x - t, point.y - t], [point.x + t, point.y + t]], { layers: calquesInterrogeables() });
  const vus = new Set(), liste = [];
  for (const f of trouves) {
    const id = coucheDuCalque(f.layer.id);
    const cle = `${id}:${f.id}`;
    if (!id || vus.has(cle)) continue;
    vus.add(cle);
    liste.push({ couche: id, id: f.id });
  }
  liste.sort((a, b) => ORDRE_CLIC.indexOf(a.couche) - ORDRE_CLIC.indexOf(b.couche));
  return liste;
}

map.on("click", (e) => {
  if (etat.mesure.active) { ajouterPointMesure(e.lngLat); return; }
  const liste = objetsSous(e.point);
  if (!liste.length) { fermerFiche(); return; }
  ouvrirFiche(liste[0].couche, liste[0].id, liste.slice(1, 7));
});
map.on("mousemove", (e) => {
  if (etat.mesure.active || !etat.meta) return;
  map.getCanvas().style.cursor = objetsSous(e.point).length ? "pointer" : "";
});

function surligner(f) {
  map.getSource("selection")?.setData({ type: "FeatureCollection", features: f ? [f] : [] });
}

function ouvrirFiche(couche, id, autres = []) {
  const f = etat.index[couche]?.get(id);
  if (!f) return;
  const c = COUCHES[couche], p = f.properties, m = etat.meta.couches[couche];
  etat.selection = { couche, id };
  surligner(f);
  document.querySelectorAll(".assemblage-carte .commune").forEach((el) => el.classList.toggle("choisie", couche === "communes" && +el.dataset.id === id));

  let corps = "";
  const douteux = p.controle_position === "écart";
  if (!c.pasDeDistance && p.dist_cnpe_m != null) {
    const d = p.dist_cnpe_m === 0 ? "0 m" : distanceTexte(p.dist_cnpe_m);
    const lib = douteux ? `du CNPE selon la position du registre, non${NBSP}fiable`
      : p.dist_cnpe_m === 0 ? (couche === "communes" ? "le CNPE est sur cette commune" : "au droit du CNPE")
        : c.distanceLibelle || "du CNPE de Penly, au plus près";
    corps += `<div class="distance${douteux ? " douteuse" : ""}"><b>${esc(d)}</b><span>${esc(lib)}</span></div>`;
  }
  if (douteux) {
    corps += `<dl class="attributs"><dt>Contrôle de position</dt><dd class="ecart">écart : déclarée à ${esc(p.commune)}, le point tombe à ${esc(p.commune_position)}</dd></dl>`;
  }
  if (couche === "cnpe") corps += ficheSite();
  if (couche === "production") corps += ficheProduction(p);
  if (couche === "cercles") corps += ficheCercle(p);
  if (c.champs) {
    corps += `<dl class="attributs">${c.champs.filter(([k]) => !(douteux && k === "controle_position")).map(([k, l, fmt]) => {
      const v = fmt ? fmt(p[k], p) : p[k] ?? "non renseigné";
      return `<dt>${esc(l)}</dt><dd>${esc(v)}</dd>`;
    }).join("")}</dl>`;
  }
  if (c.lien) {
    const [url, lib] = c.lien(p);
    if (url && /^https:\/\//.test(url)) corps += `<a class="lien-externe" href="${esc(url)}" target="_blank" rel="noopener">${esc(lib)}<svg class="ic" aria-hidden="true"><use href="#i-externe"/></svg></a>`;
  }
  if (autres.length) {
    corps += `<h3>Aussi à cet endroit</h3><ul class="aussi">${autres.map((o) => {
      const fo = etat.index[o.couche].get(o.id);
      return `<li><button type="button" data-objet="${o.couche}:${o.id}">${COUCHES[o.couche].pastille}${esc(COUCHES[o.couche].titre(fo.properties))}</button></li>`;
    }).join("")}</ul>`;
  }
  if (m) {
    corps += `<p class="source-fiche">Source : ${esc(m.source)}${m.date ? `, extrait le ${esc(dateTexte(m.date))}` : ""}. ${esc(m.licence)}.${m.decoupe_km ? ` Géométrie découpée à ${m.decoupe_km} km du site pour l'affichage.` : ""}</p>`;
  }

  const vue = $("#vue-fiche");
  vue.innerHTML = `<div class="entete-vue"><button class="retour" type="button" data-retour><svg class="ic" aria-hidden="true"><use href="#i-retour"/></svg>Couches</button></div>
    <article class="fiche"><h2 tabindex="-1">${esc(c.titre(p))}</h2>
    <p class="fiche-couche">${c.pastille}<span>${esc(m ? m.titre : c.libelle)}</span></p>${corps}</article>`;
  montrerVue("fiche");
  vue.scrollTop = 0;
  vue.querySelector("h2").focus({ preventScroll: true });
}

function ficheSite() {
  const s = etat.site;
  const lignes = s.tranches.map((t) => `<dt>${esc(t.tranche.replace("PENLY", "Penly"))}</dt><dd>${nf0.format(t.puissance_mw)} MW, en service industriel depuis le ${esc(dateTexte(t.mise_en_service))}</dd>`).join("");
  return `<dl class="attributs"><dt>Commune</dt><dd>${esc(s.commune)}, ${esc(s.departement)}</dd>${lignes}
    <dt>Position Lambert-93</dt><dd>X ${nf0.format(s.centre_l93[0])} · Y ${nf0.format(s.centre_l93[1])}</dd></dl>
    <p class="source-fiche">Deux réacteurs supplémentaires sont en projet sur le site (débat public CNDP 2022-2023) ; leurs emprises ne sont pas publiques.</p>`;
}

function ficheProduction(p) {
  const items = (p.liste || []).map((i) => `<li><b>${esc(i.nom || "Installation sans nom publié")}</b><span class="num">${esc(puissanceTexte(i.puissance_kw))}</span>
    <span>${esc([i.filiere, i.technologie].filter(Boolean).join(", "))}${i.mise_en_service ? ` · mise en service ${esc(dateTexte(i.mise_en_service))}` : ""}</span></li>`).join("");
  return `<dl class="attributs"><dt>Installations</dt><dd>${nf0.format(p.installations)}</dd>
    <dt>Puissance installée</dt><dd>${esc(puissanceTexte(p.puissance_kw))}</dd>
    <dt>Filière principale</dt><dd>${esc(p.filiere_principale)}</dd></dl>
    <p class="source-fiche">Le registre agrégé localise chaque installation au centre de sa commune : le cercle situe la commune, pas les installations.</p>
    <h3>Installations</h3><ul class="liste-installations">${items}</ul>`;
}

function bilanAnneau(r) {
  const b = etat.site.anneaux[String(r)];
  const parts = [];
  const add = (cle, f) => { if (b[cle]) parts.push(f(b[cle])); };
  const pl = (n) => (n > 1 ? "s" : "");
  add("htb_lignes", (v) => `${v.objets} tronçons HTB (${nf1.format(v.km)}${NBSP}km)`);
  add("hta", (v) => `${nf1.format(v.km)}${NBSP}km de réseau HTA`);
  add("bt", (v) => `${nf1.format(v.km)}${NBSP}km de réseau BT`);
  add("icpe", (v) => `${v.objets}${NBSP}ICPE${v.positions_douteuses ? ` (+${NBSP}${v.positions_douteuses} position${pl(v.positions_douteuses)} douteuse${pl(v.positions_douteuses)})` : ""}`);
  add("znieff1", (v) => `${v.objets} ZNIEFF de type 1`);
  add("natura2000", (v) => `${v.objets} site${v.objets > 1 ? "s" : ""} Natura 2000`);
  add("communes", (v) => `${v.objets} commune${v.objets > 1 ? "s" : ""}`);
  return parts;
}

function ficheCercle(p) {
  const parts = bilanAnneau(p.rayon_km);
  return `<h3>Dans ce cercle</h3><ul class="aussi">${parts.map((t) => `<li><span>${esc(t)}</span></li>`).join("")}</ul>`;
}

function fermerFiche() {
  etat.selection = null;
  surligner(null);
  document.querySelectorAll(".assemblage-carte .commune.choisie").forEach((el) => el.classList.remove("choisie"));
  montrerVue("couches");
}

function montrerVue(nom) {
  for (const v of ["couches", "fiche", "apropos"]) $(`#vue-${v}`).hidden = v !== nom;
  if (nom !== "couches" && ECRAN_ETROIT.matches) ouvrirTiroir(true);
}

document.addEventListener("click", (e) => {
  if (e.target.closest("[data-retour]")) { fermerFiche(); $("#couches .couche")?.focus(); }
  const o = e.target.closest("[data-objet]");
  if (o) { const [c, i] = o.dataset.objet.split(":"); ouvrirFiche(c, +i); }
  if (e.target.closest("[data-apropos]")) ouvrirApropos();
});

/* ---------------------------------------------------------------- Le projet et les sources */
function construireSources() {
  const lignes = Object.entries(etat.meta.couches).map(([, m]) => `<tr><td>${esc(m.titre)}${m.decoupe_km ? ` <small>(${m.decoupe_km} km)</small>` : ""}</td>
    <td>${m.url_source ? `<a href="${esc(m.url_source)}" target="_blank" rel="noopener">${esc(m.source)}</a>` : esc(m.source)}</td>
    <td class="num">${nf0.format(m.objets)}</td></tr>`).join("");
  $("#sources tbody").innerHTML = lignes;
  const h = location.hostname;
  if (h.endsWith(".github.io")) {
    const depot = location.pathname.split("/").filter(Boolean)[0];
    if (depot) {
      const a = $("#lien-depot a");
      a.href = `https://github.com/${h.split(".")[0]}/${depot}`;
      $("#lien-depot").hidden = false;
    }
  }
}
function ouvrirApropos() {
  surligner(null);
  montrerVue("apropos");
  $("#vue-apropos").scrollTop = 0;
  $("#apropos-titre").focus({ preventScroll: true });
}
$("#btn-apropos").addEventListener("click", () => {
  if (!$("#vue-apropos").hidden) fermerFiche(); else ouvrirApropos();
});

/* ---------------------------------------------------------------- Tableau d'assemblage et planches */
const ASS = { l: 238, h: 176, demiKm: 22.5 };
function projAss([lon, lat]) {
  const [lon0, lat0] = etat.site.centre;
  const s = ASS.l / (2 * ASS.demiKm);
  const kx = 111.32 * Math.cos((lat0 * Math.PI) / 180), ky = 111.2;
  return [ASS.l / 2 + (lon - lon0) * kx * s, ASS.h / 2 - (lat - lat0) * ky * s];
}

function construireAssemblage() {
  const s = ASS.l / (2 * ASS.demiKm);
  const chemin = (anneaux) => anneaux.map((a) => {
    let d = "", prec = null;
    for (const c of a) {
      const [x, y] = projAss(c);
      if (prec && Math.abs(x - prec[0]) < 0.8 && Math.abs(y - prec[1]) < 0.8) continue;
      d += `${d ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`;
      prec = [x, y];
    }
    return d + "Z";
  }).join("");
  const communes = etat.donnees.communes.features.map((f) => {
    const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
    return `<path class="commune" data-id="${f.id}" d="${polys.map(chemin).join("")}"><title>${esc(f.properties.nom)}</title></path>`;
  }).join("");
  const [cx, cy] = [ASS.l / 2, ASS.h / 2];
  const anneaux = ANNEAUX.map((r) => `<circle class="anneau" data-r="${r}" cx="${cx}" cy="${cy}" r="${(r * s).toFixed(1)}"/>
    <circle class="prise" data-planche="${r}" cx="${cx}" cy="${cy}" r="${(r * s).toFixed(1)}"><title>Planche ${r} km</title></circle>`).join("");
  $("#assemblage-carte").innerHTML = `<svg viewBox="0 0 ${ASS.l} ${ASS.h}" role="img" aria-label="Tableau d'assemblage : communes et cercles de 2, 5, 10 et 20 km autour du CNPE">
    <rect class="mer" width="${ASS.l}" height="${ASS.h}"/>${communes}${anneaux}
    <rect class="vue-courante" id="vue-courante" x="0" y="0" width="0" height="0"/>
    <circle class="site" cx="${cx}" cy="${cy}" r="3.2"/></svg>`;
  $("#assemblage-carte").addEventListener("click", (e) => {
    const c = e.target.closest(".commune");
    if (c) { allerCommune(+c.dataset.id); }
  });
  majCadreAssemblage();
}

function allerCommune(id) {
  const f = etat.index.communes.get(id);
  const [w, s, e, n] = emprise(f.geometry);
  marquerPlanche(null);
  map.fitBounds([[w, s], [e, n]], { padding: 40, duration: MOUVEMENT_REDUIT ? 0 : 900, easing: easeOutExpo });
  ouvrirFiche("communes", id);
}

function majCadreAssemblage() {
  const r = document.getElementById("vue-courante");
  if (!r || !etat.site) return;
  const b = map.getBounds();
  const [x1, y1] = projAss([b.getWest(), b.getNorth()]);
  const [x2, y2] = projAss([b.getEast(), b.getSouth()]);
  // Part du tableau couverte par la vue : au-delà de 90 % le cadre ne situe plus rien (l'anneau
  // actif suffit), au-delà de 40 % son lavis teinterait tout le tableau, on garde le seul filet.
  const part = (Math.max(0, Math.min(x2, ASS.l) - Math.max(x1, 0)) * Math.max(0, Math.min(y2, ASS.h) - Math.max(y1, 0))) / (ASS.l * ASS.h);
  r.setAttribute("visibility", part > 0.9 ? "hidden" : "visible");
  r.classList.toggle("large", part > 0.4);
  if (part > 0.9) return;
  const cl = (v, max) => Math.max(-2, Math.min(max + 2, v));
  r.setAttribute("x", cl(x1, ASS.l)); r.setAttribute("y", cl(y1, ASS.h));
  r.setAttribute("width", Math.max(2, cl(x2, ASS.l) - cl(x1, ASS.l)));
  r.setAttribute("height", Math.max(2, cl(y2, ASS.h) - cl(y1, ASS.h)));
}

function ouvrirPlanche(r, anime = true) {
  const [lon0, lat0] = etat.site.centre;
  const dLat = r / 111.2, dLon = r / (111.32 * Math.cos((lat0 * Math.PI) / 180));
  // La planche se cale dans la partie libre de la carte : le tableau d'assemblage reste en marge.
  const pad = ECRAN_ETROIT.matches ? { top: 64, bottom: 190, left: 16, right: 16 }
    : { top: 32, bottom: 64, left: 40, right: $("#assemblage").offsetWidth + 40 };
  map.fitBounds([[lon0 - dLon, lat0 - dLat], [lon0 + dLon, lat0 + dLat]],
    { padding: pad, duration: anime && !MOUVEMENT_REDUIT ? 1400 : 0, easing: easeOutExpo });
  marquerPlanche(r);
}

function marquerPlanche(r) {
  etat.planche = r;
  document.querySelectorAll(".planches [data-planche]").forEach((b) => b.setAttribute("aria-pressed", String(+b.dataset.planche === r)));
  document.querySelectorAll(".assemblage-carte .anneau").forEach((c) => c.classList.toggle("actif", +c.dataset.r === r));
  const leg = $("#assemblage-legende");
  if (r == null) { leg.textContent = "Vue libre. Choisir une planche ou cliquer une commune."; return; }
  leg.textContent = `Planche ${r} km : ${bilanAnneau(r).slice(0, 4).join(", ")}.`;
}

document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-planche]");
  if (b && etat.site) ouvrirPlanche(+b.dataset.planche);
});
map.on("movestart", (e) => { if (e.originalEvent && etat.planche != null) marquerPlanche(null); });

$("#zoom-plus").addEventListener("click", () => map.zoomIn({ duration: MOUVEMENT_REDUIT ? 0 : 300 }));
$("#zoom-moins").addEventListener("click", () => map.zoomOut({ duration: MOUVEMENT_REDUIT ? 0 : 300 }));
$("#recentrer").addEventListener("click", () => etat.site && ouvrirPlanche(etat.planche || 5));

/* ---------------------------------------------------------------- Mesure de distance */
function majMesure() {
  const pts = etat.mesure.points;
  const trace = etat.mesure.curseur && etat.mesure.active ? [...pts, etat.mesure.curseur] : pts;
  let total = 0;
  for (let i = 1; i < trace.length; i++) total += haversine(trace[i - 1], trace[i]);
  const feats = pts.map((p) => ({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: p } }));
  if (trace.length > 1) feats.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: trace } });
  map.getSource("mesure")?.setData({ type: "FeatureCollection", features: feats });
  $("#mesure-total").textContent = distanceTexte(total) || "0 m";
  const n = pts.length;
  $("#mesure-detail").textContent = !n ? "Cliquer sur la carte pour poser le premier point."
    : etat.mesure.active ? `${n} point${n > 1 ? "s" : ""} posé${n > 1 ? "s" : ""}. Double-clic ou Échap pour terminer.`
      : `Mesure terminée, ${n - 1} segment${n > 2 ? "s" : ""}. Distance au sol sur l'ellipsoïde.`;
}
function ajouterPointMesure(ll) { etat.mesure.points.push([ll.lng, ll.lat]); majMesure(); }
function demarrerMesure() {
  fermerMenuFond();
  etat.mesure = { active: true, points: [], curseur: null };
  $("#btn-mesure").setAttribute("aria-pressed", "true");
  $(".carte").classList.add("mesure-active");
  $("#mesure").hidden = false;
  map.doubleClickZoom.disable();
  map.getCanvas().style.cursor = "crosshair";
  majMesure();
}
function terminerMesure() {
  etat.mesure.active = false; etat.mesure.curseur = null;
  $("#btn-mesure").setAttribute("aria-pressed", "false");
  $(".carte").classList.remove("mesure-active");
  map.getCanvas().style.cursor = "";
  setTimeout(() => map.doubleClickZoom.enable(), 300);
  if (etat.mesure.points.length < 2) effacerMesure(); else majMesure();
}
function effacerMesure() {
  etat.mesure.points = []; etat.mesure.curseur = null;
  majMesure();
  if (!etat.mesure.active) $("#mesure").hidden = true;
}
$("#btn-mesure").addEventListener("click", () => (etat.mesure.active ? terminerMesure() : demarrerMesure()));
$("#mesure-effacer").addEventListener("click", effacerMesure);
$("#mesure-fin").addEventListener("click", () => { if (etat.mesure.active) terminerMesure(); else effacerMesure(); });
map.on("dblclick", (e) => { if (etat.mesure.active) { e.preventDefault(); terminerMesure(); } });
map.on("mousemove", (e) => { if (etat.mesure.active && etat.mesure.points.length) { etat.mesure.curseur = [e.lngLat.lng, e.lngLat.lat]; majMesure(); } });

/* ---------------------------------------------------------------- Fonds de plan */
function fermerMenuFond() { $("#menu-fond").hidden = true; $("#btn-fond").setAttribute("aria-expanded", "false"); }
$("#btn-fond").addEventListener("click", (e) => {
  e.stopPropagation();
  const ouvert = $("#menu-fond").hidden;
  $("#menu-fond").hidden = !ouvert;
  $("#btn-fond").setAttribute("aria-expanded", String(ouvert));
  if (ouvert) $(`#menu-fond [data-fond="${etat.fond}"]`).focus();
});
$("#menu-fond").addEventListener("click", (e) => {
  const b = e.target.closest("[data-fond]");
  if (!b) return;
  changerFond(b.dataset.fond);
  fermerMenuFond();
  $("#btn-fond").focus();
});
$("#menu-fond").addEventListener("keydown", (e) => {
  const items = [...document.querySelectorAll("#menu-fond [data-fond]")];
  const i = items.indexOf(document.activeElement);
  if (e.key === "ArrowDown") { e.preventDefault(); items[(i + 1) % items.length].focus(); }
  if (e.key === "ArrowUp") { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
});
document.addEventListener("click", (e) => { if (!e.target.closest(".menu-fond")) fermerMenuFond(); });

function changerFond(nom) {
  etat.fond = nom;
  for (const l of ["fond-plan", "fond-ortho", "fond-cadastre"]) {
    map.setLayoutProperty(l, "visibility", FONDS[nom].calques.includes(l) ? "visible" : "none");
  }
  map.setPaintProperty("fond-plan", "raster-opacity", nom === "cadastre" ? 0.6 : 0.7);
  for (const l of MASQUES_ORTHO) {
    if (map.getLayer(l)) map.setLayoutProperty(l, "visibility", nom === "ortho" ? "visible" : "none");
  }
  document.querySelectorAll("#menu-fond [data-fond]").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.fond === nom)));
  $("#fond-nom").textContent = FONDS[nom].nom;
}

/* ---------------------------------------------------------------- Recherche d'adresse */
const champ = $("#q"), liste = $("#resultats");
let resultats = [], actif = -1, minuterie = null, requete = 0;

function fermerResultats() { liste.hidden = true; champ.setAttribute("aria-expanded", "false"); actif = -1; champ.removeAttribute("aria-activedescendant"); }
function rendreResultats(etatTexte) {
  if (!resultats.length) {
    liste.innerHTML = `<li class="etat" role="option" aria-disabled="true">${esc(etatTexte || "Aucun résultat.")}</li>`;
  } else {
    let groupe = null;
    liste.innerHTML = resultats.map((r, i) => {
      const entete = r.groupe !== groupe ? `<li class="groupe" role="presentation">${esc((groupe = r.groupe))}</li>` : "";
      return `${entete}<li id="res-${i}" role="option" aria-selected="${i === actif}" data-i="${i}">
        <span>${esc(r.libelle)}</span><small>${esc(r.contexte || "")}</small><span class="dist">${esc(r.distance)}</span></li>`;
    }).join("") + (etatTexte ? `<li class="etat" role="option" aria-disabled="true">${esc(etatTexte)}</li>` : "");
  }
  liste.hidden = false;
  champ.setAttribute("aria-expanded", "true");
}

async function chercher(q) {
  const ma = ++requete;
  const n = sansAccents(q);
  const centre = etat.site?.centre || centreInitial;
  const locales = (etat.donnees.communes?.features || [])
    .filter((f) => sansAccents(f.properties.nom).includes(n)).slice(0, 3)
    .map((f) => ({ groupe: "Communes de l'aire d'étude", libelle: f.properties.nom, contexte: `Code INSEE ${f.properties.code_insee}`, distance: distanceTexte(f.properties.dist_cnpe_m), commune: f.id }));
  resultats = locales; actif = -1;
  rendreResultats(q.length >= 3 ? "Recherche des adresses…" : "");
  if (q.length < 3) return;
  try {
    const url = `https://data.geopf.fr/geocodage/search?q=${encodeURIComponent(q)}&autocomplete=1&limit=6&lat=${centre[1]}&lon=${centre[0]}`;
    const r = await fetch(url);
    if (!r.ok) throw new Error(r.status);
    const json = await r.json();
    if (ma !== requete) return;
    // Les adresses proches du site passent devant : c'est l'aire que la carte décrit.
    const adresses = (json.features || []).map((f, rang) => {
      const d = haversine(f.geometry.coordinates, centre);
      return {
        groupe: "Adresses (Géoplateforme)", libelle: f.properties.label, contexte: f.properties.context,
        distance: distanceTexte(d), coord: f.geometry.coordinates, type: f.properties.type, tri: (d < 40000 ? 0 : 1000) + rang,
      };
    }).sort((a, b) => a.tri - b.tri);
    resultats = [...locales, ...adresses];
    rendreResultats(resultats.length ? "" : "Aucune adresse ni commune trouvée.");
  } catch {
    if (ma !== requete) return;
    rendreResultats("Recherche d'adresse indisponible pour le moment ; les communes restent cherchables.");
  }
}

function choisirResultat(i) {
  const r = resultats[i];
  if (!r) return;
  fermerResultats();
  champ.value = r.libelle;
  champ.blur();
  if (r.commune != null) { allerCommune(r.commune); return; }
  marquerPlanche(null);
  const zoom = { housenumber: 17, street: 16, locality: 15, municipality: 13 }[r.type] || 15;
  map.flyTo({ center: r.coord, zoom, duration: MOUVEMENT_REDUIT ? 0 : 1400, easing: easeOutExpo });
  if (!etat.repere) {
    const el = document.createElement("div");
    el.className = "repere";
    el.innerHTML = `<svg viewBox="0 0 22 30" aria-hidden="true"><path d="M11 29s9-9.6 9-17a9 9 0 0 0-18 0c0 7.4 9 17 9 17z" fill="${C.encre}"/><circle cx="11" cy="11.5" r="3.6" fill="${C.papier}"/></svg>`;
    etat.repere = new maplibregl.Marker({ element: el, anchor: "bottom" });
  }
  etat.repere.setLngLat(r.coord).addTo(map);
}

champ.addEventListener("input", () => {
  clearTimeout(minuterie);
  const q = champ.value.trim();
  if (q.length < 2) { fermerResultats(); return; }
  minuterie = setTimeout(() => chercher(q), 220);
});
champ.addEventListener("keydown", (e) => {
  if (liste.hidden && e.key !== "Escape") return;
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    if (!resultats.length) return;
    actif = (actif + (e.key === "ArrowDown" ? 1 : -1) + resultats.length) % resultats.length;
    rendreResultats();
    champ.setAttribute("aria-activedescendant", `res-${actif}`);
  } else if (e.key === "Enter") {
    e.preventDefault();
    choisirResultat(actif >= 0 ? actif : 0);
  } else if (e.key === "Escape") {
    fermerResultats();
  }
});
$("#recherche").addEventListener("submit", (e) => e.preventDefault());
liste.addEventListener("mousedown", (e) => {
  const li = e.target.closest("[data-i]");
  if (li) { e.preventDefault(); choisirResultat(+li.dataset.i); }
});
champ.addEventListener("blur", () => setTimeout(fermerResultats, 120));

/* ---------------------------------------------------------------- Clavier et tiroir mobile */
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (!$("#menu-fond").hidden) { fermerMenuFond(); $("#btn-fond").focus(); return; }
  if (etat.mesure.active) { terminerMesure(); return; }
  if (document.activeElement === champ) return;
  if ($("#vue-couches").hidden) fermerFiche();
});

function ouvrirTiroir(ouvert) {
  $("#panneau").classList.toggle("ouvert", ouvert);
  $("#poignee").setAttribute("aria-expanded", String(ouvert));
  $("#poignee .vh").textContent = ouvert ? "Replier le panneau" : "Déplier le panneau";
}
$("#poignee").addEventListener("click", () => ouvrirTiroir(!$("#panneau").classList.contains("ouvert")));
