-- Couches publiées par GeoServer (schéma carto), construites depuis l'import du GeoPackage (schéma brut).
-- Colonnes en français mises en forme pour les fiches d'information de MapStore ; Lambert-93 (EPSG:2154),
-- GeoServer reprojette à la volée. Lancé par 01_charger_postgis.py ; relancer remplace tout.

SET search_path = carto, brut, public;

-- ---------------------------------------------------------------- Mise en forme française
-- Nombre à la française : espace insécable pour les milliers, virgule décimale
CREATE OR REPLACE FUNCTION carto.fr(n numeric, d int DEFAULT 0) RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT replace(replace(to_char(round(n, d), 'FM999,999,999,990' || CASE WHEN d > 0 THEN '.' || repeat('0', d) ELSE '' END),
                         ',', chr(160)), '.', ',')
$$;

-- Distance lisible, comme la carte web : au 10 m près sous 1 km, une décimale jusqu'à 10 km
CREATE OR REPLACE FUNCTION carto.distance_txt(m double precision) RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE WHEN m IS NULL THEN NULL
              WHEN m < 1000 THEN carto.fr(round(m::numeric / 10) * 10) || chr(160) || 'm'
              WHEN m < 10000 THEN carto.fr((m / 1000)::numeric, 1) || chr(160) || 'km'
              ELSE carto.fr((m / 1000)::numeric) || chr(160) || 'km' END
$$;

-- Nom de commune comparable : sans accents, casse, tirets ni espaces
CREATE OR REPLACE FUNCTION carto.cle_commune(t text) RETURNS text LANGUAGE sql STABLE AS $$
  SELECT regexp_replace(lower(public.unaccent(coalesce(t, ''))), '[^a-z0-9]', '', 'g')
$$;

-- ---------------------------------------------------------------- Site et zonages
DROP TABLE IF EXISTS cnpe;
CREATE TABLE cnpe AS
SELECT 1 AS fid, 'CNPE de Penly'::text AS nom, z.exploitant, 'Petit-Caux, Seine-Maritime'::text AS commune,
       n.tranches || ' tranches de ' || carto.fr(n.unitaire) || chr(160) || 'MW' AS tranches,
       carto.fr(n.totale) || chr(160) || 'MW' AS puissance,
       n.annees AS mise_en_service,
       'Deux réacteurs supplémentaires en projet (débat public CNDP 2022-2023) ; leurs emprises de chantier '
       'ne sont pas publiques.'::text AS projet,
       'EDF, opendata.edf.fr (centrales de production nucléaire)'::text AS source,
       z.geom::geometry(Point, 2154) AS geom
FROM zon_cnpe z
CROSS JOIN (SELECT count(*) AS tranches, min(puissance_installee)::numeric AS unitaire,
                   sum(puissance_installee)::numeric AS totale,
                   string_agg(left(date_de_mise_en_service_industrielle::text, 4), ' et '
                              ORDER BY date_de_mise_en_service_industrielle::text) AS annees
            FROM prod_centrales_nucleaires WHERE centrale ILIKE 'PENLY%') n;

DROP TABLE IF EXISTS cercles;
CREATE TABLE cercles AS
SELECT fid, rayon_km, libelle, rayon_km || chr(160) || 'km' AS etiquette,
       ST_Multi(geom)::geometry(MultiPolygon, 2154) AS geom,
       -- point d'étiquette au sud de chaque cercle, comme sur la carte web
       ST_SetSRID(ST_MakePoint(ST_X(ST_Centroid(geom)), ST_YMin(geom)), 2154)::geometry(Point, 2154) AS geom_etiquette
FROM zon_cercles;

-- ---------------------------------------------------------------- Transport HTB (BD TOPO, d'après RTE)
DROP TABLE IF EXISTS htb_lignes;
CREATE TABLE htb_lignes AS
SELECT l.fid, substring(l.voltage FROM '(\d+)')::int AS tension_kv, l.voltage AS tension,
       l.etat_de_l_objet AS etat, coalesce(nullif(l.sources, ''), 'BD TOPO') AS source,
       carto.distance_txt(ST_Length(l.geom)) AS longueur,
       carto.distance_txt(ST_Distance(l.geom, c.geom)) AS distance,
       l.geom::geometry(MultiLineString, 2154) AS geom
FROM res_htb_lignes l CROSS JOIN cnpe c;

DROP TABLE IF EXISTS htb_postes;
CREATE TABLE htb_postes AS
SELECT p.fid, coalesce(nullif(p.toponyme, ''), 'Poste sans nom') AS nom, p.etat_de_l_objet AS etat,
       carto.distance_txt(ST_Distance(p.geom, c.geom)) AS distance,
       p.geom::geometry(MultiPolygon, 2154) AS geom
FROM res_htb_postes p CROSS JOIN cnpe c;

DROP TABLE IF EXISTS htb_pylones;
CREATE TABLE htb_pylones AS
SELECT fid, nullif(numero, '') AS numero, etat_de_l_objet AS etat, geom::geometry(MultiPoint, 2154) AS geom
FROM res_htb_pylones;

-- ---------------------------------------------------------------- Distribution (Enedis)
DROP TABLE IF EXISTS hta;
CREATE TABLE hta AS
SELECT row_number() OVER () AS fid, pose, commune, carto.distance_txt(ST_Length(geom)) AS longueur,
       geom::geometry(MultiLineString, 2154) AS geom
FROM (SELECT 'aérienne'::text AS pose, nom_commune AS commune, geom FROM res_hta_aerien
      UNION ALL SELECT 'souterraine', nom_commune, geom FROM res_hta_souterrain) t;

DROP TABLE IF EXISTS bt;
CREATE TABLE bt AS
SELECT row_number() OVER () AS fid, pose, commune, carto.distance_txt(ST_Length(geom)) AS longueur,
       geom::geometry(MultiLineString, 2154) AS geom
FROM (SELECT 'aérienne'::text AS pose, nom_commune AS commune, geom FROM res_bt_aerien
      UNION ALL SELECT 'souterraine', nom_commune, geom FROM res_bt_souterrain) t;

DROP TABLE IF EXISTS postes_hta_bt;
CREATE TABLE postes_hta_bt AS
SELECT fid, nom_commune AS commune, geom::geometry(MultiPoint, 2154) AS geom FROM res_postes_hta_bt;

DROP TABLE IF EXISTS poteaux;
CREATE TABLE poteaux AS
SELECT fid, nom_commune AS commune, geom::geometry(MultiPoint, 2154) AS geom FROM res_poteaux_hta_bt;

-- ---------------------------------------------------------------- Production (registre ORE)
-- Le registre agrégé place chaque installation au centre de sa commune : un objet par point (commune),
-- avec le nombre d'installations, la puissance totale et la filière qui pèse le plus.
DROP TABLE IF EXISTS production;
CREATE TABLE production AS
WITH par_filiere AS (
    SELECT geom, filiere, sum(coalesce(puismaxinstallee, 0)) AS kw
    FROM prod_registre_installations GROUP BY geom, filiere),
principale AS (
    SELECT DISTINCT ON (geom) geom, filiere FROM par_filiere ORDER BY geom, kw DESC),
communes AS (
    SELECT p.geom, min(p.commune) AS commune, count(*) AS installations,
           sum(coalesce(p.puismaxinstallee, 0)) AS puissance_kw,
           string_agg(DISTINCT p.filiere, ', ') AS filieres
    FROM prod_registre_installations p GROUP BY p.geom)
SELECT row_number() OVER (ORDER BY c.puissance_kw DESC) AS fid, c.commune, c.installations,
       c.puissance_kw, CASE WHEN c.puissance_kw >= 1000 THEN carto.fr((c.puissance_kw / 1000)::numeric, 1) || chr(160) || 'MW'
                            ELSE carto.fr(c.puissance_kw::numeric, 1) || chr(160) || 'kW' END AS puissance,
       f.filiere AS filiere_principale, c.filieres,
       carto.distance_txt(ST_Distance(c.geom, k.geom)) AS distance,
       ST_Multi(c.geom)::geometry(MultiPoint, 2154) AS geom
FROM communes c JOIN principale f ON f.geom = c.geom CROSS JOIN cnpe k;

-- ---------------------------------------------------------------- Environnement (INPN)
DROP TABLE IF EXISTS znieff1, znieff2, natura2000_zsc, natura2000_zps, conservatoire;
CREATE TABLE znieff1 AS SELECT fid, nom_site AS nom, id_mnhn AS code, 'ZNIEFF de type I'::text AS type_zone,
    carto.fr(nullif(area_sig::text, '')::numeric, 1) || chr(160) || 'ha' AS surface, url_fiche AS fiche_inpn,
    geom::geometry(MultiPolygon, 2154) AS geom FROM env_znieff1;
CREATE TABLE znieff2 AS SELECT fid, nom_site AS nom, id_mnhn AS code, 'ZNIEFF de type II'::text AS type_zone,
    carto.fr(nullif(area_sig::text, '')::numeric, 1) || chr(160) || 'ha' AS surface, url_fiche AS fiche_inpn,
    geom::geometry(MultiPolygon, 2154) AS geom FROM env_znieff2;
CREATE TABLE natura2000_zsc AS SELECT fid, nom_site AS nom, id_mnhn AS code,
    'Natura 2000, zone spéciale de conservation (directive Habitats)'::text AS type_zone,
    carto.fr(nullif(area_sig::text, '')::numeric, 1) || chr(160) || 'ha' AS surface, url_fiche AS fiche_inpn,
    geom::geometry(MultiPolygon, 2154) AS geom FROM env_natura2000_zsc_sic;
CREATE TABLE natura2000_zps AS SELECT fid, nom_site AS nom, id_mnhn AS code,
    'Natura 2000, zone de protection spéciale (directive Oiseaux)'::text AS type_zone,
    carto.fr(nullif(area_sig::text, '')::numeric, 1) || chr(160) || 'ha' AS surface, url_fiche AS fiche_inpn,
    geom::geometry(MultiPolygon, 2154) AS geom FROM env_natura2000_zps;
CREATE TABLE conservatoire AS SELECT fid, nom_site AS nom, id_mnhn AS code,
    'Terrain du Conservatoire du littoral'::text AS type_zone,
    carto.fr(nullif(area_sig::text, '')::numeric, 1) || chr(160) || 'ha' AS surface, url_fiche AS fiche_inpn,
    geom::geometry(MultiPolygon, 2154) AS geom FROM env_conservatoire_littoral;

-- ---------------------------------------------------------------- Installations classées (Géorisques)
-- Contrôle qualité : la position du registre tombe-t-elle dans la commune déclarée ?
DROP TABLE IF EXISTS icpe;
CREATE TABLE icpe AS
SELECT i.fid, i.nom_ets AS nom, i.regime,
       CASE i.regime WHEN 'A' THEN 'Autorisation' WHEN 'E' THEN 'Enregistrement'
                     WHEN 'AUTRE' THEN 'Autre régime (déclaration surtout)'
                     WHEN 'NEANT' THEN 'Non classé ICPE (site inspecté)' ELSE i.regime END AS regime_libelle,
       i.lib_naf AS activite, i.commune AS commune_declaree, cp.nom_officiel AS commune_position,
       CASE WHEN cp.nom_officiel IS NULL THEN 'hors de l''emprise des communes chargées'
            WHEN carto.cle_commune(cp.nom_officiel) = carto.cle_commune(i.commune) THEN 'conforme'
            ELSE 'écart : déclarée à ' || i.commune || ', le point tombe à ' || cp.nom_officiel END AS controle_position,
       cp.nom_officiel IS NOT NULL AND carto.cle_commune(cp.nom_officiel) <> carto.cle_commune(i.commune)
           AS position_douteuse,
       carto.distance_txt(ST_Distance(i.geom, k.geom))
           || CASE WHEN cp.nom_officiel IS NOT NULL AND carto.cle_commune(cp.nom_officiel) <> carto.cle_commune(i.commune)
                   THEN ' selon la position du registre, non fiable' ELSE '' END AS distance,
       round(ST_Distance(i.geom, k.geom)) AS dist_cnpe_m,
       to_char(i.derniere_inspection, 'DD/MM/YYYY') AS derniere_inspection,
       CASE WHEN i.priorite_nationale THEN 'oui' ELSE 'non' END AS priorite_nationale,
       i.code_aiot, i.url_fiche AS fiche_georisques,
       i.geom::geometry(MultiPoint, 2154) AS geom
FROM env_icpe i
CROSS JOIN cnpe k
LEFT JOIN LATERAL (SELECT c.nom_officiel FROM ref_communes c WHERE ST_Intersects(i.geom, c.geom) LIMIT 1) cp ON true;

-- ---------------------------------------------------------------- Référentiel (IGN, cadastre Etalab)
DROP TABLE IF EXISTS communes, batiments, parcelles;
CREATE TABLE communes AS
SELECT fid, nom_officiel AS nom, code_insee, code_postal, carto.fr(population::numeric) || ' habitants' AS population,
       geom::geometry(MultiPolygon, 2154) AS geom FROM ref_communes;
CREATE TABLE batiments AS
SELECT fid, nature, nullif(usage_1, '') AS usage,
       CASE WHEN hauteur > 0 THEN carto.fr(hauteur::numeric, 1) || chr(160) || 'm' END AS hauteur,
       nombre_de_logements AS logements, geom::geometry(MultiPolygon, 2154) AS geom FROM ref_batiments;
CREATE TABLE parcelles AS
SELECT fid, id AS identifiant, section, numero, carto.fr(contenance::numeric) || chr(160) || 'm²' AS contenance,
       geom::geometry(MultiPolygon, 2154) AS geom FROM ref_parcelles_petit_caux;

-- ---------------------------------------------------------------- Clés, index, statistiques
DO $$
DECLARE t text;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'carto' LOOP
        EXECUTE format('ALTER TABLE carto.%I ADD PRIMARY KEY (fid)', t);
        EXECUTE format('CREATE INDEX ON carto.%I USING gist (geom)', t);
        EXECUTE format('ANALYZE carto.%I', t);
    END LOOP;
END $$;
