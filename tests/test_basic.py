#!/usr/bin/env python3
"""
Basic tests for PAC-MCMV MVP
"""

import sys
from pathlib import Path
import unittest
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from streamlit_app.text_analyzer import detect_delays, categorize_problems
from etl.fake_data_generator import generate_pac_data

class TestTextAnalyzer(unittest.TestCase):
    
    def test_delay_detection(self):
        """Test delay detection"""
        # Should detect delays
        self.assertTrue(detect_delays("Obra paralisada por falta de recursos"))
        self.assertTrue(detect_delays("Projeto aguardando aprovação"))
        self.assertTrue(detect_delays("Pendente documentação"))
        
        # Should not detect delays  
        self.assertFalse(detect_delays("Obra concluída com sucesso"))
        self.assertFalse(detect_delays("Projeto em execução normal"))
    
    def test_problem_categorization(self):
        """Test problem categorization"""
        problems = categorize_problems("Aguardando documentação técnica")
        self.assertIn("Documentação", problems)
        
        problems = categorize_problems("Falta de recursos financeiros")
        self.assertIn("Recursos Financeiros", problems)
        
        problems = categorize_problems("Pendente licenciamento ambiental")
        self.assertIn("Questões Ambientais", problems)

class TestDataGeneration(unittest.TestCase):
    
    def test_fake_data_generation(self):
        """Test fake data generation"""
        df = generate_pac_data(10)
        
        self.assertEqual(len(df), 10)
        self.assertIn('situacao_atual', df.columns)
        self.assertIn('uf', df.columns)
        self.assertIn('tipo_programa', df.columns)
        
        # All records should be PAC type
        self.assertTrue(all(df['tipo_programa'] == 'PAC'))

if __name__ == '__main__':
    unittest.main()
