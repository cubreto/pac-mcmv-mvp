"""
MCMV Dashboard v5 - Cascading Filters Module
Implements cascading filter logic for Region → UF → Município → Situação → Programa
"""

from typing import Dict, List, Optional, Any
from sqlalchemy import text
import structlog
from .database import DatabaseManager

logger = structlog.get_logger()

class FilterService:
    """Service for handling cascading filters with regional mappings"""
    
    # Regional mappings from business rules
    REGIONAL_MAPPINGS = {
        'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
        'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
        'Sul': ['PR', 'RS', 'SC']
    }
    
    # Status mappings based on business rules
    STATUS_MAPPINGS = {
        'nao_iniciada': {
            'label': 'Não Iniciada',
            'description': 'Projetos sem execução física iniciada',
            'sql_condition': 'pc_obra_realizada = 0 OR pc_obra_realizada IS NULL'
        },
        'em_execucao': {
            'label': 'Em Execução',
            'description': 'Projetos com execução física em andamento',
            'sql_condition': 'pc_obra_realizada > 0 AND pc_obra_realizada < 100'
        },
        'concluida': {
            'label': 'Concluída',
            'description': 'Projetos com execução física finalizada',
            'sql_condition': 'pc_obra_realizada >= 100'
        }
    }
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def get_regions(self) -> List[Dict[str, Any]]:
        """Get all available regions"""
        try:
            regions = []
            for region_name, states in self.REGIONAL_MAPPINGS.items():
                # Get count of projects in this region
                query = """
                SELECT COUNT(DISTINCT nu_apf) as project_count,
                       SUM(uh_contratadas) as total_uh
                FROM mcmv_v2.projetos 
                WHERE sg_uf = ANY(:states)
                """
                
                result = await self.db_manager.execute_query(query, {'states': states})
                
                if result:
                    regions.append({
                        'name': region_name,
                        'states': states,
                        'project_count': result[0]['project_count'] or 0,
                        'total_uh': result[0]['total_uh'] or 0
                    })
            
            logger.info("Regions retrieved successfully", count=len(regions))
            return regions
            
        except Exception as e:
            logger.error("Failed to get regions", error=str(e))
            raise
    
    async def get_states(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get states, optionally filtered by region"""
        try:
            query = """
            SELECT sg_uf,
                   COUNT(DISTINCT nu_apf) as project_count,
                   SUM(uh_contratadas) as total_uh
            FROM mcmv_v2.projetos 
            WHERE sg_uf IS NOT NULL
            """
            
            params = {}
            if region and region in self.REGIONAL_MAPPINGS:
                query += " AND sg_uf = ANY(:states)"
                params['states'] = self.REGIONAL_MAPPINGS[region]
            
            query += """
            GROUP BY sg_uf
            ORDER BY sg_uf
            """
            
            result = await self.db_manager.execute_query(query, params)
            
            # Add region info to each state
            states = []
            for row in result:
                state_code = row['sg_uf']
                state_region = None
                
                # Find which region this state belongs to
                for reg_name, reg_states in self.REGIONAL_MAPPINGS.items():
                    if state_code in reg_states:
                        state_region = reg_name
                        break
                
                states.append({
                    'code': state_code,
                    'region': state_region,
                    'project_count': row['project_count'],
                    'total_uh': row['total_uh']
                })
            
            logger.info("States retrieved successfully", 
                       region=region, count=len(states))
            return states
            
        except Exception as e:
            logger.error("Failed to get states", region=region, error=str(e))
            raise
    
    async def get_municipalities(self, 
                               region: Optional[str] = None,
                               state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get municipalities, optionally filtered by region and/or state"""
        try:
            query = """
            SELECT no_municipio as municipality,
                   sg_uf,
                   COUNT(DISTINCT nu_apf) as project_count,
                   SUM(uh_contratadas) as total_uh
            FROM mcmv_v2.projetos 
            WHERE no_municipio IS NOT NULL
            """
            
            params = {}
            
            if state:
                query += " AND sg_uf = :state"
                params['state'] = state
            elif region and region in self.REGIONAL_MAPPINGS:
                query += " AND sg_uf = ANY(:states)"
                params['states'] = self.REGIONAL_MAPPINGS[region]
            
            query += """
            GROUP BY no_municipio, sg_uf
            ORDER BY no_municipio
            """
            
            result = await self.db_manager.execute_query(query, params)
            
            municipalities = []
            for row in result:
                municipalities.append({
                    'name': row['municipality'],
                    'state': row['sg_uf'],
                    'project_count': row['project_count'],
                    'total_uh': row['total_uh']
                })
            
            logger.info("Municipalities retrieved successfully", 
                       region=region, state=state, count=len(municipalities))
            return municipalities
            
        except Exception as e:
            logger.error("Failed to get municipalities", 
                        region=region, state=state, error=str(e))
            raise
    
    async def get_status_options(self) -> List[Dict[str, Any]]:
        """Get available status options with counts"""
        try:
            query = """
            SELECT 
                CASE 
                    WHEN pc_obra_realizada = 0 OR pc_obra_realizada IS NULL THEN 'nao_iniciada'
                    WHEN pc_obra_realizada > 0 AND pc_obra_realizada < 100 THEN 'em_execucao'
                    WHEN pc_obra_realizada >= 100 THEN 'concluida'
                END as status_code,
                COUNT(DISTINCT nu_apf) as project_count,
                SUM(uh_contratadas) as total_uh
            FROM mcmv_v2.projetos
            GROUP BY status_code
            ORDER BY status_code
            """
            
            result = await self.db_manager.execute_query(query)
            
            status_options = []
            for row in result:
                status_code = row['status_code']
                if status_code in self.STATUS_MAPPINGS:
                    status_options.append({
                        'code': status_code,
                        'label': self.STATUS_MAPPINGS[status_code]['label'],
                        'description': self.STATUS_MAPPINGS[status_code]['description'],
                        'project_count': row['project_count'],
                        'total_uh': row['total_uh']
                    })
            
            logger.info("Status options retrieved successfully", count=len(status_options))
            return status_options
            
        except Exception as e:
            logger.error("Failed to get status options", error=str(e))
            raise
    
    async def get_programs(self, 
                          region: Optional[str] = None,
                          state: Optional[str] = None,
                          municipality: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available programs with optional geographic filters"""
        try:
            query = """
            SELECT programa,
                   COUNT(DISTINCT nu_apf) as project_count,
                   SUM(uh_contratadas) as total_uh,
                   SUM(vr_total_investimento) as total_investment
            FROM mcmv_v2.projetos 
            WHERE programa IS NOT NULL
            """
            
            params = {}
            
            if municipality:
                query += " AND no_municipio = :municipality"
                params['municipality'] = municipality
            
            if state:
                query += " AND sg_uf = :state"
                params['state'] = state
            elif region and region in self.REGIONAL_MAPPINGS:
                query += " AND sg_uf = ANY(:states)"
                params['states'] = self.REGIONAL_MAPPINGS[region]
            
            query += """
            GROUP BY programa
            ORDER BY SUM(vr_total_investimento) DESC
            """
            
            result = await self.db_manager.execute_query(query, params)
            
            programs = []
            for row in result:
                programs.append({
                    'code': row['programa'],
                    'name': row['programa'],  # Can be enhanced with full names
                    'project_count': row['project_count'],
                    'total_uh': row['total_uh'],
                    'total_investment': row['total_investment']
                })
            
            logger.info("Programs retrieved successfully", 
                       region=region, state=state, municipality=municipality, 
                       count=len(programs))
            return programs
            
        except Exception as e:
            logger.error("Failed to get programs", 
                        region=region, state=state, municipality=municipality, 
                        error=str(e))
            raise
    
    def build_where_clause(self, filters: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Build SQL WHERE clause and parameters from filter dict
        
        Args:
            filters: Dictionary with filter keys and values
            
        Returns:
            Tuple of (where_clause, parameters)
        """
        conditions = []
        params = {}
        
        try:
            # Region filter
            if filters.get('region') and filters['region'] in self.REGIONAL_MAPPINGS:
                conditions.append("sg_uf = ANY(:region_states)")
                params['region_states'] = self.REGIONAL_MAPPINGS[filters['region']]
            
            # State filter
            if filters.get('state'):
                conditions.append("sg_uf = :state")
                params['state'] = filters['state']
            
            # Municipality filter
            if filters.get('municipality'):
                conditions.append("no_municipio = :municipality")
                params['municipality'] = filters['municipality']
            
            # Status filter
            if filters.get('status') and filters['status'] in self.STATUS_MAPPINGS:
                status_condition = self.STATUS_MAPPINGS[filters['status']]['sql_condition']
                conditions.append(f"({status_condition})")
            
            # Program filter
            if filters.get('programa'):
                conditions.append("programa = :programa")
                params['programa'] = filters['programa']
            
            # Build final WHERE clause
            where_clause = ""
            if conditions:
                where_clause = " AND " + " AND ".join(conditions)
            
            logger.info("WHERE clause built successfully", 
                       conditions_count=len(conditions),
                       where_clause=where_clause)
            
            return where_clause, params
            
        except Exception as e:
            logger.error("Failed to build WHERE clause", filters=filters, error=str(e))
            raise
    
    async def get_filter_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary statistics for current filter combination"""
        try:
            where_clause, params = self.build_where_clause(filters)
            
            query = f"""
            SELECT 
                COUNT(DISTINCT nu_apf) as total_projects,
                SUM(uh_contratadas) as total_uh,
                SUM(vr_total_investimento) as total_investment,
                AVG(pc_obra_realizada) as avg_progress,
                COUNT(DISTINCT sg_uf) as states_count,
                COUNT(DISTINCT no_municipio) as municipalities_count,
                COUNT(DISTINCT programa) as programs_count
            FROM mcmv_v2.projetos
            WHERE 1=1 {where_clause}
            """
            
            result = await self.db_manager.execute_query(query, params)
            
            if result:
                summary = result[0]
                logger.info("Filter summary retrieved successfully", 
                           filters=filters, summary=summary)
                return summary
            else:
                return {
                    'total_projects': 0,
                    'total_uh': 0,
                    'total_investment': 0,
                    'avg_progress': 0,
                    'states_count': 0,
                    'municipalities_count': 0,
                    'programs_count': 0
                }
                
        except Exception as e:
            logger.error("Failed to get filter summary", filters=filters, error=str(e))
            raise