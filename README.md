# Urban Data Explorer 🏙

Explorer, comprendre et comparer les dynamiques du logement à Paris (2021-2025).

## Stack
- **Pipeline** : Python, pandas, geopandas (17 scripts)
- **BDD** : PostgreSQL 17 + PostGIS · MongoDB 8
- **API** : FastAPI + httpx (12 endpoints dont 3 temps réel)
- **Front** : React + Vite + MapLibre GL + Recharts

## Prérequis
- Python 3.11+
- Node 18+
- PostgreSQL 17 + PostGIS 3.6
- MongoDB 8

## Installation rapide

### 1. Cloner
```bash
git clone https://github.com/TON_USERNAME/urban-data-explorer.git
cd urban-data-explorer
```

### 2. Python
```bash
pip install -r requirements.txt
```

### 3. Bases de données
```bash
brew services start postgresql@17
brew services start mongodb-community
createdb urban_data_explorer
psql urban_data_explorer -c "CREATE EXTENSION postgis;"
```

### 4. Télécharger les données
Voir [docs/DATASETS.md](docs/DATASETS.md) pour les 18 liens de téléchargement.
Placer tous les fichiers dans `data/raw/`.

### 5. Pipeline (ordre obligatoire)
```bash
python3 pipeline/02_bronze_to_silver_dvf.py
python3 pipeline/04_bronze_to_silver_loyers_sociaux.py
python3 pipeline/07_bronze_to_silver_filosofi_clean.py
python3 pipeline/09_bronze_to_silver_geo.py
python3 pipeline/10_bronze_to_silver_iau.py
python3 pipeline/12_bronze_to_silver_ist.py
python3 pipeline/13_bronze_to_silver_iqv_imm.py
python3 pipeline/14_gold_arrondissements.py
python3 pipeline/15_load_to_postgres.py
python3 pipeline/16_load_to_mongodb.py
python3 pipeline/17_load_iris_postgres.py
python3 pipeline/18_gold_iris.py
```

### 6. API
```bash
cd Api
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs
```

### 7. Frontend
```bash
cd front
npm install
npm run dev
# → http://localhost:5173
```

## Structure

├── pipeline/        # Scripts Python Bronze→Silver→Gold
├── Api/             # FastAPI (main.py)
├── front/           # React + MapLibre
│   └── src/
│       └── components/   # Map, Sidebar, Header, ComparePanel
├── data/
│   ├── raw/         # Données brutes (non versionné — voir DATASETS.md)
│   ├── silver/      # Données nettoyées (non versionné)
│   └── gold/        # Agrégats finaux (non versionné)
├── docs/
│   └── DATASETS.md  # Liens et instructions téléchargement
└── requirements.txt

## Fonctionnalités
- Carte choroplèthe interactive avec 9 indicateurs
- Granularité IRIS (992 zones) avec prix médian au survol
- Mode comparaison côte-à-côte de 2 arrondissements (radar chart)
- Évolution temporelle des prix 2021-2025
- 3 endpoints temps réel : Vélib', qualité air, compteurs vélo