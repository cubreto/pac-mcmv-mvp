"""
MCMV Dashboard v5 - Smart Database Layer
High-performance async database with materialized view optimization
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, MetaData
from contextlib import asynccontextmanager
import structlog
from typing import Dict, Any, List, Optional
import asyncio
import time

from .config import settings

logger = structlog.get_logger()

# Database metadata
metadata = MetaData(schema="mcmv_v2")
Base = declarative_base(metadata=metadata)

class DatabaseManager:
    """Smart database manager with performance optimization"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._materialized_view_cache = {}
        self._last_refresh_time = {}
        
    async def initialize(self):
        """Initialize database connection with optimized settings"""
        try:
            self.engine = create_async_engine(
                settings.database.url,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.pool_overflow,
                pool_pre_ping=True,
                pool_recycle=1800,  # 30 minutes
                echo=settings.api.debug,
                connect_args={
                    "command_timeout": settings.database.query_timeout,
                    "server_settings": {
                        "jit": "off",  # Disable JIT for predictable performance
                        "application_name": "mcmv_dashboard_v5",
                    }
                }
            )
            
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
            
            logger.info("Database connection initialized successfully",
                       pool_size=settings.database.pool_size,
                       max_overflow=settings.database.pool_overflow)
                       
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session with automatic cleanup"""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute query with performance monitoring"""
        start_time = time.time()
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                
                # Convert to dict format
                if rows:
                    columns = result.keys()
                    data = [dict(zip(columns, row)) for row in rows]
                else:
                    data = []
                
                execution_time = time.time() - start_time
                logger.info("Query executed successfully",
                           query_type="custom",
                           execution_time=f"{execution_time:.3f}s",
                           row_count=len(data))
                
                return data
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("Query execution failed",
                        error=str(e),
                        execution_time=f"{execution_time:.3f}s",
                        query=query[:100] + "..." if len(query) > 100 else query)
            raise

    async def get_kpi_data(self, 
                          programa: Optional[str] = None,
                          regiao: Optional[str] = None,
                          status: Optional[str] = None,
                          state: Optional[str] = None,
                          municipality: Optional[str] = None,
                          tipo: Optional[str] = None,
                          modalidade_proposta: Optional[str] = None) -> Dict[str, Any]:
        """Get KPI data from materialized view with smart caching"""
        
        # For KPIs we'll query directly from mcmv_v2.projetos since we need geographic filters
        # and the materialized view may not have all the needed columns
        
        query = """
        SELECT 
            COUNT(DISTINCT nu_apf) as total_projetos,
            COALESCE(SUM(uh_contratadas), 0) as total_uh_contratadas,
            COALESCE(SUM(vr_total_operacao), 0) as total_contratado,
            COALESCE(SUM(vr_total_investimento), 0) as total_investimento,
            COALESCE(AVG(CASE WHEN uh_contratadas > 0 THEN vr_total_investimento / uh_contratadas END), 0) as investimento_medio_por_uh,
            COALESCE(AVG(pc_obra_realizada), 0) as percentual_execucao_medio,
            SUM(CASE 
                WHEN pc_obra_realizada > 0 AND pc_obra_realizada < 100 
                THEN uh_contratadas ELSE 0 
            END) as uh_em_execucao,
            SUM(CASE 
                WHEN pc_obra_realizada = 0 OR pc_obra_realizada IS NULL 
                THEN uh_contratadas ELSE 0 
            END) as uh_nao_iniciadas,
            SUM(CASE 
                WHEN pc_obra_realizada >= 100 
                THEN uh_contratadas ELSE 0 
            END) as uh_concluidas,
            COUNT(CASE 
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, dt_contratacao)) >= 2 
                AND pc_obra_realizada < 50 THEN 1 
            END) as projetos_alto_risco,
            MAX(dt_movimento) as data_atualizacao
        FROM mcmv_v2.projetos
        WHERE 1=1
        """
        
        params = {}
        
        if programa:
            query += " AND programa = :programa"
            params['programa'] = programa
            
        # Handle region filter with UF mapping
        if regiao:
            region_states = {
                'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
                'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
                'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
                'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
                'Sul': ['PR', 'RS', 'SC']
            }
            if regiao in region_states:
                query += " AND sg_uf = ANY(:regiao_states)"
                params['regiao_states'] = region_states[regiao]
            
        # State filter
        if state:
            query += " AND sg_uf = :state"
            params['state'] = state
            
        # Municipality filter
        if municipality:
            query += " AND no_municipio = :municipality"
            params['municipality'] = municipality
            
        # Status filter based on progress percentage
        if status:
            if status == 'nao_iniciada':
                query += " AND (pc_obra_realizada = 0 OR pc_obra_realizada IS NULL)"
            elif status == 'em_execucao':
                query += " AND pc_obra_realizada > 0 AND pc_obra_realizada < 100"
            elif status == 'concluida':
                query += " AND pc_obra_realizada >= 100"
        
        # RURAL-specific filters
        if tipo:
            query += " AND tipo = :tipo"
            params['tipo'] = tipo
            
        if modalidade_proposta:
            query += " AND modalidade_proposta = :modalidade_proposta"
            params['modalidade_proposta'] = modalidade_proposta
        
        start_time = time.time()
        data = await self.execute_query(query, params)
        execution_time = time.time() - start_time
        
        if data:
            result = data[0]
            logger.info("KPI data retrieved from database",
                       programa=programa,
                       regiao=regiao,
                       status=status,
                       state=state,
                       municipality=municipality,
                       execution_time=f"{execution_time:.3f}s",
                       source="mcmv_v2.projetos")
            return result
        else:
            logger.warning("No KPI data found", 
                         programa=programa, regiao=regiao, status=status,
                         state=state, municipality=municipality)
            return self._get_empty_kpi_response()
    
    async def get_regional_summary(
        self, 
        programa: Optional[str] = None,
        regiao: Optional[str] = None,
        state: Optional[str] = None,
        municipality: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get regional summary with detailed financial breakdown"""
        
        # Skip materialized view refresh for this query since we're querying mcmv_v2.projetos directly
        
        # Query from mcmv_v2.projetos to get the specific columns requested + execution status
        query = """
        SELECT 
            CASE sg_uf 
                WHEN 'AC' THEN 'Norte' WHEN 'AP' THEN 'Norte' WHEN 'AM' THEN 'Norte' 
                WHEN 'PA' THEN 'Norte' WHEN 'RO' THEN 'Norte' WHEN 'RR' THEN 'Norte' WHEN 'TO' THEN 'Norte'
                WHEN 'AL' THEN 'Nordeste' WHEN 'BA' THEN 'Nordeste' WHEN 'CE' THEN 'Nordeste' 
                WHEN 'MA' THEN 'Nordeste' WHEN 'PB' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste' 
                WHEN 'PI' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste'
                WHEN 'DF' THEN 'Centro-Oeste' WHEN 'GO' THEN 'Centro-Oeste' 
                WHEN 'MT' THEN 'Centro-Oeste' WHEN 'MS' THEN 'Centro-Oeste'
                WHEN 'ES' THEN 'Sudeste' WHEN 'MG' THEN 'Sudeste' 
                WHEN 'RJ' THEN 'Sudeste' WHEN 'SP' THEN 'Sudeste'
                WHEN 'PR' THEN 'Sul' WHEN 'RS' THEN 'Sul' WHEN 'SC' THEN 'Sul'
                ELSE 'Outros'
            END as regiao,
            COUNT(DISTINCT nu_apf) as total_projetos,
            SUM(uh_contratadas) as total_uh,
            SUM(vr_total_operacao) as total_contratado,
            SUM(vr_ts) as trabalho_social,
            SUM(vr_total_contrapartidas) as contrapartida,
            SUM(vr_total_investimento) as total_investimento,
            AVG(pc_obra_realizada) as percentual_execucao_medio,
            -- Execution status based on your specification:
            -- Não Iniciada: dt_inicio_obra is NULL or after dt_movimento
            SUM(CASE 
                WHEN dt_inicio_obra IS NULL OR dt_inicio_obra > dt_movimento 
                THEN uh_contratadas ELSE 0 
            END) as nao_iniciadas,
            -- Em andamento: dt_inicio_obra before dt_movimento and pc_obra_realizada > 0
            SUM(CASE 
                WHEN dt_inicio_obra IS NOT NULL 
                AND dt_inicio_obra <= dt_movimento 
                AND pc_obra_realizada > 0 
                AND pc_obra_realizada < 100
                THEN uh_contratadas ELSE 0 
            END) as em_execucao,
            -- Concluídas: pc_obra_realizada = 100
            SUM(CASE 
                WHEN pc_obra_realizada >= 100 
                THEN uh_contratadas ELSE 0 
            END) as concluidas
        FROM mcmv_v2.projetos
        WHERE programa IN ('FAR', 'FDS', 'RURAL')
        """
        
        params = {}
        if programa:
            query += " AND programa = :programa"
            params['programa'] = programa
            
        if regiao:
            # Add region filter using the same CASE logic
            query += " AND CASE sg_uf " \
                     "WHEN 'AC' THEN 'Norte' WHEN 'AP' THEN 'Norte' WHEN 'AM' THEN 'Norte' " \
                     "WHEN 'PA' THEN 'Norte' WHEN 'RO' THEN 'Norte' WHEN 'RR' THEN 'Norte' WHEN 'TO' THEN 'Norte' " \
                     "WHEN 'AL' THEN 'Nordeste' WHEN 'BA' THEN 'Nordeste' WHEN 'CE' THEN 'Nordeste' " \
                     "WHEN 'MA' THEN 'Nordeste' WHEN 'PB' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste' " \
                     "WHEN 'PI' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste' " \
                     "WHEN 'DF' THEN 'Centro-Oeste' WHEN 'GO' THEN 'Centro-Oeste' " \
                     "WHEN 'MT' THEN 'Centro-Oeste' WHEN 'MS' THEN 'Centro-Oeste' " \
                     "WHEN 'ES' THEN 'Sudeste' WHEN 'MG' THEN 'Sudeste' " \
                     "WHEN 'RJ' THEN 'Sudeste' WHEN 'SP' THEN 'Sudeste' " \
                     "WHEN 'PR' THEN 'Sul' WHEN 'RS' THEN 'Sul' WHEN 'SC' THEN 'Sul' " \
                     "ELSE 'Outros' END = :regiao"
            params['regiao'] = regiao
            
        if state:
            query += " AND sg_uf = :state"
            params['state'] = state
            
        if municipality:
            query += " AND no_municipio = :municipality"
            params['municipality'] = municipality
            
        query += """
        GROUP BY regiao
        ORDER BY SUM(vr_total_investimento) DESC
        """
        
        start_time = time.time()
        data = await self.execute_query(query, params)
        execution_time = time.time() - start_time
        
        logger.info("Regional summary retrieved",
                   programa=programa,
                   regiao=regiao,
                   state=state,
                   municipality=municipality,
                   execution_time=f"{execution_time:.3f}s",
                   regions_count=len(data),
                   source="materialized_view")
        
        return data
    
    async def get_program_summary(self, 
                                regiao: Optional[str] = None,
                                state: Optional[str] = None,
                                municipality: Optional[str] = None,
                                status: Optional[str] = None,
                                programa: Optional[str] = None,
                                tipo: Optional[str] = None,
                                modalidade_proposta: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get program summary with detailed financial breakdown and execution status"""
        
        # Query from mcmv_v2.projetos to get program-level data similar to regional
        query = """
        SELECT 
            programa,
            COUNT(DISTINCT nu_apf) as total_projetos,
            SUM(uh_contratadas) as total_uh,
            SUM(vr_total_operacao) as total_contratado,
            SUM(vr_ts) as trabalho_social,
            SUM(vr_total_contrapartidas) as contrapartida,
            SUM(vr_total_investimento) as total_investimento,
            AVG(pc_obra_realizada) as percentual_execucao_medio,
            -- Execution status based on your specification:
            -- Não Iniciada: dt_inicio_obra is NULL or after dt_movimento
            SUM(CASE 
                WHEN dt_inicio_obra IS NULL OR dt_inicio_obra > dt_movimento 
                THEN uh_contratadas ELSE 0 
            END) as nao_iniciadas,
            -- Em andamento: dt_inicio_obra before dt_movimento and pc_obra_realizada > 0
            SUM(CASE 
                WHEN dt_inicio_obra IS NOT NULL 
                AND dt_inicio_obra <= dt_movimento 
                AND pc_obra_realizada > 0 
                AND pc_obra_realizada < 100
                THEN uh_contratadas ELSE 0 
            END) as em_execucao,
            -- Concluídas: pc_obra_realizada = 100
            SUM(CASE 
                WHEN pc_obra_realizada >= 100 
                THEN uh_contratadas ELSE 0 
            END) as concluidas
        FROM mcmv_v2.projetos
        WHERE programa IN ('FAR', 'FDS', 'RURAL')
        """
        
        params = {}
        if regiao:
            # Add region filter using same UF mapping as regional summary
            query += """
            AND CASE sg_uf 
                WHEN 'AC' THEN 'Norte' WHEN 'AP' THEN 'Norte' WHEN 'AM' THEN 'Norte' 
                WHEN 'PA' THEN 'Norte' WHEN 'RO' THEN 'Norte' WHEN 'RR' THEN 'Norte' WHEN 'TO' THEN 'Norte'
                WHEN 'AL' THEN 'Nordeste' WHEN 'BA' THEN 'Nordeste' WHEN 'CE' THEN 'Nordeste' 
                WHEN 'MA' THEN 'Nordeste' WHEN 'PB' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste' 
                WHEN 'PI' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste'
                WHEN 'DF' THEN 'Centro-Oeste' WHEN 'GO' THEN 'Centro-Oeste' 
                WHEN 'MT' THEN 'Centro-Oeste' WHEN 'MS' THEN 'Centro-Oeste'
                WHEN 'ES' THEN 'Sudeste' WHEN 'MG' THEN 'Sudeste' 
                WHEN 'RJ' THEN 'Sudeste' WHEN 'SP' THEN 'Sudeste'
                WHEN 'PR' THEN 'Sul' WHEN 'RS' THEN 'Sul' WHEN 'SC' THEN 'Sul'
                ELSE 'Outros'
            END = :regiao
            """
            params['regiao'] = regiao
        
        # Add state filter
        if state:
            query += " AND sg_uf = :state"
            params['state'] = state
        
        # Add municipality filter  
        if municipality:
            query += " AND no_municipio = :municipality"
            params['municipality'] = municipality
        
        # Add status filter (using same logic as KPI endpoint)
        if status:
            if status == 'nao_iniciada':
                query += " AND (pc_obra_realizada = 0 OR pc_obra_realizada IS NULL)"
            elif status == 'em_execucao':
                query += " AND pc_obra_realizada > 0 AND pc_obra_realizada < 100"
            elif status == 'concluida':
                query += " AND pc_obra_realizada >= 100"
        
        # RURAL-specific filters
        if tipo:
            query += " AND tipo = :tipo"
            params['tipo'] = tipo
            
        if modalidade_proposta:
            query += " AND modalidade_proposta = :modalidade_proposta"
            params['modalidade_proposta'] = modalidade_proposta
        
        # Add program filter (this will override the default FAR/FDS/RURAL filter)
        if programa:
            query = query.replace("WHERE programa IN ('FAR', 'FDS', 'RURAL')", f"WHERE programa = :programa")
            params['programa'] = programa
            
        query += """
        GROUP BY programa
        ORDER BY SUM(vr_total_investimento) DESC
        """
        
        start_time = time.time()
        data = await self.execute_query(query, params)
        execution_time = time.time() - start_time
        
        logger.info("Program summary retrieved",
                   regiao=regiao,
                   execution_time=f"{execution_time:.3f}s",
                   programs_count=len(data),
                   source="mcmv_v2.projetos")
        
        return data
    
    async def get_temporal_trends(self, 
                                 programa: Optional[str] = None,
                                 regiao: Optional[str] = None,
                                 months: int = 24) -> List[Dict[str, Any]]:
        """Get temporal trends from materialized view"""
        
        query = """
        SELECT 
            mes_contratacao,
            programa,
            regiao,
            projetos_contratados,
            uh_contratadas_mes,
            investimento_mes,
            projetos_acumulados,
            uh_acumuladas,
            media_movel_3meses
        FROM mcmv_v2.vw_mat_temporal_trends
        WHERE mes_contratacao >= CURRENT_DATE - INTERVAL '%s months'
        """ % months
        
        params = {}
        
        if programa:
            query += " AND programa = :programa"
            params['programa'] = programa
            
        if regiao:
            query += " AND regiao = :regiao"
            params['regiao'] = regiao
            
        query += " ORDER BY mes_contratacao DESC"
        
        data = await self.execute_query(query, params)
        
        logger.info("Temporal trends retrieved",
                   programa=programa,
                   regiao=regiao,
                   months=months,
                   data_points=len(data))
        
        return data
    
    async def get_data_quality_metrics(self) -> List[Dict[str, Any]]:
        """Get data quality metrics"""
        
        query = """
        SELECT 
            programa,
            total_records,
            missing_dt_contratacao,
            missing_dt_inicio_obra,
            missing_pc_obra,
            missing_empreendimento,
            invalid_percentual_obra,
            invalid_uh_contratadas,
            invalid_investimento,
            inicio_antes_contratacao,
            progresso_sem_inicio,
            data_quality_score,
            ultima_verificacao
        FROM mcmv_v2.vw_data_quality_metrics
        ORDER BY data_quality_score DESC
        """
        
        data = await self.execute_query(query)
        
        logger.info("Data quality metrics retrieved", programs_count=len(data))
        
        return data
    
    async def get_delivery_forecast(self, 
                                    programa: Optional[str] = None,
                                    regiao: Optional[str] = None,
                                    state: Optional[str] = None,
                                    municipality: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get delivery forecast data from FAR, FDS, RURAL programs using dt_previsao_conclusao_obra with full filter support"""
        
        await self._check_and_refresh_materialized_views()
        
        # Query actual forecast data from mcmv_v2.projetos table for FAR, FDS, RURAL programs
        query = """
        SELECT
            programa,
            TO_CHAR(dt_previsao_conclusao_obra, 'YYYY-MM') AS ano_mes,
            COUNT(DISTINCT nu_apf) AS numero_projetos,
            SUM(uh_contratadas) AS numero_uhs
        FROM mcmv_v2.projetos
        WHERE dt_previsao_conclusao_obra IS NOT NULL
            AND uh_contratadas > 0
            AND programa IN ('FAR', 'FDS', 'RURAL')
            AND dt_previsao_conclusao_obra > '1980-01-01'  -- Filter out invalid dates like 1970-01-01
        """
        
        params = {}
        if programa:
            query += " AND programa = :programa"
            params['programa'] = programa
        
        if regiao:
            # Map region to states
            region_states = {
                'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
                'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
                'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
                'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
                'Sul': ['PR', 'RS', 'SC']
            }
            if regiao in region_states:
                query += f" AND sg_uf IN ({','.join([':state_' + str(i) for i in range(len(region_states[regiao]))])})"
                for i, uf in enumerate(region_states[regiao]):
                    params[f'state_{i}'] = uf
            
        if state:
            query += " AND sg_uf = :state"
            params['state'] = state
            
        if municipality:
            query += " AND no_municipio = :municipality"
            params['municipality'] = municipality
        
        query += """
        GROUP BY programa, ano_mes
        ORDER BY ano_mes, programa
        """
        
        data = await self.execute_query(query, params)
        
        logger.info("Delivery forecast retrieved from real database", 
                   programa=programa,
                   regiao=regiao,
                   state=state,
                   municipality=municipality,
                   forecast_points=len(data),
                   source="mcmv_v2.projetos.dt_previsao_conclusao_obra (FAR/FDS/RURAL)")
        
        return data
    
    async def _check_and_refresh_materialized_views(self):
        """Check if materialized views need refresh based on configuration"""
        
        refresh_interval = settings.business_rules.performance.get('database', {}).get(
            'materialized_view_refresh_interval', 1800)  # 30 minutes default
        
        current_time = time.time()
        last_refresh = self._last_refresh_time.get('materialized_views', 0)
        
        if current_time - last_refresh > refresh_interval:
            try:
                await self._refresh_materialized_views()
                self._last_refresh_time['materialized_views'] = current_time
                logger.info("Materialized views refreshed automatically",
                           refresh_interval_minutes=refresh_interval/60)
            except Exception as e:
                logger.error("Failed to refresh materialized views", error=str(e))
    
    async def _refresh_materialized_views(self):
        """Refresh all materialized views"""
        
        try:
            # First check if the function exists
            check_query = """
            SELECT EXISTS (
                SELECT 1 
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'mcmv_v2' 
                AND p.proname = 'refresh_all_materialized_views'
            )
            """
            
            function_exists = await self.execute_query(check_query)
            
            if not function_exists or not function_exists[0].get('exists', False):
                logger.warning("Function mcmv_v2.refresh_all_materialized_views() does not exist. "
                             "Please run migration script 002_create_refresh_function.sql")
                return
            
            # Execute the refresh function
            refresh_query = "SELECT * FROM mcmv_v2.refresh_all_materialized_views()"
            
            start_time = time.time()
            result = await self.execute_query(refresh_query)
            refresh_time = time.time() - start_time
            
            if result:
                logger.info("Materialized views refresh completed",
                           refresh_time=f"{refresh_time:.3f}s",
                           views_refreshed=len(result))
                
                # Log details of each view refresh
                for view_result in result:
                    if 'ERROR' in view_result.get('refresh_status', ''):
                        logger.error("Materialized view refresh failed",
                                   view=view_result.get('view_name'),
                                   status=view_result.get('refresh_status'))
                    else:
                        logger.debug("Materialized view refreshed",
                                   view=view_result.get('view_name'),
                                   status=view_result.get('refresh_status'),
                                   time=view_result.get('refresh_time'))
                           
        except Exception as e:
            logger.error("Failed to refresh materialized views", error=str(e))
            # Don't raise - allow application to continue without refresh
    
    def _get_empty_kpi_response(self) -> Dict[str, Any]:
        """Get empty KPI response structure"""
        return {
            'total_projetos': 0,
            'total_uh_contratadas': 0,
            'total_contratado': 0.0,
            'total_investimento': 0.0,
            'investimento_medio_por_uh': 0.0,
            'percentual_execucao_medio': 0.0,
            'uh_em_execucao': 0,
            'uh_nao_iniciadas': 0,
            'uh_concluidas': 0,
            'projetos_alto_risco': 0,
            'data_atualizacao': None
        }
    
    async def get_chart_data(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get chart data - convenience method for Rural chart endpoints"""
        return await self.execute_query(query, params)
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
async def get_database():
    """FastAPI dependency for database access"""
    return db_manager