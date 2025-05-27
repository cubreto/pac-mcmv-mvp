#!/usr/bin/env python3
"""
Simple text analyzer for PAC "Situação Atual" field - no over-engineering
Fixed regex warnings for Python 3.12+ compatibility
"""

import re
from collections import Counter
import pandas as pd

# Portuguese stopwords (simplified list)
STOPWORDS = {
    'a', 'ao', 'aos', 'as', 'à', 'às', 'da', 'das', 'de', 'do', 'dos', 'e', 'em', 
    'na', 'nas', 'no', 'nos', 'o', 'os', 'para', 'por', 'com', 'um', 'uma', 'uns', 
    'umas', 'se', 'que', 'não', 'mais', 'muito', 'como', 'mas', 'já', 'também', 
    'só', 'até', 'isso', 'ela', 'ele', 'eles', 'elas', 'seu', 'sua', 'seus', 'suas',
    'foi', 'ser', 'está', 'tem', 'ter', 'são', 'foram', 'será', 'sendo', 'sido'
}

def clean_text(text):
    """Basic text cleaning"""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    text = text.lower()
    # Fixed regex patterns (no more warnings)
    text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
    text = re.sub(r'\d+', ' ', text)      # Remove numbers
    text = re.sub(r'\s+', ' ', text)      # Multiple spaces to single
    
    return text.strip()

def get_word_frequency(texts):
    """Get word frequency from list of texts"""
    all_words = []
    
    for text in texts:
        cleaned = clean_text(text)
        words = cleaned.split()
        filtered_words = [w for w in words if len(w) > 2 and w not in STOPWORDS]
        all_words.extend(filtered_words)
    
    return Counter(all_words).most_common(20)

def detect_delays(text):
    """Detect if text indicates delays or problems"""
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    text_lower = text.lower()
    
    delay_indicators = [
        'atras', 'demora', 'pendente', 'aguardando', 'paralisad', 'suspend',
        'problem', 'dificuldade', 'impedimento', 'bloqueado', 'travado',
        'falta', 'ausência', 'carente', 'insuficiente', 'inadequado',
        'rejeitado', 'não aprovado', 'não concluído', 'incompleto'
    ]
    
    return any(indicator in text_lower for indicator in delay_indicators)

def categorize_problems(text):
    """Categorize types of problems"""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    problems = []
    
    categories = {
        'Documentação': ['document', 'certidão', 'comprovante', 'anexo', 'papelada'],
        'Recursos Financeiros': ['recurso', 'verba', 'financeiro', 'orçamento', 'pagamento'],
        'Aprovação/Licenças': ['aprovação', 'licença', 'autorização', 'alvará'],
        'Questões Técnicas': ['técnico', 'engenharia', 'projeto', 'especificação'],
        'Questões Ambientais': ['ambiental', 'ibama', 'meio ambiente', 'licenciamento'],
        'Questões Legais': ['jurídico', 'legal', 'lei', 'judicial', 'processo']
    }
    
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            problems.append(category)
    
    return problems

def analyze_situacao_texts(texts):
    """Main analysis function"""
    results = {
        'total_texts': len(texts),
        'common_words': get_word_frequency(texts),
        'delay_count': sum(detect_delays(text) for text in texts)
    }
    
    return results

if __name__ == "__main__":
    # Test with sample texts
    sample_texts = [
        "Projeto aguardando aprovação da documentação técnica",
        "Obra paralisada por falta de recursos financeiros",
        "Pendente licenciamento ambiental do IBAMA"
    ]
    
    results = analyze_situacao_texts(sample_texts)
    print("Analysis results:", results)
