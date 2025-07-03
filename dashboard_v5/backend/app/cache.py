"""
MCMV Dashboard v5 - Smart Cache Manager
Redis-based caching with intelligent TTL and warming strategies
"""

import redis.asyncio as redis
import json
import structlog
from typing import Any, Optional, Dict, List
import time
import hashlib
from datetime import datetime, timedelta

from .config import settings

logger = structlog.get_logger()

class CacheManager:
    """Smart cache manager with Redis backend"""
    
    def __init__(self):
        self.redis_client = None
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis.url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("Cache manager initialized successfully",
                       redis_url=settings.redis.url.split('@')[-1])  # Hide password
                       
        except Exception as e:
            logger.error("Failed to initialize cache manager", error=str(e))
            # Continue without cache if Redis is unavailable
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic deserialization"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._normalize_key(key)
            start_time = time.time()
            
            value = await self.redis_client.get(cache_key)
            
            if value is not None:
                self._cache_stats['hits'] += 1
                retrieval_time = time.time() - start_time
                
                # Deserialize JSON
                result = json.loads(value)
                
                logger.debug("Cache hit",
                           key=cache_key,
                           retrieval_time=f"{retrieval_time:.3f}s")
                
                return result
            else:
                self._cache_stats['misses'] += 1
                logger.debug("Cache miss", key=cache_key)
                return None
                
        except Exception as e:
            logger.error("Cache get failed", key=key, error=str(e))
            self._cache_stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache with automatic serialization"""
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._normalize_key(key)
            start_time = time.time()
            
            # Serialize to JSON
            serialized_value = json.dumps(value, default=self._json_serializer)
            
            # Set with optional expiration
            if expire:
                await self.redis_client.setex(cache_key, expire, serialized_value)
            else:
                await self.redis_client.set(cache_key, serialized_value)
            
            self._cache_stats['sets'] += 1
            storage_time = time.time() - start_time
            
            logger.debug("Cache set",
                        key=cache_key,
                        expire=expire,
                        storage_time=f"{storage_time:.3f}s")
            
            return True
            
        except Exception as e:
            logger.error("Cache set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._normalize_key(key)
            result = await self.redis_client.delete(cache_key)
            
            if result:
                self._cache_stats['deletes'] += 1
                logger.debug("Cache delete", key=cache_key)
            
            return bool(result)
            
        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
            
        try:
            normalized_pattern = self._normalize_key(pattern)
            keys = await self.redis_client.keys(normalized_pattern)
            
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                self._cache_stats['deletes'] += deleted_count
                
                logger.info("Cache pattern delete",
                          pattern=normalized_pattern,
                          deleted_count=deleted_count)
                
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error("Cache pattern delete failed", pattern=pattern, error=str(e))
            return 0
    
    async def invalidate_program_cache(self, programa: str):
        """Invalidate all cache entries for a specific program"""
        patterns = [
            f"kpis:{programa}:*",
            f"regional:{programa}:*",
            f"temporal:{programa}:*",
            f"kpis:ALL:*",  # Also invalidate aggregated data
            f"regional:ALL:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info("Program cache invalidated",
                   programa=programa,
                   total_deleted=total_deleted)
        
        return total_deleted
    
    async def warm_cache(self, endpoints_to_warm: Optional[List[str]] = None):
        """Warm cache with commonly requested data"""
        if not self.redis_client:
            logger.warning("Cache warming skipped - Redis not available")
            return
        
        logger.info("Starting cache warming")
        start_time = time.time()
        
        programs = ['RURAL', 'FAR', 'FDS']
        regions = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
        
        warmed_keys = 0
        
        try:
            # Warm KPIs
            if not endpoints_to_warm or 'kpis' in endpoints_to_warm:
                # Global KPIs
                await self._warm_kpis(None, None)
                warmed_keys += 1
                
                # Program-specific KPIs
                for programa in programs:
                    await self._warm_kpis(programa, None)
                    warmed_keys += 1
                
                # Region-specific KPIs
                for regiao in regions:
                    await self._warm_kpis(None, regiao)
                    warmed_keys += 1
            
            # Warm regional summaries
            if not endpoints_to_warm or 'regional' in endpoints_to_warm:
                # Global regional summary
                await self._warm_regional(None)
                warmed_keys += 1
                
                # Program-specific regional summaries
                for programa in programs:
                    await self._warm_regional(programa)
                    warmed_keys += 1
            
            warm_time = time.time() - start_time
            
            logger.info("Cache warming completed",
                       warmed_keys=warmed_keys,
                       warm_time=f"{warm_time:.3f}s")
            
        except Exception as e:
            logger.error("Cache warming failed", error=str(e))
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self._cache_stats.copy()
        
        if self.redis_client:
            try:
                # Add Redis info
                redis_info = await self.redis_client.info()
                stats.update({
                    'redis_connected': True,
                    'redis_memory_used': redis_info.get('used_memory_human', 'Unknown'),
                    'redis_keys_count': await self.redis_client.dbsize(),
                    'redis_uptime': redis_info.get('uptime_in_seconds', 0)
                })
            except Exception as e:
                stats['redis_connected'] = False
                stats['redis_error'] = str(e)
        else:
            stats['redis_connected'] = False
        
        # Calculate hit rate
        total_requests = stats['hits'] + stats['misses']
        if total_requests > 0:
            stats['hit_rate'] = stats['hits'] / total_requests
        else:
            stats['hit_rate'] = 0.0
        
        return stats
    
    async def _warm_kpis(self, programa: Optional[str], regiao: Optional[str]):
        """Warm KPI cache entry"""
        cache_key = f"kpis:{programa or 'ALL'}:{regiao or 'ALL'}:ALL"
        
        # Check if already cached
        if await self.get(cache_key):
            return
        
        # This would normally call the actual KPI function
        # For now, we'll just set a placeholder to reserve the key
        placeholder = {
            'warming': True,
            'timestamp': datetime.now().isoformat(),
            'programa': programa,
            'regiao': regiao
        }
        
        ttl = settings.business_rules.get_cache_ttl('aggregated_data')
        await self.set(cache_key, placeholder, expire=ttl)
    
    async def _warm_regional(self, programa: Optional[str]):
        """Warm regional summary cache entry"""
        cache_key = f"regional:{programa or 'ALL'}"
        
        # Check if already cached
        if await self.get(cache_key):
            return
        
        # Placeholder for warming
        placeholder = {
            'warming': True,
            'timestamp': datetime.now().isoformat(),
            'programa': programa
        }
        
        ttl = settings.business_rules.get_cache_ttl('aggregated_data')
        await self.set(cache_key, placeholder, expire=ttl)
    
    def _normalize_key(self, key: str) -> str:
        """Normalize cache key with prefix"""
        prefix = f"mcmv_v5:{settings.environment}"
        return f"{prefix}:{key}"
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Cache manager closed")

# Global cache manager instance
cache_manager = CacheManager()