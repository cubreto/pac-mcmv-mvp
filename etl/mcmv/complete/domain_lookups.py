"""
MCMV Domain Lookups - Centralized lookup tables for all programs
"""

# Building Types (CO_TIPO_EDIFICACAO) - Used by FAR and RURAL
BUILDING_TYPES = {
    '001': 'Apartamento',
    '002': 'Casa sobreposta',
    '003': 'Casa',
    '004': 'Misto'
}

# Brazilian States (SG_UF)
STATE_CODES = {
    'AC': 'Acre',
    'AL': 'Alagoas',
    'AP': 'Amapá',
    'AM': 'Amazonas',
    'BA': 'Bahia',
    'CE': 'Ceará',
    'DF': 'Distrito Federal',
    'ES': 'Espírito Santo',
    'GO': 'Goiás',
    'MA': 'Maranhão',
    'MT': 'Mato Grosso',
    'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais',
    'PA': 'Pará',
    'PB': 'Paraíba',
    'PR': 'Paraná',
    'PE': 'Pernambuco',
    'PI': 'Piauí',
    'RJ': 'Rio de Janeiro',
    'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia',
    'RR': 'Roraima',
    'SC': 'Santa Catarina',
    'SP': 'São Paulo',
    'SE': 'Sergipe',
    'TO': 'Tocantins'
}

# Record Types (CO_TIPO_REGISTRO)
RECORD_TYPES = {
    'A': 'Ativo',
    'B': 'Bloqueado',
    'C': 'Cancelado'
}

# Program Codes
PROGRAMS = {
    'FAR': 'Fundo de Arrendamento Residencial',
    'FDS': 'Fundo de Desenvolvimento Social',
    'RURAL': 'Programa Nacional de Habitação Rural'
}
