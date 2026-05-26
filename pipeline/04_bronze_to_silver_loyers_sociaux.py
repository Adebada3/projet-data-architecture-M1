import pandas as pd
import os

os.makedirs("data/silver", exist_ok=True)

# ════════════════════════════════════════════════════════════════════
# LOYERS DE RÉFÉRENCE
# ════════════════════════════════════════════════════════════════════
print("── Loyers de référence ──")
loyers = pd.read_csv("data/raw/logement-encadrement-des-loyers.csv", sep=";", low_memory=False)

# Nettoyage colonnes
loyers = loyers.rename(columns={
    'Année':                        'annee',
    'Numéro du quartier':           'id_quartier',
    'Nom du quartier':              'nom_quartier',
    'Secteurs géographiques':       'secteur',
    'Nombre de pièces principales': 'nb_pieces',
    'Epoque de construction':       'epoque',
    'Type de location':             'type_location',
    'Loyers de référence':          'loyer_ref',
    'Loyers de référence majorés':  'loyer_max',
    'Loyers de référence minorés':  'loyer_min',
    'Numéro INSEE du quartier':     'code_quartier_insee',
})

# Extraire arrondissement depuis le code quartier INSEE (75XXY → arr = XX)
# code_quartier_insee format : 751XX où XX = arrondissement sur 2 chiffres
loyers['arrondissement'] = loyers['code_quartier_insee'].astype(str).str[3:5].astype(int)

# Séparer lat/lon
loyers[['latitude', 'longitude']] = loyers['geo_point_2d'].str.split(',', expand=True).astype(float)

cols = ['annee', 'arrondissement', 'id_quartier', 'nom_quartier',
        'secteur', 'nb_pieces', 'epoque', 'type_location',
        'loyer_ref', 'loyer_max', 'loyer_min',
        'code_quartier_insee', 'latitude', 'longitude']

loyers_silver = loyers[cols].dropna(subset=['loyer_ref'])
loyers_silver.to_parquet("data/silver/loyers_paris_silver.parquet", index=False)

print(f"  ✅ {len(loyers_silver):,} lignes sauvegardées")
print(f"  Années : {sorted(loyers_silver['annee'].unique())}")
print(f"  Loyer médian ref (toutes configs) : {loyers_silver['loyer_ref'].median():.1f} €/m²")
print(f"  Aperçu par arrondissement (loyer_ref médian) :")
print(loyers_silver.groupby('arrondissement')['loyer_ref'].median().round(1).to_string())


# ════════════════════════════════════════════════════════════════════
# LOGEMENTS SOCIAUX
# ════════════════════════════════════════════════════════════════════
print("\n── Logements sociaux ──")
social = pd.read_csv("data/raw/logements-sociaux-finances-a-paris.csv", sep=";", low_memory=False)

social = social.rename(columns={
    'Identifiant livraison':                 'id_livraison',
    'Adresse du programme':                  'adresse',
    'Code postal':                           'code_postal',
    'Année du financement - agrément':       'annee',
    'Bailleur social':                       'bailleur',
    'Nombre total de logements financés':    'nb_logements',
    'Dont nombre de logements PLA I':        'nb_plai',
    'Dont nombre de logements PLUS':         'nb_plus',
    'Dont nombre de logements PLUS CD':      'nb_plus_cd',
    'Dont nombre de logements PLS':          'nb_pls',
    'Mode de réalisation':                   'mode_realisation',
    'Arrondissement':                        'arrondissement',
    'Nature de programme':                   'nature_programme',
})

# Nettoyage arrondissement (peut être "Paris 11e" ou juste "11")
social['arrondissement'] = (
    social['arrondissement']
    .astype(str)
    .str.extract(r'(\d+)')
    .astype(float)
    .astype('Int64')
)

# Séparer lat/lon
social[['latitude', 'longitude']] = social['geo_point_2d'].str.split(',', expand=True).astype(float)

# Colonnes utiles
cols_s = ['id_livraison', 'annee', 'arrondissement', 'adresse', 'code_postal',
          'bailleur', 'nb_logements', 'nb_plai', 'nb_plus', 'nb_plus_cd', 'nb_pls',
          'mode_realisation', 'nature_programme', 'latitude', 'longitude']

social_silver = social[cols_s].dropna(subset=['annee', 'arrondissement'])
social_silver.to_parquet("data/silver/logements_sociaux_silver.parquet", index=False)

print(f"  ✅ {len(social_silver):,} programmes sauvegardés")
print(f"  Période : {social_silver['annee'].min():.0f} – {social_silver['annee'].max():.0f}")
print(f"  Total logements sociaux financés : {social_silver['nb_logements'].sum():,.0f}")
print(f"  Répartition par arrondissement :")
print(social_silver.groupby('arrondissement')['nb_logements'].sum().sort_values(ascending=False).head(10).to_string())