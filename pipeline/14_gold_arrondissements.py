import pandas as pd
import geopandas as gpd
import numpy as np
import os

os.makedirs("data/gold", exist_ok=True)

# ── Base : les 20 arrondissements ──────────────────────────────────
arr = gpd.read_file("data/silver/arrondissements_silver.geojson")
gold = arr[['arrondissement', 'nom_arrondissement', 'surface_m2', 'geometry']].copy()
gold['arrondissement'] = gold['arrondissement'].astype(int)
gold = gold.sort_values('arrondissement').reset_index(drop=True)

# ── DVF : prix médian + évolution ─────────────────────────────────
dvf = pd.read_parquet("data/silver/dvf_paris_silver.parquet")
dvf_agg = dvf.groupby('arrondissement').agg(
    prix_m2_median=('prix_m2', 'median'),
    nb_transactions=('id_mutation', 'count'),
    surface_median=('surface_reelle_bati', 'median'),
).round(1).reset_index()
# Evolution prix : 2021 vs 2024
dvf_evol = dvf[dvf['annee'].isin([2021, 2024])].groupby(['arrondissement','annee'])['prix_m2'].median().unstack()
if 2021 in dvf_evol.columns and 2024 in dvf_evol.columns:
    dvf_evol['evol_prix_2021_2024_pct'] = ((dvf_evol[2024] - dvf_evol[2021]) / dvf_evol[2021] * 100).round(1)
    dvf_agg = dvf_agg.merge(dvf_evol[['evol_prix_2021_2024_pct']].reset_index(), on='arrondissement', how='left')
gold = gold.merge(dvf_agg, on='arrondissement', how='left')

# ── Loyers : loyer médian de référence ────────────────────────────
loyers = pd.read_parquet("data/silver/loyers_paris_silver.parquet")
loyers_agg = loyers[loyers['annee'] == loyers['annee'].max()].groupby('arrondissement').agg(
    loyer_ref_median=('loyer_ref', 'median'),
    loyer_max_median=('loyer_max', 'median'),
).round(2).reset_index()
gold = gold.merge(loyers_agg, on='arrondissement', how='left')

# ── Logements sociaux : part du parc ──────────────────────────────
social = pd.read_parquet("data/silver/logements_sociaux_silver.parquet")
social_agg = social.groupby('arrondissement').agg(
    nb_logements_sociaux=('nb_logements', 'sum'),
    nb_programmes=('id_livraison', 'count'),
).reset_index()
gold = gold.merge(social_agg, on='arrondissement', how='left')

# ── Filosofi : revenus ────────────────────────────────────────────
filo = pd.read_parquet("data/silver/filosofi_iris_silver.parquet")
filo_agg = filo.groupby('arrondissement').agg(
    revenu_median=('revenu_median', 'median'),
    taux_pauvrete=('taux_pauvrete', 'median'),
    indice_gini=('indice_gini', 'median'),
).round(1).reset_index()
gold = gold.merge(filo_agg, on='arrondissement', how='left')

# ── Indice accessibilité : prix/m² / revenu annuel ────────────────
gold['indice_pression_immo'] = (gold['prix_m2_median'] * 40 / gold['revenu_median']).round(2)

# ── IAU : Attractivité urbaine ────────────────────────────────────
bpe = gpd.read_file("data/silver/bpe_silver.geojson")
bpe['arrondissement'] = pd.to_numeric(bpe['arrondissement'], errors='coerce')
# Densités par domaine
for domaine, col in [
    ('Commerces', 'nb_commerces'),
    ('Santé et action sociale', 'nb_sante'),
    ('Enseignement', 'nb_scolaire'),
]:
    agg = bpe[bpe['domaine'] == domaine].groupby('arrondissement').size().reset_index(name=col)
    gold = gold.merge(agg, on='arrondissement', how='left')

resto = gpd.read_file("data/silver/restaurants_silver.geojson")
resto_agg = resto.groupby('arrondissement').size().reset_index(name='nb_restos_bars')
gold = gold.merge(resto_agg, on='arrondissement', how='left')

mon = gpd.read_file("data/silver/monuments_silver.geojson")
mon['arrondissement'] = pd.to_numeric(mon['arrondissement'], errors='coerce')
mon_agg = mon.groupby('arrondissement').size().reset_index(name='nb_monuments')
gold = gold.merge(mon_agg, on='arrondissement', how='left')

# ── IQV : Qualité de vie verte ────────────────────────────────────
ev = gpd.read_file("data/silver/espaces_verts_silver.geojson")
ev['arrondissement'] = pd.to_numeric(ev['arrondissement'], errors='coerce')
ev_agg = ev.groupby('arrondissement').agg(
    nb_espaces_verts=('nom', 'count'),
    surface_verte_m2=('surface_m2', 'sum'),
).reset_index()
gold = gold.merge(ev_agg, on='arrondissement', how='left')

arbres = pd.read_parquet("data/silver/arbres_silver.parquet")
arbres_agg = arbres.groupby('arrondissement').size().reset_index(name='nb_arbres')
gold = gold.merge(arbres_agg, on='arrondissement', how='left')

sante = gpd.read_file("data/silver/sante_silver.geojson")
sante['arrondissement'] = pd.to_numeric(sante['arrondissement'], errors='coerce')
sante_agg = sante.groupby('arrondissement').size().reset_index(name='nb_pros_sante')
gold = gold.merge(sante_agg, on='arrondissement', how='left')

# ── IMM : Mobilité ────────────────────────────────────────────────
ratp = gpd.read_file("data/silver/stations_ratp_silver.geojson")
ratp_agg = ratp.groupby('arrondissement').size().reset_index(name='nb_stations_transport')
gold = gold.merge(ratp_agg, on='arrondissement', how='left')

velib = gpd.read_file("data/silver/velib_silver.geojson")
velib = velib.set_crs("EPSG:4326", allow_override=True)

# Jointure spatiale avec les arrondissements
velib_join = gpd.sjoin(
    velib,
    arr[['arrondissement', 'geometry']],
    how="left", predicate="within"
).drop(columns=['index_right'])

velib_agg = velib_join.groupby('arrondissement').agg(
    nb_stations_velib=('id_station', 'count'),
    capacite_velib=('capacity', 'sum'),
).reset_index()
gold = gold.merge(velib_agg, on='arrondissement', how='left')

velo = gpd.read_file("data/silver/pistes_cyclables_silver.geojson")
velo['arrondissement'] = pd.to_numeric(velo['arrondissement'], errors='coerce')
velo_agg = velo.groupby('arrondissement').size().reset_index(name='nb_troncons_velo')
gold = gold.merge(velo_agg, on='arrondissement', how='left')

# ── Normalisation 0-100 pour les scores ───────────────────────────
def normalize(series):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - mn) / (mx - mn) * 100).round(1)

gold = gold.fillna(0)
gold['surface_km2'] = gold['surface_m2'] / 1_000_000

# Scores IAU (0-100)
gold['score_iau'] = (
    normalize(gold['nb_commerces'])       * 0.25 +
    normalize(gold['nb_restos_bars'])     * 0.20 +
    normalize(gold['nb_scolaire'])        * 0.25 +
    normalize(gold['nb_sante'])           * 0.20 +
    normalize(gold['nb_monuments'])       * 0.10
).round(1)

# Scores IQV (0-100)
gold['score_iqv'] = (
    normalize(gold['surface_verte_m2'])   * 0.40 +
    normalize(gold['nb_arbres'])          * 0.30 +
    normalize(gold['nb_pros_sante'])      * 0.30
).round(1)

# Scores IMM (0-100)
gold['score_imm'] = (
    normalize(gold['nb_stations_transport']) * 0.40 +
    normalize(gold['capacite_velib'])        * 0.30 +
    normalize(gold['nb_troncons_velo'])      * 0.30
).round(1)

# Score IST : inverse (moins de crime/bruit = mieux)
gold['score_ist'] = (
    normalize(100 - normalize(gold['taux_pauvrete'])) * 0.50 +
    normalize(gold['revenu_median'])                  * 0.50
).round(1)

# ── Sauvegarde Gold ───────────────────────────────────────────────
gold.to_file("data/gold/gold_arrondissements.geojson", driver="GeoJSON")

# Version tabulaire sans géométrie
gold_df = gold.drop(columns=['geometry'])
gold_df.to_parquet("data/gold/gold_arrondissements.parquet", index=False)
gold_df.to_csv("data/gold/gold_arrondissements.csv", index=False)

print("✅ Gold sauvegardé !")
print(f"\nTop 5 arrondissements par score IAU :")
print(gold_df.nlargest(5, 'score_iau')[['arrondissement','score_iau','nb_commerces','nb_restos_bars']].to_string(index=False))
print(f"\nTop 5 par score IQV :")
print(gold_df.nlargest(5, 'score_iqv')[['arrondissement','score_iqv','surface_verte_m2','nb_arbres']].to_string(index=False))
print(f"\nTop 5 par score IMM :")
print(gold_df.nlargest(5, 'score_imm')[['arrondissement','score_imm','nb_stations_transport','capacite_velib']].to_string(index=False))
print(f"\nColonnes Gold : {list(gold_df.columns)}")