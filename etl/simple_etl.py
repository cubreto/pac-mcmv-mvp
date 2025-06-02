import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# Configuración
excel_path = "data/raw/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx"
db_url = "postgresql://pac_user:pac_password@localhost:5432/pac_mcmv"

print("🚀 Iniciando carga de datos...")

# Cargar Excel
df = pd.read_excel(excel_path)
print(f"✅ Cargados {len(df)} registros con {len(df.columns)} columnas")

# Limpiar nombres de columnas
df.columns = [col.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('ç', 'c').replace('ã', 'a').replace('õ', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('â', 'a').replace('ê', 'e').replace('ô', 'o').replace('à', 'a') for col in df.columns]

# Agregar metadata
df['etl_loaded_at'] = datetime.now()
df['etl_source_file'] = os.path.basename(excel_path)

# Conectar y cargar
engine = create_engine(db_url)

# Truncar y cargar
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE pac_operations CASCADE"))
    conn.commit()

df.to_sql('pac_operations', engine, if_exists='append', index=False, chunksize=1000)

print(f"✅ {len(df)} registros cargados exitosamente!")

# Verificar
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM pac_operations"))
    count = result.scalar()
    print(f"📊 Total en base de datos: {count} registros")
