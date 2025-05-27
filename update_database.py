# Add this method to etl/database.py
import sys
sys.path.append('.')
from etl.database import DatabaseManager

# Read the current file
with open('etl/database.py', 'r') as f:
    content = f.read()

# Add the corrected method
additional_method = '''
    def get_all_projects(self):
        """Get all projects from the database using actual column names"""
        query = """
        SELECT 
            programa,
            proposta as projeto_id,
            municipio_beneficiado || ' - ' || uf as nome_projeto,
            situacao_atual,
            uf,
            municipio_beneficiado as municipio,
            valor_repasse,
            percentual_obra_realizado as percentual_executado,
            data_inicio_obra as data_inicio,
            data_atualizacao_situacao as data_fim_prevista,
            0 as beneficiarios_previstos
        FROM projeto_status
        """
        return self.load_dataframe(query)
'''

# Write back with the new method
with open('etl/database.py', 'w') as f:
    f.write(content.rstrip() + '\n' + additional_method)

print("✅ Updated database.py with correct column mapping")
