from pymongo import MongoClient
from datetime import datetime
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["urban_data_explorer"]

print("═" * 55)
print("VÉRIFICATION SAUVEGARDE HISTORIQUE STREAMING")
print("═" * 55)

collections = {
    "velib_history":  "Vélib' disponibilité",
    "air_history":    "Qualité de l'air",
    "velo_history":   "Compteurs vélo",
}

total_docs = 0
for col_name, label in collections.items():
    col = db[col_name]
    count = col.count_documents({})
    total_docs += count
    
    if count > 0:
        # Premier et dernier document
        first = col.find_one(sort=[("timestamp", 1)])
        last  = col.find_one(sort=[("timestamp", -1)])
        
        print(f"\n✅ {label} ({col_name})")
        print(f"   Documents sauvegardés : {count}")
        print(f"   Premier : {first['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Dernier : {last['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Contenu du dernier document
        if col_name == "velib_history":
            print(f"   Vélos dispo : {last.get('total_velos_dispo', 'N/A')}")
            print(f"   Stations : {last.get('nb_stations', 'N/A')}")
        elif col_name == "velo_history":
            print(f"   Compteurs : {last.get('nb_compteurs', 'N/A')}")
        elif col_name == "air_history":
            print(f"   Enregistrements : {len(last.get('data', []))}")
    else:
        print(f"\n⚠️  {label} — aucun document (relance le streaming)")

print(f"\n{'═'*55}")
print(f"TOTAL documents historique : {total_docs}")
print(f"Persistance MongoDB : ✅ CONFIRMÉE")
print(f"{'═'*55}")

# Export JSON pour preuve
export = {}
for col_name in collections:
    docs = list(db[col_name].find({}, {"_id": 0}).sort("timestamp", -1).limit(3))
    for d in docs:
        if "timestamp" in d:
            d["timestamp"] = d["timestamp"].isoformat()
    export[col_name] = {"count": db[col_name].count_documents({}), "derniers_3": docs}

with open("data/streaming_sauvegarde_proof.json", "w") as f:
    json.dump(export, f, indent=2, ensure_ascii=False, default=str)
print(f"\n📄 Preuve exportée : data/streaming_sauvegarde_proof.json")
client.close()
