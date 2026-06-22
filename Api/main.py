from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from typing import Optional
import httpx
import jwt
import time

# ── Config ─────────────────────────────────────────────────────────
DB_URL = "postgresql://cherylecheryle@localhost:5432/urban_data_explorer"
SECRET_KEY = "urban_data_explorer_secret_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

engine = create_engine(DB_URL, pool_size=10, max_overflow=20)
security = HTTPBearer(auto_error=False)

app = FastAPI(
    title="Urban Data Explorer API",
    version="2.0",
    description="API REST pour explorer les dynamiques urbaines de Paris — 2021-2025"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cache TTL ──────────────────────────────────────────────────────
_cache = {}

def get_cache(key: str):
    if key in _cache:
        data, ts, ttl = _cache[key]
        if time.time() - ts < ttl:
            return data
    return None

def set_cache(key: str, data, ttl: int = 300):
    _cache[key] = (data, time.time(), ttl)

# ── JWT Auth ───────────────────────────────────────────────────────
USERS = {
    "admin": "urban2026",
    "demo":  "demo1234",
}

def create_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": username, "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM
    )

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token manquant")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# ── Helper DB ──────────────────────────────────────────────────────
def query(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        cols = result.keys()
        return [dict(zip(cols, row)) for row in result]

# ══════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════

@app.post("/auth/login")
def login(username: str, password: str):
    """Obtenir un token JWT"""
    if username not in USERS or USERS[username] != password:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = create_token(username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "username": username
    }

@app.get("/auth/me")
def me(username: str = Depends(verify_token)):
    """Infos utilisateur connecté"""
    return {"username": username, "role": "admin" if username == "admin" else "viewer"}

# ══════════════════════════════════════════════════════════════════
# ROUTES PUBLIQUES
# ══════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "message": "Urban Data Explorer API",
        "version": "2.0",
        "status": "ok",
        "docs": "/docs",
        "endpoints": 12
    }

@app.get("/api/arrondissements")
def get_arrondissements():
    cached = get_cache("arrondissements")
    if cached: return cached
    rows = query("""
        SELECT arrondissement, nom_arrondissement,
               prix_m2_median, evol_prix_2021_2024_pct,
               loyer_ref_median, nb_logements_sociaux,
               revenu_median, taux_pauvrete,
               score_iau, score_iqv, score_imm, score_ist,
               surface_km2
        FROM gold_arrondissements ORDER BY arrondissement
    """)
    result = {"count": len(rows), "data": rows, "cached": False}
    set_cache("arrondissements", {**result, "cached": True}, ttl=600)
    return result

@app.get("/api/arrondissements/{arr_id}")
def get_arrondissement(arr_id: int):
    cache_key = f"arr_{arr_id}"
    cached = get_cache(cache_key)
    if cached: return cached
    rows = query("SELECT * FROM gold_arrondissements WHERE arrondissement = :arr", {"arr": arr_id})
    if not rows:
        raise HTTPException(status_code=404, detail=f"Arrondissement {arr_id} non trouvé")
    set_cache(cache_key, rows[0], ttl=600)
    return rows[0]

@app.get("/api/arrondissements/geo/choropleth")
def get_choropleth(indicateur: str = Query("prix_m2_median")):
    allowed = {
        "prix_m2_median","score_iau","score_iqv","score_imm","score_ist",
        "taux_pauvrete","revenu_median","nb_logements_sociaux","loyer_ref_median"
    }
    if indicateur not in allowed:
        raise HTTPException(status_code=400, detail=f"Indicateur non autorisé")
    cache_key = f"choropleth_{indicateur}"
    cached = get_cache(cache_key)
    if cached: return cached
    rows = query(f"""
        SELECT g.arrondissement, g.nom_arrondissement,
               k.{indicateur},
               ST_AsGeoJSON(g.geometry)::json as geometry
        FROM geo_arrondissements g
        JOIN gold_arrondissements k USING (arrondissement)
        ORDER BY g.arrondissement
    """)
    features = [{"type":"Feature","properties":{"arrondissement":r["arrondissement"],
        "nom":r["nom_arrondissement"], indicateur:r[indicateur]},
        "geometry":r["geometry"]} for r in rows]
    result = {"type":"FeatureCollection","features":features}
    set_cache(cache_key, result, ttl=600)
    return result

@app.get("/api/prix")
def get_prix(arrondissement: int = Query(None), annee: int = Query(None),
             type_local: str = Query(None)):
    conditions, params = [], {}
    if arrondissement: conditions.append("arrondissement = :arr"); params["arr"] = arrondissement
    if annee: conditions.append("annee = :annee"); params["annee"] = annee
    if type_local: conditions.append("type_local = :type_local"); params["type_local"] = type_local
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = query(f"""
        SELECT arrondissement, annee, type_local,
               ROUND(AVG(prix_m2)::numeric,0) as prix_m2_moyen,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::numeric,0) as prix_m2_median,
               COUNT(*) as nb_transactions
        FROM dvf_transactions {where}
        GROUP BY arrondissement, annee, type_local
        ORDER BY arrondissement, annee
    """, params)
    return {"count": len(rows), "data": rows}

@app.get("/api/prix/evolution")
def get_prix_evolution(arrondissement: int = Query(None)):
    cache_key = f"prix_evol_{arrondissement or 'all'}"
    cached = get_cache(cache_key)
    if cached: return cached
    where = "WHERE arrondissement = :arr" if arrondissement else ""
    params = {"arr": arrondissement} if arrondissement else {}
    rows = query(f"""
        SELECT annee, arrondissement,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::numeric,0) as prix_m2_median,
               COUNT(*) as nb_transactions
        FROM dvf_transactions {where}
        GROUP BY annee, arrondissement ORDER BY arrondissement, annee
    """, params)
    result = {"count": len(rows), "data": rows}
    set_cache(cache_key, result, ttl=600)
    return result

@app.get("/api/loyers")
def get_loyers(arrondissement: int = Query(None), annee: int = Query(None),
               type_location: str = Query(None)):
    conditions, params = [], {}
    if arrondissement: conditions.append("arrondissement = :arr"); params["arr"] = arrondissement
    if annee: conditions.append("annee = :annee"); params["annee"] = annee
    if type_location: conditions.append("type_location = :type_location"); params["type_location"] = type_location
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = query(f"""
        SELECT arrondissement, annee, type_location, nb_pieces, epoque,
               ROUND(AVG(loyer_ref)::numeric,2) as loyer_ref_moyen,
               ROUND(AVG(loyer_max)::numeric,2) as loyer_max_moyen,
               ROUND(AVG(loyer_min)::numeric,2) as loyer_min_moyen
        FROM loyers_reference {where}
        GROUP BY arrondissement, annee, type_location, nb_pieces, epoque
        ORDER BY arrondissement, annee
    """, params)
    return {"count": len(rows), "data": rows}

@app.get("/api/compare")
def compare(arr1: int = Query(...), arr2: int = Query(...)):
    cache_key = f"compare_{min(arr1,arr2)}_{max(arr1,arr2)}"
    cached = get_cache(cache_key)
    if cached: return cached
    rows = query("""
        SELECT arrondissement, nom_arrondissement,
               prix_m2_median, loyer_ref_median, revenu_median, taux_pauvrete,
               nb_logements_sociaux, score_iau, score_iqv, score_imm, score_ist,
               nb_commerces, nb_restos_bars, nb_monuments,
               surface_verte_m2, nb_arbres, nb_pros_sante,
               nb_stations_transport, capacite_velib
        FROM gold_arrondissements
        WHERE arrondissement IN (:a1, :a2) ORDER BY arrondissement
    """, {"a1": arr1, "a2": arr2})
    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="Arrondissements non trouvés")
    result = {
        "arrondissement_1": rows[0],
        "arrondissement_2": rows[1],
        "differences": {k: round(rows[1][k]-rows[0][k],1)
            for k in rows[0] if isinstance(rows[0][k],(int,float)) and rows[0][k] is not None}
    }
    set_cache(cache_key, result, ttl=600)
    return result

@app.get("/api/indicateurs")
def get_indicateurs():
    cached = get_cache("indicateurs")
    if cached: return cached
    rows = query("""
        SELECT arrondissement, nom_arrondissement,
               score_iau, score_iqv, score_imm, score_ist,
               nb_commerces, nb_restos_bars, nb_scolaire, nb_sante, nb_monuments,
               surface_verte_m2, nb_arbres, nb_pros_sante,
               nb_stations_transport, capacite_velib, nb_troncons_velo
        FROM gold_arrondissements ORDER BY arrondissement
    """)
    result = {"count": len(rows), "data": rows}
    set_cache("indicateurs", result, ttl=600)
    return result

@app.get("/api/iris/geo")
def get_iris_geo(arrondissement: int = Query(None)):
    cache_key = f"iris_geo_{arrondissement or 'all'}"
    cached = get_cache(cache_key)
    if cached: return cached
    where = "WHERE LEFT(\"CODE_IRIS\", 5) = :code" if arrondissement else ""
    params = {"code": f"751{arrondissement:02d}"} if arrondissement else {}
    rows = query(f"""
        SELECT "CODE_IRIS", "NOM_IRIS", "INSEE_COM",
               ST_AsGeoJSON(geometry)::json as geometry
        FROM geo_iris {where}
    """, params)
    features = [{"type":"Feature","properties":{
        "code_iris":r["CODE_IRIS"],"nom_iris":r["NOM_IRIS"],"insee_com":r["INSEE_COM"]},
        "geometry":r["geometry"]} for r in rows]
    result = {"type":"FeatureCollection","features":features}
    set_cache(cache_key, result, ttl=3600)
    return result

@app.get("/api/iris/choropleth")
def get_iris_choropleth():
    cached = get_cache("iris_choropleth")
    if cached: return cached
    rows = query("""
        SELECT code_iris, nom_iris, insee_com,
               prix_m2_median, nb_transactions, surface_median,
               ST_AsGeoJSON(geometry)::json as geometry
        FROM gold_iris WHERE prix_m2_median IS NOT NULL
    """)
    features = [{"type":"Feature","properties":{
        "code_iris":r["code_iris"],"nom_iris":r["nom_iris"],
        "prix_m2_median":r["prix_m2_median"],"nb_transactions":r["nb_transactions"],
        "surface_median":r["surface_median"]},
        "geometry":r["geometry"]} for r in rows]
    result = {"type":"FeatureCollection","features":features}
    set_cache("iris_choropleth", result, ttl=3600)
    return result

# ══════════════════════════════════════════════════════════════════
# ROUTES PROTÉGÉES (JWT requis)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/admin/cache/stats")
def cache_stats(username: str = Depends(verify_token)):
    """Stats du cache — réservé admin"""
    stats = {}
    for key, (data, ts, ttl) in _cache.items():
        age = time.time() - ts
        stats[key] = {
            "age_seconds": round(age, 0),
            "ttl_seconds": ttl,
            "expires_in": round(ttl - age, 0),
            "valid": age < ttl
        }
    return {"cache_entries": len(_cache), "details": stats}

@app.delete("/api/admin/cache/clear")
def cache_clear(username: str = Depends(verify_token)):
    """Vider le cache — réservé admin"""
    count = len(_cache)
    _cache.clear()
    return {"message": f"{count} entrées supprimées", "username": username}

@app.get("/api/admin/stats")
def admin_stats(username: str = Depends(verify_token)):
    """Statistiques complètes de la base — réservé admin"""
    stats = query("""
        SELECT tablename,
               pg_size_pretty(pg_total_relation_size(tablename::regclass)) as taille
        FROM pg_tables WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(tablename::regclass) DESC
    """)
    return {"username": username, "tables": stats, "timestamp": datetime.now().isoformat()}

# ══════════════════════════════════════════════════════════════════
# REALTIME — avec cache TTL court
# ══════════════════════════════════════════════════════════════════

@app.get("/api/realtime/velib")
async def get_velib_realtime():
    cached = get_cache("velib_rt")
    if cached:
        return {**cached, "from_cache": True}
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=100"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        data = r.json()
    stations = [{"id": rec.get("stationcode"), "nom": rec.get("name"),
        "velos_dispo": rec.get("numbikesavailable",0),
        "places_dispo": rec.get("numdocksavailable",0),
        "capacite": rec.get("capacity",0),
        "mecanique": rec.get("mechanical",0),
        "electrique": rec.get("ebike",0),
        "coordonnees": rec.get("coordonnees_geo"),
        "arrondissement": rec.get("nom_arrondissement_communes")}
        for rec in data.get("results",[])]
    result = {"source":"Paris Open Data","nb_stations":len(stations),
              "timestamp": datetime.now().isoformat(), "from_cache": False, "data":stations}
    set_cache("velib_rt", result, ttl=60)
    return result

@app.get("/api/realtime/air")
async def get_air_realtime():
    cached = get_cache("air_rt")
    if cached: return {**cached, "from_cache": True}
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/qualite-de-l-air-exposition-des-parisen-ne-s-au-no2-et-pm2-5/records?limit=10"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        data = r.json()
    result = {"source":"Paris Open Data","timestamp":datetime.now().isoformat(),
              "from_cache":False,"data":data.get("results",[])}
    set_cache("air_rt", result, ttl=300)
    return result

@app.get("/api/realtime/velo-compteurs")
async def get_velo_compteurs():
    cached = get_cache("velo_rt")
    if cached: return {**cached, "from_cache": True}
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-donnees-compteurs/records?limit=50&order_by=date%20DESC"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        data = r.json()
    compteurs = [{"id_compteur":r2.get("id_compteur"),"nom_compteur":r2.get("nom_compteur"),
        "date":r2.get("date"),"comptage_horaire":r2.get("comptage_horaire"),
        "coordonnees":r2.get("coordonnees_geo")} for r2 in data.get("results",[])]
    result = {"source":"Paris Open Data","nb_compteurs":len(compteurs),
              "timestamp":datetime.now().isoformat(),"from_cache":False,"data":compteurs}
    set_cache("velo_rt", result, ttl=120)
    return result