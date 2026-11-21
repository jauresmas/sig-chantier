-- Rôle et base des couches publiées du SIG chantier (lue par le GeoServer de la pile MapStore).
-- Lancé par 00_creer_base.py en tant que postgres ; le mot de passe du rôle vient de la variable
-- d'environnement SIG_CHANTIER_DB_PASSWORD (05_mapstore/.env). Idempotent.

\set ON_ERROR_STOP on
\getenv mdp SIG_CHANTIER_DB_PASSWORD
\if :{?mdp}
\else
    \echo 'SIG_CHANTIER_DB_PASSWORD absent : lancer python 05_mapstore/00_creer_base.py'
    \quit
\endif

SELECT format('CREATE ROLE sig_chantier LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'mdp')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sig_chantier') \gexec
-- garde le rôle aligné sur le .env si la base existait déjà
SELECT format('ALTER ROLE sig_chantier PASSWORD %L', :'mdp') \gexec

SELECT 'CREATE DATABASE sig_chantier OWNER sig_chantier ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sig_chantier') \gexec

\connect sig_chantier

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE SCHEMA IF NOT EXISTS brut AUTHORIZATION sig_chantier;
CREATE SCHEMA IF NOT EXISTS carto AUTHORIZATION sig_chantier;
ALTER ROLE sig_chantier IN DATABASE sig_chantier SET search_path TO carto, brut, public;
