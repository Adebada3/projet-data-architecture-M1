import pandas as pd
import os

# Filosofi peut avoir plusieurs fichiers selon le téléchargement INSEE
# Lance ce script pour voir ce qu'on a
import os
fichiers = [f for f in os.listdir("data/raw/") if 'filosofi' in f.lower() 
            or 'indic' in f.lower() 
            or 'BASE_TD' in f
            or 'FILO' in f.upper()]
print(f"Fichiers potentiels Filosofi : {fichiers}")

# Liste tous les fichiers raw pour vérifier
print("\nTous les fichiers dans data/raw/ :")
for f in sorted(os.listdir("data/raw/")):
    taille = os.path.getsize(f"data/raw/{f}")
    print(f"  {f} ({taille/1024/1024:.1f} Mo)")