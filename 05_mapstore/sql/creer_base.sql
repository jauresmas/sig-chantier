-- Rôle et base des couches publiées du SIG chantier Penly (lue par le GeoServer de la pile MapStore).
-- Lancé par 00_creer_base.py en tant que postgres ; le mot de passe du rôle vient de la variable
-- d'environnement PENLY_DB_PASSWORD (05_mapstore/.env). Idempotent.

\set ON_ERROR_STOP on
\getenv mdp PENLY_DB_PASSWORD
\if :{?mdp}
\else
    \echo 'PENLY_DB_PASSWORD absent : lancer python 05_mapstore/00_creer_base.py'
    \quit
\endif

SELECT format('CREATE ROLE penly LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'mdp')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'penly') \gexec
-- garde le rôle aligné sur le .env si la base existait déjà
SELECT format('ALTER ROLE penly PASSWORD %L', :'mdp') \gexec

SELECT 'CREATE DATABASE penly_carto OWNER penly ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'penly_carto') \gexec

\connect penly_carto

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE SCHEMA IF NOT EXISTS brut AUTHORIZATION penly;
CREATE SCHEMA IF NOT EXISTS carto AUTHORIZATION penly;
ALTER ROLE penly IN DATABASE penly_carto SET search_path TO carto, brut, public;
