import pandas as pd
import os

# ── BRONZE : lecture brute ──────────────────────────────────────────
print("Lecture DVF brut...")
df = pd.read_csv("data/raw/dvf.csv",
                 sep=",",
                 low_memory=False)
print(f"  Total brut : {len(df):,} lignes")

# ── FILTRE 1 : Paris uniquement ─────────────────────────────────────
paris = df[df['code_commune'].astype(str).str.startswith('75')].copy()
print(f"  Paris uniquement : {len(paris):,} lignes")

# ── FILTRE 2 : Appartements et Maisons seulement ────────────────────
# On exclut Dépendances (caves/parkings) et locaux commerciaux
paris = paris[paris['type_local'].isin(['Appartement', 'Maison'])]
print(f"  Après filtre type_local : {len(paris):,} lignes")

# ── FILTRE 3 : Valeurs cohérentes ───────────────────────────────────
# Supprimer lignes sans prix ou sans surface
paris = paris.dropna(subset=['valeur_fonciere', 'surface_reelle_bati'])
# Supprimer surface <= 0 ou aberrante (> 1000 m²)
paris = paris[(paris['surface_reelle_bati'] > 0) & 
              (paris['surface_reelle_bati'] <= 1000)]
# Supprimer prix <= 0
paris = paris[paris['valeur_fonciere'] > 0]
print(f"  Après nettoyage valeurs : {len(paris):,} lignes")

# ── CALCUL PRIX AU M² ───────────────────────────────────────────────
paris['prix_m2'] = paris['valeur_fonciere'] / paris['surface_reelle_bati']
# Supprimer prix/m² aberrants (< 500 ou > 50 000 €/m²)
paris = paris[(paris['prix_m2'] >= 500) & (paris['prix_m2'] <= 50000)]
print(f"  Après filtre prix/m² : {len(paris):,} lignes")

# ── EXTRACTION ARRONDISSEMENT ────────────────────────────────────────
# code_commune Paris = 75101 à 75120 → arrondissement = les 2 derniers chiffres
paris['arrondissement'] = paris['code_commune'].astype(str).str[-2:].astype(int)
print(f"\n  Arrondissements trouvés : {sorted(paris['arrondissement'].unique())}")

# ── TYPAGE ET NETTOYAGE FINAL ────────────────────────────────────────
paris['date_mutation'] = pd.to_datetime(paris['date_mutation'])
paris['annee'] = paris['date_mutation'].dt.year
paris['mois'] = paris['date_mutation'].dt.month

# Colonnes utiles pour le projet
cols_silver = [
    'id_mutation', 'date_mutation', 'annee', 'mois',
    'arrondissement', 'code_commune',
    'adresse_nom_voie', 'code_postal',
    'type_local', 'surface_reelle_bati', 'nombre_pieces_principales',
    'valeur_fonciere', 'prix_m2',
    'latitude', 'longitude'
]
paris_silver = paris[cols_silver]

# ── SAUVEGARDE SILVER ────────────────────────────────────────────────
os.makedirs("data/silver", exist_ok=True)
output_path = "data/silver/dvf_paris_silver.parquet"
paris_silver.to_parquet(output_path, index=False)
print(f"\n✅ Silver sauvegardé : {output_path}")
print(f"   {len(paris_silver):,} transactions · {paris_silver['annee'].min()}-{paris_silver['annee'].max()}")
print(f"\nAperçu prix/m² médian par arrondissement :")
print(paris_silver.groupby('arrondissement')['prix_m2'].median().round(0).to_string())