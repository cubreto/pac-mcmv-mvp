#!/usr/bin/env python3
"""
Generate fake data for PAC and Habitação programs
Used as placeholder until real Habitação data arrives
"""

import pandas as pd
import numpy as np
from faker import Faker
from faker.providers import BaseProvider
import random
from datetime import datetime, timedelta

fake = Faker('pt_BR')

class PACProvider(BaseProvider):
    """Custom provider for PAC/MCMV specific data"""
    
    pac_programs = [
        "Construção de Hospitais e UBS",
        "Pavimentação de Vias Urbanas", 
        "Construção de Escolas",
        "Saneamento Básico",
        "Construção de Pontes",
        "Drenagem Urbana",
        "Energia Elétrica Rural",
        "Abastecimento de Água"
    ]
    
    habitacao_programs = [
        "Minha Casa Minha Vida - Faixa 1",
        "Minha Casa Minha Vida - Faixa 2", 
        "Minha Casa Minha Vida - Faixa 3",
        "Casa Verde e Amarela",
        "Regularização Fundiária",
        "Urbanização de Assentamentos",
        "Habitação Rural",
        "Reabilitação de Áreas Centrais"
    ]
    
    situacao_templates = {
        'normal': [
            "Obra em execução conforme cronograma estabelecido",
            "Projeto aprovado e em fase de licitação",
            "Execução dentro do prazo previsto", 
            "Obra concluída e entregue à população",
            "Em processo de medição de obra executada",
            "Aguardando vistoria técnica para liberação"
        ],
        'problema_recursos': [
            "Obra paralisada por falta de recursos financeiros",
            "Aguardando liberação de verba para continuidade",
            "Cronograma atrasado devido atraso no repasse",
            "Suspensa temporariamente por contingenciamento orçamentário"
        ],
        'problema_documentacao': [
            "Pendente documentação técnica para aprovação",
            "Aguardando regularização documental do terreno",
            "Falta de certidões necessárias para prosseguimento",
            "Documentação em análise pelos órgãos competentes"
        ],
        'problema_ambiental': [
            "Aguardando licenciamento ambiental do IBAMA",
            "Pendente parecer técnico ambiental",
            "Em processo de compensação ambiental",
            "Suspenso para adequação às normas ambientais"
        ],
        'problema_tecnico': [
            "Obra paralisada por problemas técnicos no projeto",
            "Necessária revisão das especificações técnicas",
            "Aguardando aprovação de projeto executivo",
            "Em adequação às normas técnicas vigentes"
        ]
    }
    
    def pac_programa(self):
        return self.random_element(self.pac_programs)
    
    def habitacao_programa(self):
        return self.random_element(self.habitacao_programs)
    
    def situacao_atual(self):
        # 60% normal, 40% problems
        if random.random() < 0.6:
            category = 'normal'
        else:
            category = random.choice(['problema_recursos', 'problema_documentacao', 
                                    'problema_ambiental', 'problema_tecnico'])
        
        return self.random_element(self.situacao_templates[category])

fake.add_provider(PACProvider)

def generate_pac_data(n_records=500):
    """Generate fake PAC data"""
    
    records = []
    brazilian_states = [
        'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 
        'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 
        'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
    ]
    
    for _ in range(n_records):
        uf = random.choice(brazilian_states)
        
        record = {
            'proposta': f"PAC-{fake.random_int(10000, 99999)}",
            'uf': uf,
            'municipio_beneficiado': fake.city(),
            'programa': fake.pac_programa(),
            'tipo_programa': 'PAC',
            'valor_repasse': round(random.uniform(100000, 50000000), 2),
            'valor_investimento': round(random.uniform(150000, 60000000), 2),
            'valor_empenhado': round(random.uniform(50000, 45000000), 2),
            'valor_pago': round(random.uniform(10000, 40000000), 2),
            'percentual_obra_realizado': round(random.uniform(0, 100), 1),
            'data_inicio_obra': fake.date_between(start_date='-2y', end_date='today'),
            'situacao_atual': fake.situacao_atual(),
            'data_atualizacao_situacao': fake.date_between(start_date='-6m', end_date='today')
        }
        
        records.append(record)
    
    return pd.DataFrame(records)

def generate_habitacao_data(n_records=300):
    """Generate fake Habitação data"""
    
    records = []
    brazilian_states = [
        'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 
        'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 
        'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
    ]
    
    for _ in range(n_records):
        uf = random.choice(brazilian_states)
        
        record = {
            'proposta': f"HAB-{fake.random_int(10000, 99999)}",
            'uf': uf,
            'municipio_beneficiado': fake.city(),
            'programa': fake.habitacao_programa(),
            'tipo_programa': 'HABITACAO',
            'valor_repasse': round(random.uniform(50000, 20000000), 2),
            'valor_investimento': round(random.uniform(80000, 25000000), 2),
            'valor_empenhado': round(random.uniform(30000, 18000000), 2),
            'valor_pago': round(random.uniform(5000, 15000000), 2),
            'percentual_obra_realizado': round(random.uniform(0, 100), 1),
            'data_inicio_obra': fake.date_between(start_date='-2y', end_date='today'),
            'situacao_atual': fake.situacao_atual(),
            'data_atualizacao_situacao': fake.date_between(start_date='-6m', end_date='today')
        }
        
        records.append(record)
    
    return pd.DataFrame(records)

def generate_combined_dataset(pac_records=500, habitacao_records=300):
    """Generate combined PAC + Habitação dataset"""
    
    print(f"Generating {pac_records} PAC records...")
    pac_df = generate_pac_data(pac_records)
    
    print(f"Generating {habitacao_records} Habitação records...")
    habitacao_df = generate_habitacao_data(habitacao_records)
    
    # Combine datasets
    combined_df = pd.concat([pac_df, habitacao_df], ignore_index=True)
    
    print(f"✅ Generated {len(combined_df)} total records")
    print(f"   - PAC: {len(pac_df)} records")
    print(f"   - Habitação: {len(habitacao_df)} records")
    
    return combined_df

if __name__ == "__main__":
    # Generate sample data
    df = generate_combined_dataset()
    
    # Save to CSV for inspection
    df.to_csv('data/sample_combined_data.csv', index=False)
    print("Sample data saved to data/sample_combined_data.csv")
    
    # Show sample
    print("\nSample records:")
    print(df[['proposta', 'uf', 'programa', 'tipo_programa', 'situacao_atual']].head())
