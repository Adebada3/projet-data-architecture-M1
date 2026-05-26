from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import json
import httpx

DB_URL = "postgresql://cherylecheryle@localhost:5432/urban_data_explorer"
engine = create_engine(DB_URL)

app = FastAPI(title="Urban Data Explorer API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helpers ────────────────────────────────────────────────────────
def query(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        cols = result.keys()
        return [dict(zip(cols, row)) for row in result]

# ══════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"message": "Urban Data Explorer API", "version": "1.0", "status": "ok"}

# ── Arrondissements ────────────────────────────────────────────────
@app.get("/api/arrondissements")
def get_arrondissements():
    """Tous les arrondissements avec leurs KPIs Gold"""
    rows = query("""
        SELECT arrondissement, nom_arrondissement,
               prix_m2_median, evol_prix_2021_2024_pct,
               loyer_ref_median, nb_logements_sociaux,
               revenu_median, taux_pauvrete,
               score_iau, score_iqv, score_imm, score_ist,
               indice_pression_immo, surface_km2
        FROM gold_arrondissements
        ORDER BY arrondissement
    """)
    return {"count": len(rows), "data": rows}

@app.get("/api/arrondissements/{arr_id}")
def get_arrondissement(arr_id: int):
    """Détail complet d'un arrondissement"""
    rows = query("""
        SELECT * FROM gold_arrondissements
        WHERE arrondissement = :arr
    """, {"arr": arr_id})
    if not rows:
        return {"error": f"Arrondissement {arr_id} non trouvé"}
    return rows[0]

# ── GeoJSON carte ──────────────────────────────────────────────────
@app.get("/api/arrondissements/geo/choropleth")
def get_choropleth(
    indicateur: str = Query("prix_m2_median",
        description="prix_m2_median | score_iau | score_iqv | score_imm | score_ist | taux_pauvrete | revenu_median")
):
    """GeoJSON pour carte choroplèthe — joint géométrie + indicateur"""
    allowed = {
        "prix_m2_median", "score_iau", "score_iqv",
        "score_imm", "score_ist", "taux_pauvrete",
        "revenu_median", "nb_logements_sociaux",
        "loyer_ref_median", "indice_pression_immo"
    }
    if indicateur not in allowed:
        return {"error": f"Indicateur non autorisé. Valeurs: {allowed}"}

    rows = query(f"""
        SELECT g.arrondissement, g.nom_arrondissement,
               k.{indicateur},
               ST_AsGeoJSON(g.geometry)::json as geometry
        FROM geo_arrondissements g
        JOIN gold_arrondissements k USING (arrondissement)
        ORDER BY g.arrondissement
    """)
    features = [{
        "type": "Feature",
        "properties": {
            "arrondissement": r["arrondissement"],
            "nom": r["nom_arrondissement"],
            indicateur: r[indicateur],
        },
        "geometry": r["geometry"]
    } for r in rows]
    return {"type": "FeatureCollection", "features": features}

# ── Prix DVF ───────────────────────────────────────────────────────
@app.get("/api/prix")
def get_prix(
    arrondissement: int = Query(None),
    annee: int = Query(None),
    type_local: str = Query(None)
):
    """Prix au m² — filtrable par arrondissement, année, type"""
    conditions = []
    params = {}
    if arrondissement:
        conditions.append("arrondissement = :arr")
        params["arr"] = arrondissement
    if annee:
        conditions.append("annee = :annee")
        params["annee"] = annee
    if type_local:
        conditions.append("type_local = :type_local")
        params["type_local"] = type_local

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = query(f"""
        SELECT arrondissement, annee, type_local,
               ROUND(AVG(prix_m2)::numeric, 0) as prix_m2_moyen,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::numeric, 0) as prix_m2_median,
               COUNT(*) as nb_transactions
        FROM dvf_transactions
        {where}
        GROUP BY arrondissement, annee, type_local
        ORDER BY arrondissement, annee
    """, params)
    return {"count": len(rows), "data": rows}

@app.get("/api/prix/evolution")
def get_prix_evolution(arrondissement: int = Query(None)):
    """Evolution du prix médian par année"""
    where = "WHERE arrondissement = :arr" if arrondissement else ""
    params = {"arr": arrondissement} if arrondissement else {}
    rows = query(f"""
        SELECT annee,
               arrondissement,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::numeric, 0) as prix_m2_median,
               COUNT(*) as nb_transactions
        FROM dvf_transactions
        {where}
        GROUP BY annee, arrondissement
        ORDER BY arrondissement, annee
    """, params)
    return {"count": len(rows), "data": rows}

# ── Loyers ─────────────────────────────────────────────────────────
@app.get("/api/loyers")
def get_loyers(
    arrondissement: int = Query(None),
    annee: int = Query(None),
    type_location: str = Query(None)
):
    """Loyers de référence"""
    conditions = []
    params = {}
    if arrondissement:
        conditions.append("arrondissement = :arr")
        params["arr"] = arrondissement
    if annee:
        conditions.append("annee = :annee")
        params["annee"] = annee
    if type_location:
        conditions.append("type_location = :type_location")
        params["type_location"] = type_location
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = query(f"""
        SELECT arrondissement, annee, type_location,
               nb_pieces, epoque,
               ROUND(AVG(loyer_ref)::numeric, 2) as loyer_ref_moyen,
               ROUND(AVG(loyer_max)::numeric, 2) as loyer_max_moyen,
               ROUND(AVG(loyer_min)::numeric, 2) as loyer_min_moyen
        FROM loyers_reference
        {where}
        GROUP BY arrondissement, annee, type_location, nb_pieces, epoque
        ORDER BY arrondissement, annee
    """, params)
    return {"count": len(rows), "data": rows}

# ── Comparaison ────────────────────────────────────────────────────
@app.get("/api/compare")
def compare(arr1: int = Query(...), arr2: int = Query(...)):
    """Compare deux arrondissements côte à côte"""
    rows = query("""
        SELECT arrondissement, nom_arrondissement,
               prix_m2_median, loyer_ref_median,
               revenu_median, taux_pauvrete,
               nb_logements_sociaux, indice_pression_immo,
               score_iau, score_iqv, score_imm, score_ist,
               nb_commerces, nb_restos_bars, nb_monuments,
               surface_verte_m2, nb_arbres, nb_pros_sante,
               nb_stations_transport, capacite_velib
        FROM gold_arrondissements
        WHERE arrondissement IN (:a1, :a2)
        ORDER BY arrondissement
    """, {"a1": arr1, "a2": arr2})
    if len(rows) < 2:
        return {"error": "Un ou deux arrondissements non trouvés"}
    return {
        "arrondissement_1": rows[0],
        "arrondissement_2": rows[1],
        "differences": {
            k: round(rows[1][k] - rows[0][k], 1)
            for k in rows[0]
            if isinstance(rows[0][k], (int, float)) and rows[0][k] is not None
        }
    }

# ── Indicateurs créatifs ───────────────────────────────────────────
@app.get("/api/indicateurs")
def get_indicateurs():
    """Scores IAU / IST / IQV / IMM pour tous les arrondissements"""
    rows = query("""
        SELECT arrondissement, nom_arrondissement,
               score_iau, score_iqv, score_imm, score_ist,
               nb_commerces, nb_restos_bars, nb_scolaire,
               nb_sante, nb_monuments,
               surface_verte_m2, nb_arbres, nb_pros_sante,
               nb_stations_transport, capacite_velib, nb_troncons_velo
        FROM gold_arrondissements
        ORDER BY arrondissement
    """)
    return {"count": len(rows), "data": rows}

@app.get("/api/iris/geo")
def get_iris_geo(arrondissement: int = Query(None)):
    """GeoJSON des zones IRIS — optionnellement filtré par arrondissement"""
    where = "WHERE LEFT(\"CODE_IRIS\", 5) = :code" if arrondissement else ""
    params = {"code": f"751{arrondissement:02d}"} if arrondissement else {}
    rows = query(f"""
        SELECT "CODE_IRIS", "NOM_IRIS", "INSEE_COM",
               ST_AsGeoJSON(geometry)::json as geometry
        FROM geo_iris
        {where}
    """, params)
    features = [{
        "type": "Feature",
        "properties": {
            "code_iris": r["CODE_IRIS"],
            "nom_iris": r["NOM_IRIS"],
            "insee_com": r["INSEE_COM"],
        },
        "geometry": r["geometry"]
    } for r in rows]
    return {"type": "FeatureCollection", "features": features}



@app.get("/api/realtime/velib")
async def get_velib_realtime():
    """Disponibilité Vélib' en temps réel"""
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=100"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        data = r.json()
    stations = []
    for record in data.get("results", []):
        stations.append({
            "id": record.get("stationcode"),
            "nom": record.get("name"),
            "velos_dispo": record.get("numbikesavailable", 0),
            "places_dispo": record.get("numdocksavailable", 0),
            "capacite": record.get("capacity", 0),
            "mecanique": record.get("mechanical", 0),
            "electrique": record.get("ebike", 0),
            "coordonnees": record.get("coordonnees_geo"),
            "arrondissement": record.get("nom_arrondissement_communes"),
        })
    return {
        "source": "Paris Open Data — temps réel",
        "nb_stations": len(stations),
        "data": stations
    }

@app.get("/api/realtime/air")
async def get_air_realtime():
    """Qualité de l'air Paris — dernières mesures"""
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/qualite-de-l-air-exposition-des-parisen-ne-s-au-no2-et-pm2-5/records?limit=10&order_by=Année%20DESC"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        data = r.json()
    return {
        "source": "Paris Open Data",
        "data": data.get("results", [])
    }

@app.get("/api/realtime/velo-compteurs")
async def get_velo_compteurs():
    """Comptages vélo en temps réel — dernières 24h"""
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-donnees-compteurs/records?limit=50&order_by=date%20DESC"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        data = r.json()
    compteurs = []
    for r2 in data.get("results", []):
        compteurs.append({
            "id_compteur": r2.get("id_compteur"),
            "nom_compteur": r2.get("nom_compteur"),
            "date": r2.get("date"),
            "comptage_horaire": r2.get("comptage_horaire"),
            "coordonnees": r2.get("coordonnees_geo"),
        })
    return {
        "source": "Paris Open Data — temps réel",
        "nb_compteurs": len(compteurs),
        "data": compteurs
    }
    
    
@app.get("/api/iris/choropleth")
def get_iris_choropleth():
    """GeoJSON IRIS coloré par prix au m² — pour zoom détail"""
    rows = query("""
        SELECT code_iris, nom_iris, insee_com,
               prix_m2_median, nb_transactions,
               surface_median,
               ST_AsGeoJSON(geometry)::json as geometry
        FROM gold_iris
        WHERE prix_m2_median IS NOT NULL
    """)
    features = [{
        "type": "Feature",
        "properties": {
            "code_iris": r["code_iris"],
            "nom_iris": r["nom_iris"],
            "prix_m2_median": r["prix_m2_median"],
            "nb_transactions": r["nb_transactions"],
            "surface_median": r["surface_median"],
        },
        "geometry": r["geometry"]
    } for r in rows]
    return {"type": "FeatureCollection", "features": features}