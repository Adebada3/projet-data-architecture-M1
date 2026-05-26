import pandas as pd

# Lecture du DVF (pandas gère le .gz nativement)
print("Lecture du DVF...")
df = pd.read_csv("data/raw/dvf.csv", 
                 sep=",",
                 low_memory=False)

print(f"Nombre de lignes total : {len(df)}")
print(f"Colonnes : {list(df.columns)}")
print(f"\nAperçu :\n{df.head(3)}")

# Filtre Paris uniquement
paris = df[df['code_commune'].astype(str).str.startswith('75')]
print(f"\nLignes Paris uniquement : {len(paris)}")
print(f"\nTypes de biens :\n{paris['type_local'].value_counts()}")