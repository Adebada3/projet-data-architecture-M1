import geopandas as gpd
import pandas as pd
import os

os.makedirs("data/silver", exist_ok=True)

# ════════════════════════════════════════════════════════════════════
# ARRONDISSEMENTS
# ════════════════════════════════════════════════════════════════════
print("── Arrondissements ──")
arr = gpd.read_file("data/raw/arrondissements.geojson")
arr = arr.rename(columns={
    'c_ar':     'arrondissement',
    'c_arinsee':'code_insee',
    'l_ar':     'nom_arrondissement',
    'surface':  'surface_m2',
})
arr['arrondissement'] = arr['arrondissement'].astype(int)
arr_silver = arr[['arrondissement', 'code_insee', 'nom_arrondissement', 'surface_m2', 'geometry']]
arr_silver = arr_silver.set_crs("EPSG:4326", allow_override=True)
arr_silver.to_file("data/silver/arrondissements_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(arr_silver)} arrondissements sauvegardés")

# ════════════════════════════════════════════════════════════════════
# ESPACES VERTS
# ════════════════════════════════════════════════════════════════════
print("\n── Espaces verts ──")
ev = gpd.read_file("data/raw/espaces_verts.geojson")
ev = ev.rename(columns={
    'nsq_espace_vert':      'id_ev',
    'nom_ev':               'nom',
    'type_ev':              'type',
    'categorie':            'categorie',
    'surface_totale_reelle':'surface_m2',
    'ouvert_ferme':         'ouvert',
})
ev_silver = ev[['id_ev', 'nom', 'type', 'categorie', 'surface_m2', 'ouvert', 'geometry']]
ev_silver = ev_silver.set_crs("EPSG:4326", allow_override=True)

# Jointure spatiale pour obtenir l'arrondissement
ev_silver = gpd.sjoin(
    ev_silver.to_crs("EPSG:4326"),
    arr_silver[['arrondissement', 'geometry']].to_crs("EPSG:4326"),
    how="left", predicate="intersects"
).drop(columns=['index_right'])

ev_silver.to_file("data/silver/espaces_verts_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(ev_silver):,} espaces verts sauvegardés")
print(f"  Surface totale verte : {ev_silver['surface_m2'].sum()/10000:.0f} hectares")
print(f"  Par arrondissement (top 5) :")
print(ev_silver.groupby('arrondissement')['surface_m2'].sum().sort_values(ascending=False).head(5).to_string())

# ════════════════════════════════════════════════════════════════════
# STATIONS RATP/RER — filtre Paris uniquement
# ════════════════════════════════════════════════════════════════════
print("\n── Stations RATP/RER ──")
ratp = gpd.read_file("data/raw/emplacement-des-gares-idf.geojson")
ratp = ratp.set_crs("EPSG:4326", allow_override=True)

# Jointure spatiale pour garder seulement les stations dans Paris
ratp_paris = gpd.sjoin(
    ratp,
    arr_silver[['arrondissement', 'geometry']].to_crs("EPSG:4326"),
    how="inner", predicate="within"
).drop(columns=['index_right'])

ratp_silver = ratp_paris[['nom_gares', 'mode', 'res_com', 'arrondissement', 'geometry']].rename(columns={
    'nom_gares': 'nom_station',
    'res_com':   'ligne',
})
ratp_silver.to_file("data/silver/stations_ratp_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(ratp_silver):,} stations Paris sauvegardées")
print(f"  Par mode :\n{ratp_silver['mode'].value_counts().to_string()}")

# ════════════════════════════════════════════════════════════════════
# VÉLIB'
# ════════════════════════════════════════════════════════════════════
print("\n── Vélib' ──")
velib = gpd.read_file("data/raw/velib-disponibilite-en-temps-reel.geojson")
velib = velib.set_crs("EPSG:4326", allow_override=True)

# Filtre Paris uniquement via code INSEE
velib_paris = velib[velib['code_insee_commune'].astype(str).str.startswith('75')]

velib_silver = velib_paris[[
    'stationcode', 'name', 'capacity',
    'nom_arrondissement_communes', 'code_insee_commune', 'geometry'
]].rename(columns={
    'stationcode':                  'id_station',
    'name':                         'nom_station',
    'nom_arrondissement_communes':  'arrondissement_nom',
})
velib_silver.to_file("data/silver/velib_silver.geojson", driver="GeoJSON")
print(f"  ✅ {len(velib_silver):,} stations Vélib' Paris sauvegardées")
print(f"  Capacité totale : {velib_silver['capacity'].sum():,} vélos")