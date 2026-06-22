cat > docs/DOCKER.md << 'EOF'
# Déploiement Docker

## Lancer tout le stack

```bash
docker-compose up -d
```

## Services démarrés
- **API** → http://localhost:8001/docs
- **PostgreSQL** → localhost:5433
- **MongoDB** → localhost:27018

## Commandes utiles

```bash
# Voir les logs
docker-compose logs -f api

# Status des conteneurs
docker-compose ps

# Arrêter
docker-compose down

# Reconstruire l'API après modif
docker-compose up -d --build api

# Entrer dans le conteneur API
docker exec -it ude_api bash

# Entrer dans PostgreSQL
docker exec -it ude_postgres psql -U ude_user -d urban_data_explorer
```

## Architecture conteneurs
- `ude_postgres` : PostgreSQL 17 + PostGIS 3.4
- `ude_mongodb` : MongoDB 8
- `ude_api` : FastAPI sur port 8001
- Données persistées dans volumes Docker
EOF