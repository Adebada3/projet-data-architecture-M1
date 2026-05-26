import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text

DB_URL = "postgresql://cherylecheryle@localhost:5432/urban_data_explorer"
engine = create_engine(DB_URL)

print("── Gold IRIS — prix médian par zone ──")

# DVF avec coordonnées
dvf = pd.read_parquet("data/silver/dvf_paris_silver.parquet")
dvf = dvf.dropna(subset=['latitude', 'longitude'])
print(f"  DVF avec coords : {len(dvf):,}")

# Contours IRIS
iris = gpd.read_file(
    "data/raw/contours-iris/CONTOURS-IRIS_3-0__SHP_LAMB93_FXX_2024-01-01/"
    "CONTOURS-IRIS/1_DONNEES_LIVRAISON_2024-12-00164/"
    "CONTOURS-IRIS_3-0_SHP_LAMB93_FXX-ED2024-01-01/CONTOURS-IRIS.shp"
)
iris_paris = iris[iris['INSEE_COM'].astype(str).str.startswith('75')].copy()
iris_paris = iris_paris.to_crs("EPSG:4326")

# Convertir DVF en GeoDataFrame
gdf_dvf = gpd.GeoDataFrame(
    dvf,
    geometry=gpd.points_from_xy(dvf['longitude'], dvf['latitude']),
    crs="EPSG:4326"
)

# Jointure spatiale DVF → IRIS
print("  Jointure spatiale DVF × IRIS...")
joined = gpd.sjoin(gdf_dvf, iris_paris[['CODE_IRIS','NOM_IRIS','geometry']],
                   how="left", predicate="within")

# Agrégation par IRIS
agg = joined.groupby('CODE_IRIS').agg(
    prix_m2_median=('prix_m2', 'median'),
    prix_m2_moyen=('prix_m2', 'mean'),
    nb_transactions=('id_mutation', 'count'),
    surface_median=('surface_reelle_bati', 'median'),
    annee_min=('annee', 'min'),
    annee_max=('annee', 'max'),
).round(1).reset_index()

print(f"  IRIS avec données DVF : {len(agg)}")

# Fusionner avec géométries IRIS
iris_gold = iris_paris.merge(agg, on='CODE_IRIS', how='left')
iris_gold = iris_gold.rename(columns={
    'CODE_IRIS': 'code_iris',
    'NOM_IRIS': 'nom_iris',
    'INSEE_COM': 'insee_com',
    'NOM_COM': 'nom_com',
})

# Charger dans PostgreSQL
iris_gold[['code_iris','nom_iris','insee_com','prix_m2_median',
           'prix_m2_moyen','nb_transactions','surface_median',
           'annee_min','annee_max','geometry']].to_postgis(
    "gold_iris", engine, if_exists="replace", index=False
)

print(f"✅ {len(iris_gold)} zones IRIS chargées dans gold_iris")
print(f"   Prix médian IRIS : {agg['prix_m2_median'].median():.0f} €/m²")
print(f"   IRIS sans données : {iris_gold['prix_m2_median'].isna().sum()}")