import geopandas as gpd
import os

# ── Arrondissements ──────────────────────────────────────────────
print("── Arrondissements ──")
arr = gpd.read_file("data/raw/arrondissements.geojson")
print(f"  Colonnes : {list(arr.columns)}")
print(f"  Lignes : {len(arr)}")
print(arr.head(3))

# ── Espaces verts ────────────────────────────────────────────────
print("\n── Espaces verts ──")
ev = gpd.read_file("data/raw/espaces_verts.geojson")
print(f"  Colonnes : {list(ev.columns)}")
print(f"  Lignes : {len(ev):,}")
print(ev.head(2))

# ── Stations RATP ────────────────────────────────────────────────
print("\n── Stations RATP/RER ──")
ratp = gpd.read_file("data/raw/emplacement-des-gares-idf.geojson")
print(f"  Colonnes : {list(ratp.columns)}")
print(f"  Lignes : {len(ratp):,}")
print(ratp.head(2))

# ── Vélib' ───────────────────────────────────────────────────────
print("\n── Vélib' ──")
velib = gpd.read_file("data/raw/velib-disponibilite-en-temps-reel.geojson")
print(f"  Colonnes : {list(velib.columns)}")
print(f"  Lignes : {len(velib):,}")
print(velib.head(2))