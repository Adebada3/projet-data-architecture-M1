import pandas as pd
import os

os.makedirs("data/silver", exist_ok=True)

print("── Filosofi IRIS ──")
df = pd.read_csv("data/raw/BASE_TD_FILO_IRIS_2021_DEC.csv", sep=";", low_memory=False)

print(f"  Colonnes : {list(df.columns)}")
print(f"  Lignes : {len(df):,}")
print(f"\nAperçu :\n{df.head(3)}")

# Filtre Paris : code IRIS commence par 75
paris = df[df['IRIS'].astype(str).str.startswith('75')]
print(f"\n  IRIS Paris : {len(paris):,} zones")
print(f"\n  Colonnes disponibles (revenus) :")
# Afficher colonnes liées aux revenus
cols_revenus = [c for c in df.columns if any(x in c for x in ['MED', 'TP', 'D1', 'D9', 'RD', 'Q1', 'Q3'])]
print(f"  {cols_revenus}")