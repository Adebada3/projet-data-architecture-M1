import pandas as pd
import geopandas as gpd
import os

os.makedirs("data/silver", exist_ok=True)
arr = gpd.read_file("data/silver/arrondissements_silver.geojson").set_crs("EPSG:4326", allow_override=True)

# ════════════════════════════════════════════════════════════════════
# ARBRES DE PARIS
# ════════════════════════════════════════════════════════════════════
print("── Arbres de Paris ──")
arbres = pd.read_csv("data/raw/les-arbres.csv", sep=";", low_memory=False)

# Extraire lat/lon
arbres[['latitude', 'longitude']] = arbres['geo_point_2d'].str.split(',', expand=True).astype(float)

# Nettoyage arrondissement
arbres['arrondissement'] = (
    arbres['ARRONDISSEMENT'].astype(str)
    .str.extract(r'(\d+)')
    .astype(float)
    .astype('Int64')
)

arbres_silver = arbres[[
    'IDBASE', 'arrondissement', 'TYPE EMPLACEMENT', 'DOMANIALITE',
    'LIBELLE FRANCAIS', 'GENRE', 'ESPECE',
    'HAUTEUR (m)', 'CIRCONFERENCE (cm)', 'STADE DE DEVELOPPEMENT',
    'REMARQUABLE', 'latitude', 'longitude'
]].rename(columns={
    'IDBASE':               'id_arbre',
    'TYPE EMPLACEMENT':     'type_emplacement',
    'DOMANIALITE':          'domanialite',
    'LIBELLE FRANCAIS':     'nom_commun',
    'GENRE':                'genre',
    'ESPECE':               'espece',
    'HAUTEUR (m)':          'hauteur_m',
    'CIRCONFERENCE (cm)':   'circonf_cm',
    'STADE DE DEVELOPPEMENT': 'stade',
    'REMARQUABLE':          'remarquable',
})

arbres_silver = arbres_silver.dropna(subset=['arrondissement'])
arbres_silver.to_parquet("data/silver/arbres_silver.parquet", index=False)
print(f"  ✅ {len(arbres_silver):,} arbres sauvegardés")
print(f"  Par arrondissement (top 5) :")
print(arbres_silver.groupby('arrondissement')['id_arbre'].count().sort_values(ascending=False).head(5).to_string())

# ════════════════════════════════════════════════════════════════════
# PROFESSIONNELS DE SANTÉ — filtre Paris
# ════════════════════════════════════════════════════════════════════
print("\n── Pros de santé ──")
sante = pd.read_csv(
    "data/raw/annuaire-et-localisation-des-professionnels-de-sante.csv",
    sep=";", low_memory=False,
    usecols=['Nom du professionnel', 'Profession', 'Adresse',
             'Commune', 'code_insee', 'Coordonnées']
)
print(f"  Total IDF : {len(sante):,}")

# Filtre Paris
sante_paris = sante[sante['code_insee'].astype(str).str.startswith('75')].copy()
print(f"  Paris : {len(sante_paris):,}")
print(f"  Professions :\n{sante_paris['Profession'].value_counts().head(10).to_string()}")

# Extraire lat/lon depuis Coordonnées
sante_paris = sante_paris.dropna(subset=['Coordonnées'])
coords = sante_paris['Coordonnées'].str.split(',', expand=True)
sante_paris['latitude']  = pd.to_numeric(coords[0], errors='coerce')
sante_paris['longitude'] = pd.to_numeric(coords[1], errors='coerce')
sante_paris = sante_paris.dropna(subset=['latitude', 'longitude'])

# Jointure spatiale → arrondissement
gdf_sante = gpd.GeoDataFrame(
    sante_paris,
    geometry=gpd.points_from_xy(sante_paris['longitude'], sante_paris['latitude']),
    crs="EPSG:4326"
)
gdf_sante = gpd.sjoin(
    gdf_sante,
    arr[['arrondissement', 'geometry']],
    how="left", predicate="within"
).drop(columns=['index_right'])

sante_silver = gdf_sante[[
    'Nom du professionnel', 'Profession', 'Adresse',
    'Commune', 'code_insee', 'arrondissement',
    'latitude', 'longitude', 'geometry'
]].rename(columns={
    'Nom du professionnel': 'nom',
    'Profession':           'profession',
    'Adresse':              'adresse',
    'Commune':              'commune',
})

sante_silver.to_file("data/silver/sante_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(sante_silver):,} pros de santé sauvegardés")
print(f"  Par arrondissement (top 5) :")
print(sante_silver.groupby('arrondissement')['nom'].count().sort_values(ascending=False).head(5).to_string())

# ════════════════════════════════════════════════════════════════════
# PISTES CYCLABLES
# ════════════════════════════════════════════════════════════════════
print("\n── Pistes cyclables ──")
velo = gpd.read_file("data/raw/amenagements-cyclables.geojson")
velo = velo.set_crs("EPSG:4326", allow_override=True)

# Le fichier a déjà une colonne arrondissement — on la renomme avant sjoin
if 'arrondissement' in velo.columns:
    velo = velo.rename(columns={'arrondissement': 'arr_original'})

# Jointure spatiale → arrondissement depuis notre référentiel
velo = gpd.sjoin(
    velo,
    arr[['arrondissement', 'geometry']],
    how="left", predicate="intersects"
).drop(columns=['index_right'])

# Colonnes utiles — on garde ce qui existe
cols_velo = ['arrondissement', 'geometry']
for c in ['nom', 'amenagement', 'cote_amenagement', 'sens',
          'surface', 'coronapiste', 'voie_a_sens_unique']:
    if c in velo.columns:
        cols_velo.append(c)

velo_silver = velo[cols_velo]
velo_silver.to_file("data/silver/pistes_cyclables_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(velo_silver):,} tronçons sauvegardés")
print(f"  Par arrondissement (top 5) :")
print(velo_silver.groupby('arrondissement')['geometry'].count()
      .sort_values(ascending=False).head(5).to_string())