import pandas as pd
import numpy as np
import os

os.makedirs("data/silver", exist_ok=True)

# ════════════════════════════════════════════════════════════════════
# CRIMINALITÉ — filtre Paris (département 75)
# ════════════════════════════════════════════════════════════════════
print("── Criminalité ──")
crime = pd.read_csv(
    "data/raw/donnee-dep-data.gouv-2025-geographie2025-produit-le2026-01-22.csv",
    sep=";", low_memory=False)

paris_crime = crime[crime['Code_departement'].astype(str) == '75'].copy()
print(f"  Paris : {len(paris_crime):,} lignes")
print(f"  Indicateurs : {paris_crime['indicateur'].unique()}")
print(f"  Années : {sorted(paris_crime['annee'].unique())}")

# Pivot : une ligne par année, une colonne par indicateur
crime_pivot = paris_crime.pivot_table(
    index='annee',
    columns='indicateur',
    values='taux_pour_mille',
    aggfunc='first'
).reset_index()
crime_pivot.columns.name = None
crime_pivot['departement'] = '75'
print(f"\n  Aperçu pivot :\n{crime_pivot.head(3)}")

crime_pivot.to_parquet("data/silver/criminalite_paris_silver.parquet", index=False)
print(f"  ✅ Criminalité sauvegardée : {len(crime_pivot)} années")

# ════════════════════════════════════════════════════════════════════
# BRUIT ROUTIER — moyenne par année toutes stations
# ════════════════════════════════════════════════════════════════════
print("\n── Bruit routier ──")
bruit = pd.read_csv(
    "data/raw/bruit-evolution-de-l-indice-du-bruit-mesure-sur-des-stations-parisiennes.csv",
    sep=";", low_memory=False)

# Colonnes Lden (jour+nuit) et Ln (nuit) séparément
cols_lden = [c for c in bruit.columns if 'Lden' in c or 'lden' in c]
cols_ln   = [c for c in bruit.columns if ' Ln ' in c or 'ln_' in c]

bruit['lden_moyen'] = bruit[cols_lden].mean(axis=1, skipna=True).round(1)
bruit['ln_moyen']   = bruit[cols_ln].mean(axis=1, skipna=True).round(1)

bruit_silver = bruit[['Année', 'lden_moyen', 'ln_moyen']].rename(columns={'Année': 'annee'})
bruit_silver = bruit_silver.dropna(subset=['lden_moyen'])
bruit_silver['scope'] = 'Paris (moyenne stations)'

bruit_silver.to_parquet("data/silver/bruit_paris_silver.parquet", index=False)
print(f"  ✅ {len(bruit_silver)} années sauvegardées")
print(bruit_silver.sort_values('annee').to_string(index=False))

# ════════════════════════════════════════════════════════════════════
# QUALITÉ AIR — déjà par arrondissement
# ════════════════════════════════════════════════════════════════════
print("\n── Qualité air NO2 par arrondissement ──")
air = pd.read_csv(
    "data/raw/qualite-de-l-air-exposition-des-parisen-ne-s-au-no2-et-pm2-5.csv",
    sep=";", low_memory=False)

# Garder colonnes arrondissement NO2
cols_arr = ['Année'] + [c for c in air.columns if 'ardt soumis' in c and 'NO2' in c]
air_arr = air[cols_arr].copy()

# Renommer colonnes → arrondissement 1..20
rename_map = {'Année': 'annee'}
for col in cols_arr[1:]:
    # Extraire le numéro d'arrondissement
    num = ''.join(filter(str.isdigit, col.split('ardt')[0]))
    if num:
        rename_map[col] = f'arr_{int(num):02d}_nb_personnes_no2'
air_arr = air_arr.rename(columns=rename_map)

# Ajouter PM2.5 global
air_arr['pm25_parisiens_depasse_vr'] = air['Nbre Parisiens soumis à dépassement VR PM2.5']
air_arr['no2_parisiens_depasse_vr']  = air['Nbre Parisiens soumis à dépassement VR NO2']

air_arr = air_arr.dropna(subset=['annee'])
air_arr.to_parquet("data/silver/qualite_air_silver.parquet", index=False)
print(f"  ✅ {len(air_arr)} années sauvegardées")
print(air_arr[['annee', 'no2_parisiens_depasse_vr', 'pm25_parisiens_depasse_vr']].sort_values('annee').to_string(index=False))