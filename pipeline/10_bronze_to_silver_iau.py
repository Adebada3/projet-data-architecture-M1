import geopandas as gpd
import pandas as pd
import os

os.makedirs("data/silver", exist_ok=True)

arr = gpd.read_file("data/silver/arrondissements_silver.geojson")
arr = arr.set_crs("EPSG:4326", allow_override=True)

# ════════════════════════════════════════════════════════════════════
# BPE
# ════════════════════════════════════════════════════════════════════
print("── BPE Équipements ──")
bpe = pd.read_csv("data/raw/bpe23-nettoye.csv", sep=";", low_memory=False)

# Filtre Paris
bpe_paris = bpe[bpe['Code département et commune'].astype(str).str.startswith('75')].copy()
print(f"  Paris : {len(bpe_paris):,} équipements")
print(f"  Domaines :\n{bpe_paris['Domaine'].value_counts().to_string()}")

# Coordonnées Lambert X/Y → GeoDataFrame
bpe_paris = bpe_paris.dropna(subset=['Lambert X', 'Lambert Y'])
gdf_bpe = gpd.GeoDataFrame(
    bpe_paris,
    geometry=gpd.points_from_xy(bpe_paris['Lambert X'], bpe_paris['Lambert Y']),
    crs="EPSG:2154"
).to_crs("EPSG:4326")

# Jointure spatiale
gdf_bpe = gpd.sjoin(
    gdf_bpe,
    arr[['arrondissement', 'geometry']],
    how="left", predicate="within"
).drop(columns=['index_right'])

bpe_silver = gdf_bpe[[
    "Type d'équipement", 'Type', 'Domaine', 'Sous-domaine',
    'Code département et commune', 'arrondissement', 'geometry'
]].rename(columns={
    "Type d'équipement": 'type_equipement',
    'Type':              'type_label',
    'Domaine':           'domaine',
    'Sous-domaine':      'sous_domaine',
    'Code département et commune': 'code_commune',
})

bpe_silver.to_file("data/silver/bpe_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(bpe_silver):,} équipements sauvegardés")

# ════════════════════════════════════════════════════════════════════
# MONUMENTS HISTORIQUES
# ════════════════════════════════════════════════════════════════════
print("\n── Monuments historiques ──")
mon = pd.read_csv(
    "data/raw/liste-des-immeubles-proteges-au-titre-des-monuments-historiques.csv",
    sep=";", low_memory=False)
print(f"  Colonnes : {list(mon.columns)}")
print(f"  Lignes : {len(mon):,}")
print(mon.head(2))

# ════════════════════════════════════════════════════════════════════
# MONUMENTS HISTORIQUES (suite)
# ════════════════════════════════════════════════════════════════════

# Filtre Paris via département
mon_paris = mon[mon['Departement_format_numerique'].astype(str) == '75'].copy()
print(f"  Paris : {len(mon_paris):,} monuments")

# Extraire lat/lon depuis 'coordonnees_au_format_WGS84' → "lat, lon"
mon_paris = mon_paris.dropna(subset=['coordonnees_au_format_WGS84'])
coords = mon_paris['coordonnees_au_format_WGS84'].str.split(',', expand=True)
mon_paris['latitude']  = coords[0].astype(float)
mon_paris['longitude'] = coords[1].astype(float)

gdf_mon = gpd.GeoDataFrame(
    mon_paris,
    geometry=gpd.points_from_xy(mon_paris['longitude'], mon_paris['latitude']),
    crs="EPSG:4326"
)

# Jointure spatiale → arrondissement
gdf_mon = gpd.sjoin(
    gdf_mon,
    arr[['arrondissement', 'geometry']],
    how="left", predicate="within"
).drop(columns=['index_right'])

mon_silver = gdf_mon[[
    'Reference', 'Denomination_de_l_edifice',
    'Adresse_forme_editoriale', 'Nature_de_la_protection',
    'Typologie_de_la_protection', 'Date_et_typologie_de_la_protection',
    'Siecle_de_la_campagne_principale_de_construction',
    'arrondissement', 'latitude', 'longitude', 'geometry'
]].rename(columns={
    'Reference':                                        'id_monument',
    'Denomination_de_l_edifice':                        'nom',
    'Adresse_forme_editoriale':                         'adresse',
    'Nature_de_la_protection':                          'nature_protection',
    'Typologie_de_la_protection':                       'type_protection',
    'Date_et_typologie_de_la_protection':               'date_protection',
    'Siecle_de_la_campagne_principale_de_construction': 'siecle',
})

mon_silver.to_file("data/silver/monuments_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(mon_silver):,} monuments sauvegardés")
print(f"  Par arrondissement (top 5) :")
print(mon_silver.groupby('arrondissement')['id_monument'].count().sort_values(ascending=False).head(5).to_string())

# ════════════════════════════════════════════════════════════════════
# OSM RESTAURANTS
# ════════════════════════════════════════════════════════════════════
print("\n── OSM Restaurants ──")
resto = gpd.read_file("data/raw/osm-restaurant-fr.geojson")
print(f"  Total France : {len(resto):,}")
print(f"  Colonnes : {list(resto.columns[:10])}...")
resto = resto.set_crs("EPSG:4326", allow_override=True)

# Filtre Paris via jointure spatiale
resto_paris = gpd.sjoin(
    resto,
    arr[['arrondissement', 'geometry']],
    how="inner", predicate="within"
).drop(columns=['index_right'])

print(f"  Paris : {len(resto_paris):,} restaurants/bars")
print(f"  Types :\n{resto_paris['type'].value_counts().head(8).to_string()}")

# Colonnes utiles
cols_r = ['type', 'arrondissement', 'geometry']
# Ajouter 'name' si elle existe
if 'name' in resto_paris.columns:
    cols_r = ['name'] + cols_r
if 'cuisine' in resto_paris.columns:
    cols_r.append('cuisine')

resto_silver = resto_paris[cols_r]
resto_silver.to_file("data/silver/restaurants_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(resto_silver):,} établissements sauvegardés")
print(f"  Par arrondissement (top 5) :")
print(resto_silver.groupby('arrondissement')['type'].count().sort_values(ascending=False).head(5).to_string())