from pymongo import MongoClient, ASCENDING
from datetime import datetime
import pandas as pd
import geopandas as gpd
import json
import os

client = MongoClient("mongodb://localhost:27017/")
db = client["urban_data_explorer"]

print("✅ Connexion MongoDB OK")
print(f"   Base : urban_data_explorer")

# ════════════════════════════════════════════════════════════════════
# 1. DATA CATALOG — métadonnées de toutes les sources
# ════════════════════════════════════════════════════════════════════
print("\n── Data Catalog ──")
db.data_catalog.drop()

catalog = [
    {
        "id": "DS-01", "nom": "DVF Géolocalisées",
        "description": "Demandes de valeurs foncières — transactions immobilières géolocalisées",
        "producteur": "DGFiP / Etalab",
        "url": "https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees",
        "licence": "Licence Ouverte v2.0",
        "format": ["CSV.GZ"],
        "frequence_maj": "Semestrielle",
        "periode": "2021-2025",
        "nb_lignes": 165887,
        "indicateur": "obligatoire",
        "tags": ["immobilier", "prix", "transactions"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-02", "nom": "Encadrement des loyers Paris",
        "description": "Loyers de référence, majorés et minorés par quartier, type et époque",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/logement-encadrement-des-loyers/",
        "licence": "ODbL",
        "format": ["CSV", "API"],
        "frequence_maj": "Annuelle",
        "periode": "2019-2025",
        "nb_lignes": 17920,
        "indicateur": "obligatoire",
        "tags": ["loyers", "logement", "réglementation"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-03", "nom": "Logements sociaux financés Paris",
        "description": "Programmes de logements sociaux financés par arrondissement",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/logements-sociaux-finances-a-paris/",
        "licence": "ODbL",
        "format": ["CSV", "API"],
        "frequence_maj": "Annuelle",
        "periode": "2001-2024",
        "nb_lignes": 4174,
        "indicateur": "obligatoire",
        "tags": ["logement social", "HLM", "bailleur"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-04", "nom": "Filosofi INSEE — Revenus IRIS",
        "description": "Revenus, pauvreté et inégalités par zone IRIS",
        "producteur": "INSEE",
        "url": "https://www.insee.fr/fr/statistiques/8229323",
        "licence": "Licence Ouverte v2.0",
        "format": ["CSV"],
        "frequence_maj": "Annuelle",
        "periode": "2021",
        "nb_lignes": 864,
        "indicateur": "obligatoire",
        "tags": ["revenus", "pauvreté", "inégalités", "IRIS"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-05", "nom": "Contours arrondissements Paris",
        "description": "Polygones des 20 arrondissements parisiens en WGS84",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/arrondissements/",
        "licence": "ODbL",
        "format": ["GeoJSON"],
        "frequence_maj": "Stable",
        "nb_lignes": 20,
        "indicateur": "geo_reference",
        "tags": ["géographie", "arrondissements", "polygones"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IAU-1", "nom": "BPE — Base Permanente des Équipements",
        "description": "Équipements et services : commerces, santé, enseignement, loisirs",
        "producteur": "INSEE / data.iledefrance.fr",
        "url": "https://data.iledefrance.fr/explore/dataset/bpe23-nettoye/",
        "licence": "Licence Ouverte v2.0",
        "format": ["CSV"],
        "frequence_maj": "Annuelle",
        "nb_lignes": 126518,
        "indicateur": "IAU",
        "tags": ["équipements", "commerces", "services"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IAU-2", "nom": "Monuments historiques",
        "description": "Liste des immeubles protégés au titre des monuments historiques",
        "producteur": "Ministère de la Culture",
        "url": "https://data.culture.gouv.fr/explore/dataset/liste-des-immeubles-proteges-au-titre-des-monuments-historiques/",
        "licence": "Licence Ouverte v2.0",
        "format": ["CSV"],
        "nb_lignes": 1882,
        "indicateur": "IAU",
        "tags": ["patrimoine", "monuments", "culture"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IAU-3", "nom": "OSM Restaurants Paris",
        "description": "Restaurants, cafés, bars issus d'OpenStreetMap",
        "producteur": "OpenStreetMap / data.smartidf.services",
        "url": "https://data.smartidf.services/explore/dataset/osm-restaurant-fr/",
        "licence": "ODbL",
        "format": ["GeoJSON"],
        "nb_lignes": 16411,
        "indicateur": "IAU",
        "tags": ["restauration", "gastronomie", "OSM"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IST-1", "nom": "Criminalité — statistiques départementales",
        "description": "Taux de criminalité par indicateur et par département",
        "producteur": "Ministère de l'Intérieur",
        "url": "https://www.data.gouv.fr/datasets/bases-statistiques-communale-departementale-et-regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales",
        "licence": "Licence Ouverte v2.0",
        "format": ["CSV"],
        "nb_lignes": 180,
        "indicateur": "IST",
        "tags": ["criminalité", "sécurité", "délinquance"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IST-2", "nom": "Bruit routier Paris",
        "description": "Évolution de l'indice de bruit mesuré sur les stations parisiennes",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/bruit-evolution-de-l-indice-du-bruit-mesure-sur-des-stations-parisiennes/",
        "licence": "ODbL",
        "format": ["CSV"],
        "nb_lignes": 16,
        "indicateur": "IST",
        "tags": ["bruit", "environnement", "pollution sonore"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IST-3", "nom": "Qualité de l'air NO2/PM2.5",
        "description": "Exposition des Parisiens au NO2 et PM2.5 par arrondissement",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/qualite-de-l-air-exposition-des-parisen-ne-s-au-no2-et-pm2-5/",
        "licence": "ODbL",
        "format": ["CSV"],
        "nb_lignes": 10,
        "indicateur": "IST",
        "tags": ["air", "pollution", "santé environnementale"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IQV-1", "nom": "Espaces verts Paris",
        "description": "Polygones des espaces verts parisiens avec surface et type",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/espaces_verts/",
        "licence": "ODbL",
        "format": ["GeoJSON"],
        "nb_lignes": 2553,
        "indicateur": "IQV",
        "tags": ["espaces verts", "nature", "parcs"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IQV-2", "nom": "Arbres de Paris",
        "description": "Localisation et caractéristiques des arbres sur le domaine public",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/les-arbres/",
        "licence": "ODbL",
        "format": ["CSV"],
        "nb_lignes": 174822,
        "indicateur": "IQV",
        "tags": ["arbres", "végétation", "nature urbaine"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IQV-3", "nom": "Professionnels de santé IDF",
        "description": "Annuaire et localisation des professionnels de santé",
        "producteur": "data.gouv.fr",
        "url": "https://www.data.gouv.fr/datasets/annuaire-et-localisation-des-professionnels-de-sante-en-ile-de-france/",
        "licence": "Licence Ouverte v2.0",
        "format": ["CSV"],
        "nb_lignes": 95465,
        "indicateur": "IQV",
        "tags": ["santé", "médecins", "accessibilité"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IMM-1", "nom": "Stations RATP/RER IDF",
        "description": "Emplacement des gares et stations de transport en commun IDF",
        "producteur": "Île-de-France Mobilités",
        "url": "https://data.iledefrance-mobilites.fr/explore/dataset/emplacement-des-gares-idf/",
        "licence": "ODbL",
        "format": ["GeoJSON"],
        "nb_lignes": 436,
        "indicateur": "IMM",
        "tags": ["transport", "RATP", "métro", "RER"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IMM-2", "nom": "Vélib' stations",
        "description": "Disponibilité en temps réel des stations Vélib'",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/velib-disponibilite-en-temps-reel/",
        "licence": "ODbL",
        "format": ["GeoJSON", "API"],
        "nb_lignes": 994,
        "indicateur": "IMM",
        "tags": ["vélo", "Vélib", "mobilité douce"],
        "date_integration": datetime.now()
    },
    {
        "id": "DS-IMM-3", "nom": "Aménagements cyclables Paris",
        "description": "Pistes et bandes cyclables sur le territoire parisien",
        "producteur": "Ville de Paris",
        "url": "https://opendata.paris.fr/explore/dataset/amenagements-cyclables/",
        "licence": "ODbL",
        "format": ["GeoJSON"],
        "nb_lignes": 165085,
        "indicateur": "IMM",
        "tags": ["vélo", "pistes cyclables", "mobilité"],
        "date_integration": datetime.now()
    },
]

db.data_catalog.insert_many(catalog)
db.data_catalog.create_index("id", unique=True)
db.data_catalog.create_index("indicateur")
print(f"  ✅ {len(catalog)} sources cataloguées")

# ════════════════════════════════════════════════════════════════════
# 2. PROFILS ARRONDISSEMENTS — document JSON complet par arrondissement
# ════════════════════════════════════════════════════════════════════
print("\n── Profils arrondissements ──")
db.arrondissements_profiles.drop()

gold = pd.read_parquet("data/gold/gold_arrondissements.parquet")

profiles = []
for _, row in gold.iterrows():
    profile = {
        "arrondissement": int(row["arrondissement"]),
        "nom": row["nom_arrondissement"],
        "surface_km2": round(float(row["surface_km2"]), 2),
        "immobilier": {
            "prix_m2_median": round(float(row["prix_m2_median"]), 0),
            "evol_prix_2021_2024_pct": round(float(row.get("evol_prix_2021_2024_pct", 0)), 1),
            "loyer_ref_median": round(float(row["loyer_ref_median"]), 1),
            "loyer_max_median": round(float(row["loyer_max_median"]), 1),
            "nb_transactions": int(row["nb_transactions"]),
            "indice_pression_immo": round(float(row["indice_pression_immo"]), 2),
        },
        "social": {
            "revenu_median": round(float(row["revenu_median"]), 0),
            "taux_pauvrete": round(float(row["taux_pauvrete"]), 1),
            "indice_gini": round(float(row["indice_gini"]), 2),
            "nb_logements_sociaux": int(row["nb_logements_sociaux"]),
        },
        "scores": {
            "iau": round(float(row["score_iau"]), 1),
            "iqv": round(float(row["score_iqv"]), 1),
            "imm": round(float(row["score_imm"]), 1),
            "ist": round(float(row["score_ist"]), 1),
        },
        "attractivite": {
            "nb_commerces": int(row["nb_commerces"]),
            "nb_restos_bars": int(row["nb_restos_bars"]),
            "nb_scolaire": int(row["nb_scolaire"]),
            "nb_sante_bpe": int(row["nb_sante"]),
            "nb_monuments": int(row["nb_monuments"]),
        },
        "qualite_vie": {
            "surface_verte_m2": round(float(row["surface_verte_m2"]), 0),
            "nb_arbres": int(row["nb_arbres"]),
            "nb_espaces_verts": int(row["nb_espaces_verts"]),
            "nb_pros_sante": int(row["nb_pros_sante"]),
        },
        "mobilite": {
            "nb_stations_transport": int(row["nb_stations_transport"]),
            "nb_stations_velib": int(row["nb_stations_velib"]),
            "capacite_velib": int(row["capacite_velib"]),
            "nb_troncons_velo": int(row["nb_troncons_velo"]),
        },
        "date_maj": datetime.now()
    }
    profiles.append(profile)

db.arrondissements_profiles.insert_many(profiles)
db.arrondissements_profiles.create_index("arrondissement", unique=True)
print(f"  ✅ {len(profiles)} profils arrondissements créés")

# ════════════════════════════════════════════════════════════════════
# 3. RÉSUMÉ
# ════════════════════════════════════════════════════════════════════
print("\n── Collections MongoDB ──")
for col in db.list_collection_names():
    count = db[col].count_documents({})
    print(f"  {col:<35} {count} documents")

print("\n✅ MongoDB chargé !")
client.close()