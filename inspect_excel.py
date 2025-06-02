import pandas as pd

# Cargar el Excel
df = pd.read_excel('data/raw/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx')

print(f"Total de registros: {len(df)}")
print(f"Total de columnas: {len(df.columns)}")
print("\nColumnas encontradas:")
for i, col in enumerate(df.columns):
    print(f"{i+1}. {col}")
