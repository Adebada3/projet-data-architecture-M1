import time
import httpx
import asyncio
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["urban_data_explorer"]

# Collections pour l'historique temps réel
db.velib_history.create_index("timestamp")
db.air_history.create_index("timestamp")
db.velo_history.create_index("timestamp")

print("═" * 55)
print("MICRO-BATCH STREAMING — Urban Data Explorer")
print("═" * 55)
print("Collecte : Vélib' (60s) · Air (300s) · Vélo (120s)")
print("Stockage : MongoDB collections historiques")
print("Ctrl+C pour arrêter\n")

VELIB_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=100"
AIR_URL   = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/qualite-de-l-air-exposition-des-parisen-ne-s-au-no2-et-pm2-5/records?limit=5"
VELO_URL  = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-donnees-compteurs/records?limit=50&order_by=date%20DESC"

last_velib = 0
last_air   = 0
last_velo  = 0
batch_num  = 0

async def collect_velib():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(VELIB_URL)
        data = r.json()
    stations = data.get("results", [])
    total_velos = sum(s.get("numbikesavailable", 0) for s in stations)
    total_elec  = sum(s.get("ebike", 0) for s in stations)
    doc = {
        "timestamp": datetime.now(),
        "nb_stations": len(stations),
        "total_velos_dispo": total_velos,
        "total_electriques": total_elec,
        "snapshot": [{
            "id": s.get("stationcode"),
            "nom": s.get("name"),
            "velos": s.get("numbikesavailable", 0),
            "places": s.get("numdocksavailable", 0),
        } for s in stations[:20]]  # on garde les 20 premières stations
    }
    db.velib_history.insert_one(doc)
    return len(stations), total_velos

async def collect_air():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(AIR_URL)
        data = r.json()
    results = data.get("results", [])
    doc = {
        "timestamp": datetime.now(),
        "data": results
    }
    db.air_history.insert_one(doc)
    return len(results)

async def collect_velo():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(VELO_URL)
        data = r.json()
    results = data.get("results", [])
    total = sum(r2.get("comptage_horaire", 0) or 0 for r2 in results)
    doc = {
        "timestamp": datetime.now(),
        "nb_compteurs": len(results),
        "total_passages": total,
        "data": results[:20]
    }
    db.velo_history.insert_one(doc)
    return len(results), total

async def main():
    global last_velib, last_air, last_velo, batch_num

    while True:
        now = time.time()
        batch_num += 1
        print(f"\n[Batch #{batch_num}] {datetime.now().strftime('%H:%M:%S')}")

        # Vélib' toutes les 60 secondes
        if now - last_velib >= 60:
            try:
                nb, total = await collect_velib()
                last_velib = now
                count = db.velib_history.count_documents({})
                print(f"  🚲 Vélib' : {nb} stations · {total} vélos dispo · {count} docs MongoDB")
            except Exception as e:
                print(f"  ⚠️  Vélib' erreur : {e}")

        # Qualité air toutes les 5 minutes
        if now - last_air >= 300:
            try:
                nb = await collect_air()
                last_air = now
                count = db.air_history.count_documents({})
                print(f"  💨 Air : {nb} enregistrements · {count} docs MongoDB")
            except Exception as e:
                print(f"  ⚠️  Air erreur : {e}")

        # Compteurs vélo toutes les 2 minutes
        if now - last_velo >= 120:
            try:
                nb, total = await collect_velo()
                last_velo = now
                count = db.velo_history.count_documents({})
                print(f"  🔢 Vélo compteurs : {nb} capteurs · {total} passages · {count} docs MongoDB")
            except Exception as e:
                print(f"  ⚠️  Vélo erreur : {e}")

        await asyncio.sleep(15)  # vérifie toutes les 15 secondes

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        total_velib = db.velib_history.count_documents({})
        total_air   = db.air_history.count_documents({})
        total_velo  = db.velo_history.count_documents({})
        print(f"\n\nCollecte arrêtée après {batch_num} batches")
        print(f"Documents MongoDB stockés :")
        print(f"  velib_history  : {total_velib}")
        print(f"  air_history    : {total_air}")
        print(f"  velo_history   : {total_velo}")
        client.close()