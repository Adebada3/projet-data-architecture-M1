import pandas as pd
import os

os.makedirs("data/silver", exist_ok=True)

print("── Filosofi Silver ──")
df = pd.read_csv("data/raw/BASE_TD_FILO_IRIS_2021_DEC.csv", sep=";", low_memory=False)

# Filtre Paris
paris = df[df['IRIS'].astype(str).str.startswith('75')].copy()
print(f"  {len(paris):,} zones IRIS Paris")

# Les valeurs utilisent la virgule comme séparateur décimal → convertir
cols_numeriques = [c for c in paris.columns if c != 'IRIS']
for col in cols_numeriques:
    paris[col] = paris[col].astype(str).str.replace(',', '.').str.strip()
    paris[col] = pd.to_numeric(paris[col], errors='coerce')

# Extraire arrondissement depuis le code IRIS
# Format IRIS Paris : 751XXYYYY où XX = arrondissement
paris['code_commune'] = paris['IRIS'].astype(str).str[:5]   # ex: 75110
paris['arrondissement'] = paris['IRIS'].astype(str).str[3:5].astype(int)  # ex: 10

# Renommer colonnes pour lisibilité
paris = paris.rename(columns={
    'IRIS':          'code_iris',
    'DEC_MED21':     'revenu_median',
    'DEC_TP6021':    'taux_pauvrete',
    'DEC_Q121':      'q1_revenu',
    'DEC_Q321':      'q3_revenu',
    'DEC_D121':      'd1_revenu',
    'DEC_D921':      'd9_revenu',
    'DEC_RD21':      'rapport_interdecile',
    'DEC_GI21':      'indice_gini',
    'DEC_PIMP21':    'part_imposition',
    'DEC_S80S2021':  'ratio_s80_s20',
})

cols_silver = [
    'code_iris', 'code_commune', 'arrondissement',
    'revenu_median', 'taux_pauvrete',
    'q1_revenu', 'q3_revenu', 'd1_revenu', 'd9_revenu',
    'rapport_interdecile', 'indice_gini',
    'part_imposition', 'ratio_s80_s20'
]

silver = paris[cols_silver].dropna(subset=['revenu_median'])
silver.to_parquet("data/silver/filosofi_iris_silver.parquet", index=False)

print(f"  ✅ {len(silver):,} zones sauvegardées")
print(f"\n  Revenu médian par arrondissement (€/an) :")
print(silver.groupby('arrondissement')['revenu_median'].median().round(0).to_string())
print(f"\n  Taux de pauvreté par arrondissement (%) :")
print(silver.groupby('arrondissement')['taux_pauvrete'].median().round(1).to_string())