cat > README.md << 'EOF'
# Urban Data Explorer 🏙

Explorer, comprendre et comparer les dynamiques du logement à Paris (2021-2025).

## Stack
- **Pipeline** : Python, pandas, geopandas
- **BDD** : PostgreSQL 17 + PostGIS · MongoDB 8
- **API** : FastAPI
- **Front** : React + Vite + MapLibre GL

## Prérequis
- Python 3.11+
- Node 18+
- PostgreSQL 17 + PostGIS
- MongoDB 8

## Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/TON_USERNAME/urban-data-explorer.git
cd urban-data-explorer
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Démarrer PostgreSQL et MongoDB
```bash
brew services start postgresql@17
brew services start mongodb-community
```

### 4. Créer la base PostgreSQL
```bash
createdb urban_data_explorer
psql urban_data_explorer -c "CREATE EXTENSION postgis;"
```

### 5. Télécharger les données
Voir `docs/DATASETS.md` pour tous les liens de téléchargement.
Placer les fichiers dans `data/raw/`.

### 6. Exécuter le pipeline
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

### 7. Lancer l'API
```bash
cd Api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
API disponible sur http://localhost:8000/docs

### 8. Lancer le front
```bash
cd front
npm install
npm run dev
```
Application disponible sur http://localhost:5173

## Structure

├── pipeline/        # Scripts Python Bronze→Silver→Gold
├── Api/             # FastAPI
├── front/           # React + MapLibre
├── data/
│   ├── raw/         # Données brutes (non versionné)
│   ├── silver/      # Données nettoyées (non versionné)
│   └── gold/        # Agrégats (non versionné)
└── docs/            # Documentation

EOF