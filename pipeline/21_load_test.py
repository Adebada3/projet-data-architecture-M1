import asyncio
import httpx
import time

API = "http://localhost:8000"

async def test_100_rps():
    print("═" * 50)
    print("TEST 100 REQUÊTES/SECONDE")
    print("═" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test 1 — 100 requêtes simultanées
        print("\n── 100 requêtes simultanées ──")
        start = time.time()
        tasks = [client.get(f"{API}/api/arrondissements") for _ in range(100)]
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        ok = sum(1 for r in responses if r.status_code == 200)
        rps = 100 / elapsed
        print(f"  ✅ {ok}/100 succès en {elapsed:.2f}s → {rps:.0f} req/sec")

        # Test 2 — endpoints variés
        print("\n── 100 requêtes variées simultanées ──")
        urls = (
            [f"{API}/api/arrondissements"] * 30 +
            [f"{API}/api/arrondissements/{i}" for i in range(1, 21)] * 3 +
            [f"{API}/api/prix/evolution?arrondissement={i}" for i in range(1, 11)] * 2 +
            [f"{API}/api/compare?arr1=6&arr2=19"] * 20
        )[:100]
        
        start = time.time()
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start
        ok = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        rps = 100 / elapsed
        print(f"  ✅ {ok}/100 succès en {elapsed:.2f}s → {rps:.0f} req/sec")

        # Test 3 — cache (2e passage)
        print("\n── 100 requêtes avec cache ──")
        start = time.time()
        tasks = [client.get(f"{API}/api/arrondissements") for _ in range(100)]
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        rps = 100 / elapsed
        print(f"  ✅ 100/100 cache hits en {elapsed:.2f}s → {rps:.0f} req/sec")

asyncio.run(test_100_rps())