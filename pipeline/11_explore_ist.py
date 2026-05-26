import pandas as pd

# Criminalité
print("── Criminalité ──")
crime = pd.read_csv("data/raw/donnee-dep-data.gouv-2025-geographie2025-produit-le2026-01-22.csv",
                    sep=";", low_memory=False)
print(f"  Colonnes : {list(crime.columns)}")
print(f"  Lignes : {len(crime):,}")
print(crime.head(3))

# Bruit
print("\n── Bruit routier ──")
bruit = pd.read_csv("data/raw/bruit-evolution-de-l-indice-du-bruit-mesure-sur-des-stations-parisiennes.csv",
                    sep=";", low_memory=False)
print(f"  Colonnes : {list(bruit.columns)}")
print(f"  Lignes : {len(bruit):,}")
print(bruit.head(3))

# Qualité air
print("\n── Qualité air ──")
air = pd.read_csv("data/raw/qualite-de-l-air-exposition-des-parisen-ne-s-au-no2-et-pm2-5.csv",
                  sep=";", low_memory=False)
print(f"  Colonnes : {list(air.columns)}")
print(f"  Lignes : {len(air):,}")
print(air.head(3))