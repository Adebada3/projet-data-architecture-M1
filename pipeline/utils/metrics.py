import time
import functools

def mesure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"  ⏱ {func.__name__} : {elapsed:.2f}s")
        return result
    return wrapper

class PipelineMetrics:
    def __init__(self, nom_script):
        self.nom = nom_script
        self.start = time.time()
        self.etapes = []

    def etape(self, nom, nb_lignes=None, taille_mo=None):
        elapsed = time.time() - self.start
        info = f"  ✓ {nom} — {elapsed:.1f}s"
        if nb_lignes: info += f" · {nb_lignes:,} lignes"
        if taille_mo: info += f" · {taille_mo:.1f} Mo"
        print(info)
        self.etapes.append({
            "etape": nom,
            "temps_s": round(elapsed, 2),
            "nb_lignes": nb_lignes,
            "taille_mo": taille_mo
        })

    def fin(self, nb_lignes_out=None):
        total = time.time() - self.start
        print(f"\n  ═══ {self.nom} terminé en {total:.1f}s ═══")
        if nb_lignes_out:
            throughput = nb_lignes_out / total
            print(f"  Throughput : {throughput:,.0f} lignes/sec")
        return {"script": self.nom, "total_s": round(total, 2), "etapes": self.etapes}