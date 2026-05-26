import pandas as pd
import os

print("Lecture loyers...")
# Séparateur point-virgule sur opendata.paris.fr
df = pd.read_csv("data/raw/logement-encadrement-des-loyers.csv", sep=";", low_memory=False)

print(f"  Colonnes : {list(df.columns)}")
print(f"  Lignes : {len(df):,}")
print(f"\nAperçu :\n{df.head(3)}")