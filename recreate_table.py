import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np

# Conectar a la BD
db_url = "postgresql://pac_user:pac_password@localhost:5432/pac_mcmv"
engine = create_engine(db_url)

# Cargar Excel
df = pd.read_excel('data/raw/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx')

# Limpiar nombres de columnas
df.columns = [col.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('ç', 'c').replace('ã', 'a').replace('õ', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('â', 'a').replace('ê', 'e').replace('ô', 'o').replace('à', 'a') for col in df.columns]

print(f"Total columnas: {len(df.columns)}")

# Eliminar la tabla existente y sus dependencias
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS pac_operations CASCADE"))
    conn.commit()

# Crear la tabla con todas las columnas detectadas automáticamente
# Pandas inferirá los tipos de datos
df.head(0).to_sql('pac_operations', engine, if_exists='replace', index=False)

print("✅ Tabla pac_operations recreada con todas las columnas")

# Mostrar la estructura
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'pac_operations'
        ORDER BY ordinal_position
    """))
    print("\nEstructura de la tabla:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")
