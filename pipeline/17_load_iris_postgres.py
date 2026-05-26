import geopandas as gpd
from sqlalchemy import create_engine

DB_URL = "postgresql://cherylecheryle@localhost:5432/urban_data_explorer"
engine = create_engine(DB_URL)

SHP = "data/raw/contours-iris/CONTOURS-IRIS_3-0__SHP_LAMB93_FXX_2024-01-01/CONTOURS-IRIS/1_DONNEES_LIVRAISON_2024-12-00164/CONTOURS-IRIS_3-0_SHP_LAMB93_FXX-ED2024-01-01/CONTOURS-IRIS.shp"

print("Lecture IRIS France...")
iris = gpd.read_file(SHP)
print(f"  Total France : {len(iris):,} zones")
print(f"  Colonnes : {list(iris.columns)}")
print(f"  CRS : {iris.crs}")

# Filtre Paris + reprojection WGS84
iris_paris = iris[iris['INSEE_COM'].astype(str).str.startswith('75')].copy()
iris_paris = iris_paris.to_crs("EPSG:4326")
print(f"  Paris : {len(iris_paris)} zones IRIS")

# Charger dans PostgreSQL
iris_paris.to_postgis("geo_iris", engine, if_exists="replace", index=False)
print(f"✅ {len(iris_paris)} zones IRIS chargées dans PostgreSQL")
print(iris_paris[['CODE_IRIS','NOM_IRIS','INSEE_COM']].head(5))