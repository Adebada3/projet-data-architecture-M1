import time
import os
import json
from sqlalchemy import create_engine, text

print("═" * 60)
print("BENCHMARK PIPELINE — Urban Data Explorer")
print("═" * 60)

# ── Comparaison tailles Raw vs Silver ─────────────────────────────
print("\n── Tailles fichiers Raw vs Silver ──")
comparaisons = [
    ("Loyers",    "data/raw/logement-encadrement-des-loyers.csv",
                  "data/silver/loyers_paris_silver.parquet"),
    ("Filosofi",  "data/raw/BASE_TD_FILO_IRIS_2021_DEC.csv",
                  "data/silver/filosofi_iris_silver.parquet"),
    ("Log.sociaux","data/raw/logements-sociaux-finances-a-paris.csv",
                  "data/silver/logements_sociaux_silver.parquet"),
]
for nom, raw, silver in comparaisons:
    if os.path.exists(raw) and os.path.exists(silver):
        r = os.path.getsize(raw) / 1e6
        s = os.path.getsize(silver) / 1e6
        print(f"  {nom:<14} Raw: {r:.1f} Mo → Silver: {s:.2f} Mo (÷{r/max(s,0.001):.0f})")

# ── Lecture Parquet vs CSV ─────────────────────────────────────────
print("\n── Lecture Parquet vs CSV (loyers) ──")
import pandas as pd

t1 = time.time()
pd.read_csv("data/raw/logement-encadrement-des-loyers.csv", sep=";")
temps_csv = time.time() - t1

t2 = time.time()
pd.read_parquet("data/silver/loyers_paris_silver.parquet")
temps_parquet = time.time() - t2

print(f"  CSV    : {temps_csv:.3f}s")
print(f"  Parquet: {temps_parquet:.3f}s")
print(f"  Gain   : {temps_csv/max(temps_parquet,0.001):.1f}x plus rapide")

# ── Performance PostgreSQL ─────────────────────────────────────────
print("\n── Performance requêtes PostgreSQL ──")
engine = create_engine("postgresql://cherylecheryle@localhost:5432/urban_data_explorer")

queries = [
    ("Gold 20 arrondissements",
     "SELECT * FROM gold_arrondissements"),
    ("Prix médian par arrondissement",
     "SELECT arrondissement, ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::numeric,0) FROM dvf_transactions GROUP BY arrondissement ORDER BY arrondissement"),
    ("IRIS Paris 992 zones",
     "SELECT code_iris, prix_m2_median FROM gold_iris"),
    ("Comparaison arr 6 vs 19",
     "SELECT * FROM gold_arrondissements WHERE arrondissement IN (6,19)"),
    ("Évolution prix arr 11",
     "SELECT annee, COUNT(*), ROUND(AVG(prix_m2)::numeric,0) FROM dvf_transactions WHERE arrondissement=11 GROUP BY annee ORDER BY annee"),
    ("GeoJSON arrondissements",
     "SELECT arrondissement, ST_AsGeoJSON(geometry) FROM geo_arrondissements"),
]

resultats_sql = []
with engine.connect() as conn:
    for nom, sql in queries:
        t = time.time()
        rows = conn.execute(text(sql)).fetchall()
        ms = (time.time() - t) * 1000
        print(f"  {nom:<35} {ms:6.1f}ms — {len(rows)} lignes")
        resultats_sql.append({"query": nom, "ms": round(ms,1), "rows": len(rows)})

# ── Tailles tables PostgreSQL ──────────────────────────────────────
print("\n── Tailles tables PostgreSQL ──")
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT tablename,
               pg_size_pretty(pg_total_relation_size(tablename::regclass)) as taille,
               (SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = t.tablename) as nb_cols
        FROM pg_tables t
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(tablename::regclass) DESC
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]:<30} {r[1]:<12} {r[2]} colonnes")

# ── Résumé ────────────────────────────────────────────────────────
print("\n" + "═" * 60)
print("RÉSUMÉ PERFORMANCES")
print("═" * 60)
stats = {
    "sources_ingérées": 18,
    "volume_brut_go": 4,
    "transactions_dvf": 165887,
    "zones_iris": 992,
    "scripts_pipeline": 18,
    "tables_postgresql": 7,
    "collections_mongodb": 2,
    "endpoints_api": 12,
    "gain_parquet_vs_csv": f"{temps_csv/max(temps_parquet,0.001):.1f}x",
    "requetes_sql": resultats_sql
}
for k, v in stats.items():
    if k != "requetes_sql":
        print(f"  {k:<30} {v}")

os.makedirs("data", exist_ok=True)
with open("data/benchmark_results.json", "w") as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)
print("\n✅ Résultats sauvegardés dans data/benchmark_results.json")
print("═" * 60)