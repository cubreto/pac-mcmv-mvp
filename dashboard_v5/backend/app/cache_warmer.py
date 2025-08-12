"""
Cache Warming Service for MCMV Dashboard v5
Pre-populates Redis cache with common queries on startup
"""
import asyncio
import structlog
from typing import List, Dict, Any
from .database import db_manager
from .cache import cache_manager
from .config import settings

logger = structlog.get_logger()

class CacheWarmer:
    """Service to warm up cache with frequently accessed data"""
    
    def __init__(self):
        self.warm_queries = [
            # KPIs for main dashboard and each program
            {"endpoint": "kpis", "params": {}},
            {"endpoint": "kpis", "params": {"programa": "FAR"}},
            {"endpoint": "kpis", "params": {"programa": "FDS"}},
            {"endpoint": "kpis", "params": {"programa": "RURAL"}},
            
            # Regional summaries
            {"endpoint": "regional", "params": {}},
            {"endpoint": "regional", "params": {"programa": "FAR"}},
            {"endpoint": "regional", "params": {"programa": "FDS"}},
            {"endpoint": "regional", "params": {"programa": "RURAL"}},
            
            # Program summaries
            {"endpoint": "programs", "params": {}},
            
            # Dados prioritários latest state
            {"endpoint": "dados_prioritarios_estado_atual", "params": {}},
            
            # Common filters
            {"endpoint": "filters_regions", "params": {}},
            {"endpoint": "filters_states", "params": {}},
            {"endpoint": "filters_programs", "params": {}},
        ]
    
    async def warm_kpis(self, params: Dict[str, Any]) -> None:
        """Warm KPI data"""
        try:
            programa = params.get('programa')
            cache_key = f"kpis:{programa or 'ALL'}:ALL:ALL:ALL"
            
            # Check if already cached
            cached = await cache_manager.get(cache_key)
            if cached:
                logger.info("Cache already warm", endpoint="kpis", params=params)
                return
            
            # Get data from database
            data = await db_manager.get_kpi_data(programa=programa)
            
            # Cache it
            cache_ttl = settings.business_rules.get_cache_ttl('summary_data')
            await cache_manager.set(cache_key, data, expire=cache_ttl)
            
            logger.info("Cache warmed", endpoint="kpis", params=params)
            
        except Exception as e:
            logger.error("Failed to warm KPI cache", error=str(e), params=params)
    
    async def warm_regional(self, params: Dict[str, Any]) -> None:
        """Warm regional summary data"""
        try:
            programa = params.get('programa')
            cache_key = f"regional:{programa or 'ALL'}"
            
            cached = await cache_manager.get(cache_key)
            if cached:
                logger.info("Cache already warm", endpoint="regional", params=params)
                return
            
            data = await db_manager.get_regional_summary(programa=programa)
            
            cache_ttl = settings.business_rules.get_cache_ttl('aggregated_data')
            await cache_manager.set(cache_key, data, expire=cache_ttl)
            
            logger.info("Cache warmed", endpoint="regional", params=params)
            
        except Exception as e:
            logger.error("Failed to warm regional cache", error=str(e), params=params)
    
    async def warm_programs(self, params: Dict[str, Any]) -> None:
        """Warm program summary data"""
        try:
            cache_key = "programs:ALL|ALL|ALL|ALL|ALL|ALL|ALL"
            
            cached = await cache_manager.get(cache_key)
            if cached:
                logger.info("Cache already warm", endpoint="programs", params=params)
                return
            
            data = await db_manager.get_program_summary()
            
            # Transform to dict for caching
            result = {
                "data": data,
                "metadata": {
                    "programs_count": len(data),
                    "cache_ttl": settings.business_rules.get_cache_ttl('summary_data')
                }
            }
            
            await cache_manager.set(cache_key, result, expire=result["metadata"]["cache_ttl"])
            
            logger.info("Cache warmed", endpoint="programs", params=params)
            
        except Exception as e:
            logger.error("Failed to warm programs cache", error=str(e), params=params)
    
    async def warm_dados_prioritarios_estado_atual(self, params: Dict[str, Any]) -> None:
        """Warm dados prioritarios latest state"""
        try:
            cache_key = "dados_prioritarios:estado_atual:latest"
            
            cached = await cache_manager.get(cache_key)
            if cached:
                logger.info("Cache already warm", endpoint="dados_prioritarios_estado_atual", params=params)
                return
            
            # Query for latest state
            query = """
            SELECT DISTINCT ON (apf)
                apf, modalidade, situacao_empreendimento, sg_uf, municipio,
                nome_empreendimento, data_movimento, uh_original_contratadas,
                uh_entregues, valor_contratado, valor_desembolsado
            FROM mcmv_v2.dados_prioritarios
            WHERE EXTRACT(month FROM data_movimento) = 5 
                AND EXTRACT(year FROM data_movimento) = 2025
            ORDER BY apf, data_movimento DESC
            """
            
            data = await db_manager.execute_query(query)
            
            cache_ttl = settings.business_rules.get_cache_ttl('tables')
            await cache_manager.set(cache_key, {"data": data}, expire=cache_ttl)
            
            logger.info("Cache warmed", endpoint="dados_prioritarios_estado_atual", params=params)
            
        except Exception as e:
            logger.error("Failed to warm dados prioritarios cache", error=str(e), params=params)
    
    async def warm_filters(self, endpoint: str, params: Dict[str, Any]) -> None:
        """Warm filter data"""
        try:
            if endpoint == "filters_regions":
                cache_key = "filters:regions"
                data = [
                    {"value": "Norte", "label": "Norte"},
                    {"value": "Nordeste", "label": "Nordeste"},
                    {"value": "Centro-Oeste", "label": "Centro-Oeste"},
                    {"value": "Sudeste", "label": "Sudeste"},
                    {"value": "Sul", "label": "Sul"}
                ]
            elif endpoint == "filters_states":
                cache_key = "filters:states:ALL"
                query = "SELECT DISTINCT sg_uf FROM mcmv_v2.projetos WHERE sg_uf IS NOT NULL ORDER BY sg_uf"
                states = await db_manager.execute_query(query)
                data = [{"value": s["sg_uf"], "label": s["sg_uf"]} for s in states]
            elif endpoint == "filters_programs":
                cache_key = "filters:programs"
                data = [
                    {"value": "FAR", "label": "FAR"},
                    {"value": "FDS", "label": "FDS"},
                    {"value": "RURAL", "label": "RURAL"}
                ]
            else:
                return
            
            cached = await cache_manager.get(cache_key)
            if cached:
                logger.info("Cache already warm", endpoint=endpoint, params=params)
                return
            
            cache_ttl = settings.business_rules.get_cache_ttl('static_data')
            await cache_manager.set(cache_key, data, expire=cache_ttl)
            
            logger.info("Cache warmed", endpoint=endpoint, params=params)
            
        except Exception as e:
            logger.error("Failed to warm filter cache", endpoint=endpoint, error=str(e))
    
    async def warm_all(self) -> None:
        """Warm all configured caches"""
        logger.info("Starting cache warming process...")
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for query in self.warm_queries:
            endpoint = query["endpoint"]
            params = query["params"]
            
            if endpoint == "kpis":
                tasks.append(self.warm_kpis(params))
            elif endpoint == "regional":
                tasks.append(self.warm_regional(params))
            elif endpoint == "programs":
                tasks.append(self.warm_programs(params))
            elif endpoint == "dados_prioritarios_estado_atual":
                tasks.append(self.warm_dados_prioritarios_estado_atual(params))
            elif endpoint.startswith("filters_"):
                tasks.append(self.warm_filters(endpoint, params))
        
        # Run all warming tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(
            "Cache warming completed",
            total_queries=len(tasks),
            successes=successes,
            failures=failures,
            elapsed_seconds=f"{elapsed:.2f}"
        )

# Global cache warmer instance
cache_warmer = CacheWarmer()

async def warm_cache_on_startup():
    """Function to be called on application startup"""
    try:
        await asyncio.sleep(2)  # Give services time to initialize
        await cache_warmer.warm_all()
    except Exception as e:
        logger.error("Cache warming failed", error=str(e))