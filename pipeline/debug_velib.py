import geopandas as gpd
import pandas as pd

velib = gpd.read_file("data/silver/velib_silver.geojson")
print(f"Colonnes : {list(velib.columns)}")
print(f"Lignes : {len(velib)}")
print(f"\ncode_insee_commune samples :")
print(velib['code_insee_commune'].value_counts().head(10))
print(f"\nAperçu :")
print(velib[['id_station', 'nom_station', 'capacity', 'code_insee_commune']].head(5))