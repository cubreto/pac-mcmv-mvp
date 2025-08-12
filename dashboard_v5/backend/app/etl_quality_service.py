"""
ETL Quality Service - Comprehensive data quality analysis for MCMV data
Captures and reports data quality issues during ETL and for ongoing monitoring
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from sqlalchemy import text
import structlog
from collections import defaultdict

logger = structlog.get_logger()

class ETLQualityService:
    """Service for analyzing ETL data quality issues"""
    
    def __init__(self, database):
        self.db = database
        
    async def analyze_dados_prioritarios_quality(self) -> Dict[str, Any]:
        """Comprehensive quality analysis for dados_prioritarios table"""
        try:
            issues = []
            stats = {}
            
            # 1. Check for temporal inconsistencies
            temporal_issues = await self._check_temporal_consistency()
            if temporal_issues:
                issues.extend(temporal_issues)
            
            # 2. Check for whitespace issues
            whitespace_issues = await self._check_whitespace_issues()
            if whitespace_issues:
                issues.extend(whitespace_issues)
            
            # 3. Check for duplicate entries
            duplicate_issues = await self._check_duplicates()
            if duplicate_issues:
                issues.extend(duplicate_issues)
            
            # 4. Check for data type inconsistencies
            type_issues = await self._check_data_types()
            if type_issues:
                issues.extend(type_issues)
            
            # 5. Check for missing required fields
            missing_field_issues = await self._check_missing_fields()
            if missing_field_issues:
                issues.extend(missing_field_issues)
            
            # 6. Check for outliers and anomalies
            anomaly_issues = await self._check_anomalies()
            if anomaly_issues:
                issues.extend(anomaly_issues)
            
            # Get overall statistics
            stats = await self._get_quality_statistics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "table": "dados_prioritarios",
                "total_issues": len(issues),
                "issues": issues,
                "statistics": stats,
                "quality_score": self._calculate_quality_score(issues, stats)
            }
            
        except Exception as e:
            logger.error("Failed to analyze dados_prioritarios quality", error=str(e))
            raise
    
    async def _check_temporal_consistency(self) -> List[Dict[str, Any]]:
        """Check for temporal inconsistencies in data"""
        issues = []
        
        # Check for records with mismatched data_movimento
        query = """
        WITH monthly_data AS (
            SELECT 
                DATE_TRUNC('month', data_movimento) as month,
                data_movimento,
                COUNT(*) as record_count,
                COUNT(DISTINCT data_movimento) as unique_dates
            FROM mcmv_v2.dados_prioritarios
            GROUP BY DATE_TRUNC('month', data_movimento), data_movimento
        ),
        expected_dates AS (
            SELECT 
                month,
                CASE 
                    WHEN EXTRACT(MONTH FROM month) IN (1,3,5,7,8,10,12) THEN month + INTERVAL '30 days'
                    WHEN EXTRACT(MONTH FROM month) = 2 THEN month + INTERVAL '27 days'
                    ELSE month + INTERVAL '29 days'
                END as expected_date
            FROM (SELECT DISTINCT DATE_TRUNC('month', data_movimento) as month FROM mcmv_v2.dados_prioritarios) m
        )
        SELECT 
            md.month,
            md.data_movimento,
            ed.expected_date,
            md.record_count,
            CASE 
                WHEN md.data_movimento != ed.expected_date THEN 'Unexpected date for month'
                ELSE 'OK'
            END as issue
        FROM monthly_data md
        JOIN expected_dates ed ON md.month = ed.month
        WHERE md.data_movimento != ed.expected_date
        """
        
        result = await self.db.execute_query(query)
        for row in result:
            issues.append({
                "type": "inconsistencia_temporal",
                "severity": "medium",
                "description": f"Data de movimento {row['data_movimento']} não corresponde ao fim do mês esperado",
                "details": {
                    "mes": str(row['month']),
                    "data_atual": str(row['data_movimento']),
                    "data_esperada": str(row['expected_date']),
                    "registros_afetados": row['record_count']
                }
            })
        
        # Check for records from wrong months in latest snapshot
        query = """
        WITH latest_month AS (
            SELECT MAX(DATE_TRUNC('month', data_movimento)) as month
            FROM mcmv_v2.dados_prioritarios
        )
        SELECT 
            data_movimento,
            COUNT(*) as record_count,
            array_agg(DISTINCT apf ORDER BY apf) as sample_apfs
        FROM mcmv_v2.dados_prioritarios
        WHERE DATE_TRUNC('month', data_movimento) != (SELECT month FROM latest_month)
        AND data_movimento >= (SELECT month FROM latest_month)
        GROUP BY data_movimento
        """
        
        result = await self.db.execute_query(query)
        for row in result:
            issues.append({
                "type": "dados_mes_incorreto",
                "severity": "high",
                "description": f"Encontrados {row['record_count']} registros de {row['data_movimento']} nos dados do mês mais recente",
                "details": {
                    "data_movimento": str(row['data_movimento']),
                    "quantidade_registros": row['record_count'],
                    "apfs_exemplo": row['sample_apfs']
                }
            })
        
        return issues
    
    async def _check_whitespace_issues(self) -> List[Dict[str, Any]]:
        """Check for whitespace issues in text fields"""
        issues = []
        
        # Check for trailing/leading spaces
        query = """
        SELECT 
            sg_uf,
            municipio,
            LENGTH(municipio) as length,
            LENGTH(TRIM(municipio)) as trimmed_length,
            COUNT(*) as affected_records
        FROM mcmv_v2.dados_prioritarios
        WHERE LENGTH(municipio) != LENGTH(TRIM(municipio))
        GROUP BY sg_uf, municipio
        """
        
        result = await self.db.execute_query(query)
        for row in result:
            issues.append({
                "type": "espacos_extras",
                "severity": "low",
                "description": f"Município '{row['municipio']}' possui espaços no início ou fim",
                "details": {
                    "estado": row['sg_uf'],
                    "municipio": row['municipio'],
                    "tamanho": row['length'],
                    "tamanho_limpo": row['trimmed_length'],
                    "registros_afetados": row['affected_records']
                }
            })
        
        # Check for double/multiple spaces within text
        query = """
        SELECT 
            sg_uf,
            municipio,
            COUNT(*) as affected_records
        FROM mcmv_v2.dados_prioritarios
        WHERE municipio LIKE '%  %'  -- two or more spaces
        GROUP BY sg_uf, municipio
        """
        
        result = await self.db.execute_query(query)
        for row in result:
            issues.append({
                "type": "espacos_duplos",
                "severity": "medium",
                "description": f"Município '{row['municipio']}' possui espaços duplos ou múltiplos",
                "details": {
                    "estado": row['sg_uf'],
                    "municipio": row['municipio'],
                    "registros_afetados": row['affected_records']
                }
            })
        
        return issues
    
    async def _check_duplicates(self) -> List[Dict[str, Any]]:
        """Check for duplicate entries"""
        issues = []
        
        # Check for exact duplicates within same month
        query = """
        WITH duplicates AS (
            SELECT 
                apf,
                data_movimento,
                COUNT(*) as duplicate_count
            FROM mcmv_v2.dados_prioritarios
            GROUP BY apf, data_movimento
            HAVING COUNT(*) > 1
        )
        SELECT 
            data_movimento,
            COUNT(DISTINCT apf) as duplicate_apfs,
            SUM(duplicate_count) as total_duplicates,
            array_agg(apf ORDER BY duplicate_count DESC) as sample_apfs
        FROM duplicates
        GROUP BY data_movimento
        """
        
        result = await self.db.execute_query(query)
        for row in result:
            issues.append({
                "type": "registros_duplicados",
                "severity": "high",
                "description": f"Encontrados {row['duplicate_apfs']} APFs com duplicatas em {row['data_movimento']}",
                "details": {
                    "data_movimento": str(row['data_movimento']),
                    "apfs_duplicados": row['duplicate_apfs'],
                    "total_registros_duplicados": row['total_duplicates'],
                    "apfs_exemplo": row['sample_apfs']
                }
            })
        
        return issues
    
    async def _check_data_types(self) -> List[Dict[str, Any]]:
        """Check for data type inconsistencies"""
        issues = []
        
        # Check numeric fields for non-numeric values
        numeric_fields = [
            'pc_exec', 'valor_contratado', 'valor_desembolsado',
            'uh_contratadas', 'uh_entregues', 'latitude', 'longitude'
        ]
        
        for field in numeric_fields:
            query = f"""
            SELECT 
                COUNT(*) as invalid_count,
                array_agg(DISTINCT apf) as sample_apfs
            FROM mcmv_v2.dados_prioritarios
            WHERE {field} IS NOT NULL 
            AND ({field} < 0 OR {field} > 1e10 OR {field}::text ~ '[^0-9.-]')
            """
            
            try:
                results = await self.db.execute_query(query)
                result = results[0] if results else None
                if result and result['invalid_count'] > 0:
                    issues.append({
                        "type": "valor_numerico_invalido",
                        "severity": "medium",
                        "description": f"Campo '{field}' possui {result['invalid_count']} valores numéricos inválidos",
                        "details": {
                            "campo": field,
                            "quantidade_invalida": result['invalid_count'],
                            "apfs_exemplo": result['sample_apfs']
                        }
                    })
            except:
                pass  # Field might not exist or have different type
        
        return issues
    
    async def _check_missing_fields(self) -> List[Dict[str, Any]]:
        """Check for missing required fields"""
        issues = []
        
        required_fields = {
            'apf': 'APF identifier',
            'nome_empreendimento': 'Project name',
            'sg_uf': 'State code',
            'municipio': 'Municipality',
            'modalidade': 'Program modality',
            'data_movimento': 'Movement date'
        }
        
        for field, description in required_fields.items():
            query = f"""
            SELECT 
                COUNT(*) as missing_count,
                ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios) * 100, 2) as missing_percentage,
                array_agg(DISTINCT apf) as sample_apfs
            FROM mcmv_v2.dados_prioritarios
            WHERE {field} IS NULL OR TRIM({field}::text) = ''
            """
            
            results = await self.db.execute_query(query)
            result = results[0] if results else None
            if result and result['missing_count'] > 0:
                severity = 'high' if result['missing_percentage'] > 10 else 'medium'
                issues.append({
                    "type": "missing_required_field",
                    "severity": severity,
                    "description": f"{description} is missing in {result['missing_count']} records ({result['missing_percentage']}%)",
                    "details": {
                        "field": field,
                        "missing_count": result['missing_count'],
                        "missing_percentage": float(result['missing_percentage']),
                        "sample_apfs": result['sample_apfs']
                    }
                })
        
        return issues
    
    async def _check_anomalies(self) -> List[Dict[str, Any]]:
        """Check for data anomalies and outliers"""
        issues = []
        
        # Check for invalid date ranges
        query = """
        SELECT 
            COUNT(*) as count,
            MIN(data_contratacao) as min_date,
            MAX(data_contratacao) as max_date
        FROM mcmv_v2.dados_prioritarios
        WHERE data_contratacao < '2009-01-01' OR data_contratacao > CURRENT_DATE
        """
        
        results = await self.db.execute_query(query)
        result = results[0] if results else None
        if result and result['count'] > 0:
            issues.append({
                "type": "invalid_date_range",
                "severity": "medium",
                "description": f"Found {result['count']} records with invalid contract dates",
                "details": {
                    "count": result['count'],
                    "min_date": str(result['min_date']),
                    "max_date": str(result['max_date'])
                }
            })
        
        # Check for value outliers
        query = """
        WITH stats AS (
            SELECT 
                AVG(valor_contratado) as avg_value,
                STDDEV(valor_contratado) as std_value
            FROM mcmv_v2.dados_prioritarios
            WHERE valor_contratado > 0
        )
        SELECT 
            COUNT(*) as outlier_count,
            MIN(valor_contratado) as min_value,
            MAX(valor_contratado) as max_value,
            array_agg(apf ORDER BY valor_contratado DESC) as top_apfs
        FROM mcmv_v2.dados_prioritarios, stats
        WHERE valor_contratado > (avg_value + 3 * std_value)
        OR valor_contratado < 0
        """
        
        results = await self.db.execute_query(query)
        result = results[0] if results else None
        if result and result['outlier_count'] > 0:
            issues.append({
                "type": "value_outliers",
                "severity": "low",
                "description": f"Found {result['outlier_count']} records with outlier contract values",
                "details": {
                    "outlier_count": result['outlier_count'],
                    "min_value": float(result['min_value']) if result['min_value'] else 0,
                    "max_value": float(result['max_value']) if result['max_value'] else 0,
                    "sample_apfs": result['top_apfs']
                }
            })
        
        return issues
    
    async def _get_quality_statistics(self) -> Dict[str, Any]:
        """Get overall quality statistics"""
        query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT apf) as unique_projects,
            COUNT(DISTINCT data_movimento) as snapshot_count,
            MIN(data_movimento) as earliest_snapshot,
            MAX(data_movimento) as latest_snapshot,
            COUNT(DISTINCT sg_uf) as states_covered,
            COUNT(DISTINCT municipio) as municipalities_covered
        FROM mcmv_v2.dados_prioritarios
        """
        
        results = await self.db.execute_query(query)
        result = results[0] if results else None
        
        return {
            "total_records": result['total_records'],
            "unique_projects": result['unique_projects'],
            "snapshot_count": result['snapshot_count'],
            "date_range": {
                "start": str(result['earliest_snapshot']),
                "end": str(result['latest_snapshot'])
            },
            "coverage": {
                "states": result['states_covered'],
                "municipalities": result['municipalities_covered']
            }
        }
    
    def _calculate_quality_score(self, issues: List[Dict], stats: Dict) -> float:
        """Calculate overall quality score based on issues found"""
        if not stats.get('total_records', 0):
            return 0.0
        
        # Weight issues by severity
        severity_weights = {
            'high': 10,
            'medium': 5,
            'low': 1
        }
        
        total_weight = sum(severity_weights.get(issue['severity'], 1) for issue in issues)
        
        # Calculate score (100 - penalty)
        penalty = min(100, total_weight * 2)  # Cap at 100
        return round(100 - penalty, 2)
    
    async def analyze_projetos_quality(self) -> Dict[str, Any]:
        """Analyze quality issues in projetos table"""
        # Similar implementation for projetos table
        # This would check for different issues specific to projetos
        pass
    
    async def save_quality_report(self, report: Dict[str, Any]) -> None:
        """Save quality report to database for historical tracking"""
        # TODO: Implement proper insert method in DatabaseManager
        # For now, we'll skip saving to database
        pass