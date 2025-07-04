#!/usr/bin/env python3
"""
Data Quality Analysis for Dados Prioritários
Analyzes the original Excel file to create quality metrics for the dashboard
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json

def analyze_excel_file():
    """Analyze the original Excel file for data quality metrics"""
    
    file_path = Path('/home/ec2-user/pac-mcmv-mvp/data/mcmv/FAR_FDS_RURAL_20250627/Dados_Prioritários_Janeiro_Abril_2025.xlsx')
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    print("📊 Analyzing original Excel file for data quality...")
    
    # Load Excel file
    df = pd.read_excel(file_path, sheet_name='Planilha1')
    print(f"✅ Loaded {len(df)} records from Excel")
    
    # Basic statistics
    print(f"\n📈 Basic Statistics:")
    print(f"   Total records: {len(df):,}")
    print(f"   Total columns: {len(df.columns)}")
    
    # Column analysis
    print(f"\n📋 Column Analysis:")
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        print(f"   {col}: {null_count:,} nulls ({null_pct:.1f}%)")
    
    # Program distribution
    print(f"\n🏗️ Program Distribution:")
    if 'Modalidade' in df.columns:
        program_counts = df['Modalidade'].value_counts()
        for program, count in program_counts.items():
            pct = (count / len(df)) * 100
            print(f"   {program}: {count:,} ({pct:.1f}%)")
    
    # Status analysis
    print(f"\n📊 Status Analysis:")
    if 'Situação do Empreendimento' in df.columns:
        status_counts = df['Situação do Empreendimento'].value_counts()
        for status, count in status_counts.items():
            pct = (count / len(df)) * 100
            print(f"   {status}: {count:,} ({pct:.1f}%)")
    
    # Geographic coverage
    print(f"\n🌍 Geographic Coverage:")
    if 'UF' in df.columns:
        uf_counts = df['UF'].value_counts()
        print(f"   Total UFs: {len(uf_counts)}")
        print(f"   Missing UF: {df['UF'].isnull().sum():,}")
        
    if 'Município' in df.columns:
        municipio_counts = df['Município'].value_counts()
        print(f"   Total Municipalities: {len(municipio_counts)}")
        print(f"   Missing Municipality: {df['Município'].isnull().sum():,}")
    
    # Financial data quality
    print(f"\n💰 Financial Data Quality:")
    financial_cols = ['Valor Contratado', 'Valor Desembolsado', 'Valor Aporte Adicional']
    for col in financial_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            zero_count = (df[col] == 0).sum()
            negative_count = (df[col] < 0).sum()
            print(f"   {col}:")
            print(f"     - Missing: {null_count:,}")
            print(f"     - Zero values: {zero_count:,}")
            print(f"     - Negative values: {negative_count:,}")
    
    # Housing units analysis
    print(f"\n🏠 Housing Units Analysis:")
    uh_cols = ['UH Contratadas', 'UH Entregues', 'UH Vigentes', 'Unidades habitacionais a serem entregues']
    for col in uh_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            zero_count = (df[col] == 0).sum()
            total = df[col].sum()
            print(f"   {col}:")
            print(f"     - Missing: {null_count:,}")
            print(f"     - Zero values: {zero_count:,}")
            print(f"     - Total: {total:,.0f}")
    
    # Date analysis
    print(f"\n📅 Date Quality Analysis:")
    date_cols = ['Data de Movimento', 'Data de Contratação', 'Data da previsão da entrega']
    for col in date_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100
            print(f"   {col}: {null_count:,} missing ({null_pct:.1f}%)")
    
    # Percentage execution analysis
    print(f"\n📊 Execution Percentage Analysis:")
    if '% Exec' in df.columns:
        exec_col = df['% Exec']
        null_count = exec_col.isnull().sum()
        invalid_pct = ((exec_col < 0) | (exec_col > 100)).sum()
        zero_count = (exec_col == 0).sum()
        hundred_count = (exec_col == 100).sum()
        
        print(f"   Missing: {null_count:,}")
        print(f"   Invalid (outside 0-100%): {invalid_pct:,}")
        print(f"   Zero execution: {zero_count:,}")
        print(f"   100% completed: {hundred_count:,}")
        print(f"   Mean execution: {exec_col.mean():.1f}%")
    
    return df

def generate_quality_criteria(df):
    """Generate data quality criteria based on analysis"""
    
    print(f"\n🎯 Generating Data Quality Criteria...")
    
    criteria = {
        "completeness_fields": {
            "critical": ["APF", "Modalidade", "UF", "Município", "Situação do Empreendimento"],
            "important": ["Data de Contratação", "Valor Contratado", "UH Contratadas"],
            "optional": ["Data da previsão da entrega", "Valor Aporte Adicional", "Observações"]
        },
        "accuracy_rules": {
            "percentage_fields": ["% Exec"],
            "percentage_range": [0, 100],
            "financial_fields": ["Valor Contratado", "Valor Desembolsado"],
            "financial_min": 0,
            "housing_units_fields": ["UH Contratadas", "UH Entregues", "UH Vigentes"],
            "housing_units_min": 0
        },
        "consistency_rules": {
            "date_order": [
                ("Data de Contratação", "Data da previsão da entrega"),
                ("Data de Movimento", "Data da previsão da entrega")
            ],
            "financial_logic": [
                ("Valor Desembolsado", "<=", "Valor Contratado"),
                ("UH Entregues", "<=", "UH Contratadas")
            ],
            "valid_programs": ["FAR", "FDS", "RURAL"],
            "valid_status": [
                "CONCLUÍDO E ENTREGUE",
                "EM ANDAMENTO", 
                "PARALISADO",
                "FASE PROJETO",
                "DISTRATADO/CANCELADO",
                "DESIMOBILIZADO"
            ]
        },
        "geographic_validation": {
            "valid_ufs": [
                'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
            ],
            "ibge_code_range": [1000000, 9999999]
        }
    }
    
    return criteria

def calculate_program_quality_metrics(df, criteria):
    """Calculate quality metrics by program"""
    
    print(f"\n📊 Calculating Quality Metrics by Program...")
    
    results = {}
    
    for program in df['Modalidade'].unique():
        if pd.isna(program):
            continue
            
        program_df = df[df['Modalidade'] == program].copy()
        total_records = len(program_df)
        
        # Completeness Score
        completeness_issues = 0
        critical_fields = criteria['completeness_fields']['critical']
        important_fields = criteria['completeness_fields']['important']
        
        for field in critical_fields:
            if field in program_df.columns:
                missing = program_df[field].isnull().sum()
                completeness_issues += missing * 2  # Critical fields weighted more
        
        for field in important_fields:
            if field in program_df.columns:
                missing = program_df[field].isnull().sum()
                completeness_issues += missing
        
        max_completeness_issues = total_records * (len(critical_fields) * 2 + len(important_fields))
        completeness_score = max(0, 100 * (1 - completeness_issues / max_completeness_issues))
        
        # Accuracy Score
        accuracy_issues = 0
        
        # Check percentage fields
        for field in criteria['accuracy_rules']['percentage_fields']:
            if field in program_df.columns:
                invalid = ((program_df[field] < 0) | (program_df[field] > 100)).sum()
                accuracy_issues += invalid
        
        # Check financial fields
        for field in criteria['accuracy_rules']['financial_fields']:
            if field in program_df.columns:
                invalid = (program_df[field] < 0).sum()
                accuracy_issues += invalid
        
        # Check housing units
        for field in criteria['accuracy_rules']['housing_units_fields']:
            if field in program_df.columns:
                invalid = (program_df[field] < 0).sum()
                accuracy_issues += invalid
        
        accuracy_score = max(0, 100 * (1 - accuracy_issues / total_records))
        
        # Consistency Score
        consistency_issues = 0
        
        # Check valid programs
        if program not in criteria['consistency_rules']['valid_programs']:
            consistency_issues += total_records
        
        # Check valid status
        if 'Situação do Empreendimento' in program_df.columns:
            invalid_status = ~program_df['Situação do Empreendimento'].isin(
                criteria['consistency_rules']['valid_status']
            )
            consistency_issues += invalid_status.sum()
        
        # Check financial logic
        if 'Valor Desembolsado' in program_df.columns and 'Valor Contratado' in program_df.columns:
            invalid_disbursement = (
                program_df['Valor Desembolsado'] > program_df['Valor Contratado']
            ).sum()
            consistency_issues += invalid_disbursement
        
        if 'UH Entregues' in program_df.columns and 'UH Contratadas' in program_df.columns:
            invalid_delivery = (
                program_df['UH Entregues'] > program_df['UH Contratadas']
            ).sum()
            consistency_issues += invalid_delivery
        
        consistency_score = max(0, 100 * (1 - consistency_issues / total_records))
        
        # Overall Score
        overall_score = (completeness_score + accuracy_score + consistency_score) / 3
        
        # Issue breakdown
        issues = {
            'missing_dates': 0,
            'missing_values': 0,
            'invalid_percentages': 0,
            'date_inconsistencies': 0
        }
        
        # Count specific issues
        date_fields = ['Data de Movimento', 'Data de Contratação', 'Data da previsão da entrega']
        for field in date_fields:
            if field in program_df.columns:
                issues['missing_dates'] += program_df[field].isnull().sum()
        
        value_fields = ['Valor Contratado', 'UH Contratadas']
        for field in value_fields:
            if field in program_df.columns:
                issues['missing_values'] += program_df[field].isnull().sum()
        
        if '% Exec' in program_df.columns:
            issues['invalid_percentages'] = ((program_df['% Exec'] < 0) | (program_df['% Exec'] > 100)).sum()
        
        # Date consistency issues
        if ('Data de Contratação' in program_df.columns and 
            'Data da previsão da entrega' in program_df.columns):
            valid_dates = (
                program_df['Data de Contratação'].notnull() & 
                program_df['Data da previsão da entrega'].notnull()
            )
            if valid_dates.any():
                inconsistent_dates = (
                    program_df.loc[valid_dates, 'Data de Contratação'] > 
                    program_df.loc[valid_dates, 'Data da previsão da entrega']
                ).sum()
                issues['date_inconsistencies'] = inconsistent_dates
        
        results[program] = {
            'program': program,
            'total_records': int(total_records),
            'completeness_score': round(completeness_score, 1),
            'accuracy_score': round(accuracy_score, 1),
            'consistency_score': round(consistency_score, 1),
            'overall_score': round(overall_score, 1),
            'issues': {k: int(v) for k, v in issues.items()}
        }
    
    return results

def main():
    """Main analysis function"""
    print("🔍 MCMV Data Quality Analysis - Dados Prioritários")
    print("=" * 60)
    
    # Analyze Excel file
    df = analyze_excel_file()
    if df is None:
        return
    
    # Generate quality criteria
    criteria = generate_quality_criteria(df)
    
    # Calculate metrics by program
    quality_metrics = calculate_program_quality_metrics(df, criteria)
    
    # Display results
    print(f"\n📊 DATA QUALITY RESULTS:")
    print("=" * 60)
    
    for program, metrics in quality_metrics.items():
        print(f"\n🏗️ {program} Program:")
        print(f"   Records: {metrics['total_records']:,}")
        print(f"   Completeness: {metrics['completeness_score']}%")
        print(f"   Accuracy: {metrics['accuracy_score']}%")
        print(f"   Consistency: {metrics['consistency_score']}%")
        print(f"   Overall Score: {metrics['overall_score']}%")
        print(f"   Issues:")
        for issue_type, count in metrics['issues'].items():
            print(f"     - {issue_type}: {count:,}")
    
    # Save results to JSON
    output_file = Path('/home/ec2-user/pac-mcmv-mvp/dashboard_v5/data_quality_analysis.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(quality_metrics, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"✅ Analysis complete!")

if __name__ == "__main__":
    main()