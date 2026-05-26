import pandas as pd

df = pd.read_csv("data/raw/logements-sociaux-finances-a-paris.csv", sep=";", low_memory=False)
print(f"Colonnes : {list(df.columns)}")
print(f"Lignes : {len(df):,}")
print(df.head(3))