"""Étape 0 : crée le rôle PostgreSQL « penly » et la base penly_carto (PostGIS, schémas brut et carto).

À lancer une fois. Le mot de passe du rôle est tiré au hasard et rangé dans 05_mapstore/.env (ignoré par
git), jamais affiché. psql se connecte en postgres : il lit pgpass.conf s'il existe, sinon il demande le
mot de passe de postgres.

    python 05_mapstore/00_creer_base.py
"""
import secrets

from commun import ENV_LOCAL, ICI, PG, lire_env, psql


def main():
    local = lire_env(ENV_LOCAL)
    if not local.get("PENLY_DB_PASSWORD"):
        modele = (ICI / ".env.example").read_text(encoding="utf-8")
        texte = ENV_LOCAL.read_text(encoding="utf-8") if ENV_LOCAL.exists() else modele
        mdp = secrets.token_urlsafe(24)
        if "PENLY_DB_PASSWORD=" in texte:
            texte = "\n".join(f"PENLY_DB_PASSWORD={mdp}" if l.strip().startswith("PENLY_DB_PASSWORD=") else l
                              for l in texte.splitlines()) + "\n"
        else:
            texte += f"\nPENLY_DB_PASSWORD={mdp}\n"
        ENV_LOCAL.write_text(texte, encoding="utf-8")
        local = lire_env(ENV_LOCAL)
        print(f"mot de passe du rôle penly créé dans {ENV_LOCAL.name}")
    psql((ICI / "sql" / "creer_base.sql").read_text(encoding="utf-8"), base="postgres", utilisateur="postgres",
         variables={"PENLY_DB_PASSWORD": local["PENLY_DB_PASSWORD"]})
    print(f"base {PG['dbname']} prête (rôle {PG['user']}, schémas brut et carto)")


if __name__ == "__main__":
    main()
