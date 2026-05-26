import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import os

DB_URL = "postgresql://cherylecheryle@localhost:5432/urban_data_explorer"
engine = create_engine(DB_URL)

# ── Test connexion ─────────────────────────────────────────────────
with engine.connect() as conn:
    result = conn.execute(text("SELECT PostGIS_version()"))
    print(f"✅ Connexion OK — PostGIS {result.fetchone()[0][:3]}")

# ── 1. Table Gold arrondissements (sans géométrie) ─────────────────
print("\nChargement gold_arrondissements...")
gold = pd.read_parquet("data/gold/gold_arrondissements.parquet")
gold.to_sql("gold_arrondissements", engine, if_exists="replace", index=False)
print(f"  ✅ {len(gold)} arrondissements chargés")

# ── 2. Table géo arrondissements (avec géométrie) ──────────────────
print("\nChargement geo_arrondissements...")
arr = gpd.read_file("data/silver/arrondissements_silver.geojson")
arr['arrondissement'] = arr['arrondissement'].astype(int)
arr.to_postgis("geo_arrondissements", engine, if_exists="replace", index=False)
print(f"  ✅ {len(arr)} polygones chargés")

# ── 3. DVF transactions ────────────────────────────────────────────
print("\nChargement dvf_transactions...")
dvf = pd.read_parquet("data/silver/dvf_paris_silver.parquet")
# Garde seulement les colonnes essentielles pour l'API
dvf_light = dvf[[
    'annee', 'mois', 'arrondissement',
    'type_local', 'surface_reelle_bati',
    'nombre_pieces_principales', 'valeur_fonciere', 'prix_m2'
]]
dvf_light.to_sql("dvf_transactions", engine, if_exists="replace", index=False)
print(f"  ✅ {len(dvf_light):,} transactions chargées")

# ── 4. Loyers ──────────────────────────────────────────────────────
print("\nChargement loyers_reference...")
loyers = pd.read_parquet("data/silver/loyers_paris_silver.parquet")
loyers.to_sql("loyers_reference", engine, if_exists="replace", index=False)
print(f"  ✅ {len(loyers):,} loyers chargés")

# ── 5. Logements sociaux ───────────────────────────────────────────
print("\nChargement logements_sociaux...")
social = pd.read_parquet("data/silver/logements_sociaux_silver.parquet")
social_light = social.drop(columns=['latitude', 'longitude'], errors='ignore')
social_light.to_sql("logements_sociaux", engine, if_exists="replace", index=False)
print(f"  ✅ {len(social_light):,} programmes chargés")

# ── 6. Filosofi revenus ────────────────────────────────────────────
print("\nChargement filosofi_revenus...")
filo = pd.read_parquet("data/silver/filosofi_iris_silver.parquet")
filo.to_sql("filosofi_revenus", engine, if_exists="replace", index=False)
print(f"  ✅ {len(filo):,} zones IRIS chargées")

# ── 7. Index pour performances API ────────────────────────────────
print("\nCréation des index...")
with engine.connect() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gold_arr ON gold_arrondissements(arrondissement)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dvf_arr ON dvf_transactions(arrondissement)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dvf_annee ON dvf_transactions(annee)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_loyers_arr ON loyers_reference(arrondissement)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_loyers_annee ON loyers_reference(annee)"))
    conn.commit()
print("  ✅ Index créés")

# ── Résumé des tables ──────────────────────────────────────────────
print("\n── Tables dans PostgreSQL ──")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass))
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(tablename::regclass) DESC
    """))
    for row in result:
        print(f"  {row[0]:<30} {row[1]}")