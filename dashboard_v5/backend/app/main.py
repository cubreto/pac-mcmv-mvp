"""
MCMV Dashboard v5 - FastAPI Main Application
High-performance backend with materialized views and smart caching
"""

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from typing import Optional, List, Dict, Any
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from .config import settings
from .database import db_manager, get_database
from .models import KPIResponse, RegionalSummaryResponse, ProgramSummaryResponse, TemporalTrendsResponse, DataQualityResponse, DeliveryForecastResponse
from .cache import cache_manager
from .filters import FilterService

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('mcmv_dashboard_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('mcmv_dashboard_request_duration_seconds', 'Request duration', ['endpoint'])

app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=False,  # Set to False when allowing all origins
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware for collecting metrics and logging"""
    start_time = time.time()
    endpoint = request.url.path
    method = request.method
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(endpoint=endpoint).observe(time.time() - start_time)
        
        # Log request
        logger.info("Request completed",
                   method=method,
                   endpoint=endpoint,
                   status=status,
                   duration=f"{time.time() - start_time:.3f}s")
        
        return response
        
    except Exception as e:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
        logger.error("Request failed",
                    method=method,
                    endpoint=endpoint,
                    error=str(e),
                    duration=f"{time.time() - start_time:.3f}s")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting MCMV Dashboard v5",
               environment=settings.environment,
               api_version=settings.api.version)
    
    # Initialize database
    await db_manager.initialize()
    
    # Initialize cache
    await cache_manager.initialize()
    
    # Initialize filter service
    global filter_service
    filter_service = FilterService(db_manager)
    
    logger.info("Application startup completed successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down MCMV Dashboard v5")
    
    await db_manager.close()
    await cache_manager.close()
    
    logger.info("Application shutdown completed")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api.version,
        "environment": settings.environment,
        "timestamp": time.time()
    }

# Health check endpoint for API v5
@app.get("/api/v5/health")
async def health_check_v5():
    """Health check endpoint for API v5"""
    return {
        "status": "healthy",
        "version": settings.api.version,
        "environment": settings.environment,
        "timestamp": time.time()
    }

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.enable_prometheus:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ================================================
# KPI ENDPOINTS
# ================================================

@app.get(f"{settings.api.base_path}/kpis", response_model=KPIResponse)
async def get_kpis(
    programa: Optional[str] = Query(None, description="Program filter"),
    regiao: Optional[str] = Query(None, description="Region filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    state: Optional[str] = Query(None, description="State filter (UF)"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    database = Depends(get_database)
):
    """Get KPI data with smart caching and materialized view optimization"""
    
    cache_key = f"kpis:{programa or 'ALL'}:{regiao or 'ALL'}:{status or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('aggregated_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("KPIs served from cache",
                   programa=programa, regiao=regiao, status=status, state=state, municipality=municipality)
        return cached_result
    
    # Get from database
    start_time = time.time()
    
    try:
        data = await database.get_kpi_data(programa=programa, regiao=regiao, status=status, state=state, municipality=municipality)
        
        # Enhance with business rules
        result = KPIResponse(
            total_projetos=data['total_projetos'],
            total_uh_contratadas=data['total_uh_contratadas'],
            total_contratado=data['total_contratado'],
            total_investimento=data['total_investimento'],
            investimento_medio_por_uh=data['investimento_medio_por_uh'],
            percentual_execucao_medio=data['percentual_execucao_medio'],
            uh_em_execucao=data['uh_em_execucao'],
            uh_nao_iniciadas=data['uh_nao_iniciadas'],
            uh_concluidas=data['uh_concluidas'],
            projetos_alto_risco=data['projetos_alto_risco'],
            data_atualizacao=data['data_atualizacao'],
            metadata={
                "programa": programa,
                "regiao": regiao,
                "status": status,
                "state": state,
                "municipality": municipality,
                "execution_time": f"{time.time() - start_time:.3f}s",
                "source": "materialized_view",
                "cache_ttl": cache_ttl
            }
        )
        
        # Cache result
        await cache_manager.set(cache_key, result.dict(), expire=cache_ttl)
        
        logger.info("KPIs served from database",
                   programa=programa,
                   regiao=regiao,
                   status=status,
                   state=state,
                   municipality=municipality,
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return result
        
    except Exception as e:
        logger.error("Failed to get KPIs",
                    programa=programa, regiao=regiao, status=status, 
                    state=state, municipality=municipality, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve KPI data")

@app.get(f"{settings.api.base_path}/regional", response_model=RegionalSummaryResponse)
async def get_regional_summary(
    programa: Optional[str] = Query(None, description="Program filter"),
    database = Depends(get_database)
):
    """Get regional summary with materialized view optimization"""
    
    cache_key = f"regional:{programa or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('aggregated_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Regional summary served from cache", programa=programa)
        return cached_result
    
    start_time = time.time()
    
    try:
        data = await database.get_regional_summary(programa=programa)
        
        # Enhance with business rules
        regions_with_colors = []
        region_config = settings.business_rules.regions
        
        for region_data in data:
            region_name = region_data['regiao']
            color = region_config.get(region_name, {}).get('color', '#9E9E9E')
            
            regions_with_colors.append({
                **region_data,
                'color': color
            })
        
        result = RegionalSummaryResponse(
            data=regions_with_colors,
            metadata={
                "programa": programa,
                "execution_time": f"{time.time() - start_time:.3f}s",
                "source": "materialized_view",
                "regions_count": len(data),
                "cache_ttl": cache_ttl
            }
        )
        
        # Cache result
        await cache_manager.set(cache_key, result.dict(), expire=cache_ttl)
        
        logger.info("Regional summary served from database",
                   programa=programa,
                   regions_count=len(data),
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return result
        
    except Exception as e:
        logger.error("Failed to get regional summary", programa=programa, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve regional summary")

@app.get(f"{settings.api.base_path}/programs", response_model=ProgramSummaryResponse)
async def get_program_summary(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    programa: Optional[str] = Query(None, description="Program filter"),
    database = Depends(get_database)
):
    """Get program summary with financial breakdown and execution status"""
    
    # Create cache key with all filters
    filter_parts = [
        regiao or 'ALL',
        state or 'ALL', 
        municipality or 'ALL',
        status or 'ALL',
        programa or 'ALL'
    ]
    cache_key = f"programs:{'|'.join(filter_parts)}"
    cache_ttl = settings.business_rules.get_cache_ttl('summary_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Program summary served from cache", 
                   regiao=regiao, state=state, municipality=municipality)
        return cached_result
    
    try:
        start_time = time.time()
        data = await database.get_program_summary(
            regiao=regiao, 
            state=state, 
            municipality=municipality, 
            status=status, 
            programa=programa
        )
        
        # Add color coding for programs
        program_colors = {
            'FAR': '#2196F3',  # Blue
            'FDS': '#4CAF50',  # Green  
            'RURAL': '#FF9800'  # Orange
        }
        
        for item in data:
            item['color'] = program_colors.get(item['programa'], '#9E9E9E')
        
        execution_time = time.time() - start_time
        
        result = ProgramSummaryResponse(
            data=data,
            metadata={
                "regiao": regiao,
                "execution_time": f"{execution_time:.3f}s",
                "source": "mcmv_v2.projetos",
                "programs_count": len(data),
                "cache_ttl": cache_ttl
            }
        )
        
        # Cache the result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Program summary retrieved successfully",
                   regiao=regiao, programs_count=len(data), execution_time=f"{execution_time:.3f}s")
        
        return result
        
    except Exception as e:
        logger.error("Failed to get program summary", regiao=regiao, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve program summary")

@app.get(f"{settings.api.base_path}/temporal", response_model=TemporalTrendsResponse)
async def get_temporal_trends(
    programa: Optional[str] = Query(None, description="Program filter"),
    regiao: Optional[str] = Query(None, description="Region filter"),
    months: int = Query(24, description="Number of months to retrieve", ge=1, le=60),
    database = Depends(get_database)
):
    """Get temporal trends from materialized view"""
    
    cache_key = f"temporal:{programa or 'ALL'}:{regiao or 'ALL'}:{months}"
    cache_ttl = settings.business_rules.get_cache_ttl('detailed_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Temporal trends served from cache",
                   programa=programa, regiao=regiao, months=months)
        return cached_result
    
    start_time = time.time()
    
    try:
        data = await database.get_temporal_trends(
            programa=programa, regiao=regiao, months=months)
        
        result = TemporalTrendsResponse(
            data=data,
            metadata={
                "programa": programa,
                "regiao": regiao,
                "months": months,
                "execution_time": f"{time.time() - start_time:.3f}s",
                "data_points": len(data),
                "cache_ttl": cache_ttl
            }
        )
        
        # Cache result
        await cache_manager.set(cache_key, result.dict(), expire=cache_ttl)
        
        logger.info("Temporal trends served from database",
                   programa=programa, regiao=regiao, months=months,
                   data_points=len(data),
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return result
        
    except Exception as e:
        logger.error("Failed to get temporal trends",
                    programa=programa, regiao=regiao, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve temporal trends")

@app.get(f"{settings.api.base_path}/data-quality", response_model=DataQualityResponse)
async def get_data_quality_metrics(
    database = Depends(get_database)
):
    """Get data quality metrics"""
    
    cache_key = "data_quality:all"
    cache_ttl = settings.business_rules.get_cache_ttl('static_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Data quality metrics served from cache")
        return cached_result
    
    start_time = time.time()
    
    try:
        data = await database.get_data_quality_metrics()
        
        # Calculate overall quality score
        if data:
            overall_score = sum(item['data_quality_score'] for item in data) / len(data)
        else:
            overall_score = 0.0
        
        result = DataQualityResponse(
            programs=data,
            overall_score=overall_score,
            minimum_acceptable_score=settings.business_rules.data_quality.get('minimum_score', 85.0),
            metadata={
                "execution_time": f"{time.time() - start_time:.3f}s",
                "programs_analyzed": len(data),
                "cache_ttl": cache_ttl
            }
        )
        
        # Cache result
        await cache_manager.set(cache_key, result.dict(), expire=cache_ttl)
        
        logger.info("Data quality metrics served from database",
                   programs_count=len(data),
                   overall_score=overall_score,
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return result
        
    except Exception as e:
        logger.error("Failed to get data quality metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve data quality metrics")

@app.get(f"{settings.api.base_path}/delivery-forecast", response_model=DeliveryForecastResponse)
async def get_delivery_forecast(
    programa: Optional[str] = Query(None, description="Program filter"),
    database = Depends(get_database)
):
    """Get delivery forecast data mimicking v4 behavior"""
    
    cache_key = f"delivery_forecast:{programa or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('detailed_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Delivery forecast served from cache", programa=programa)
        return cached_result
    
    start_time = time.time()
    
    try:
        data = await database.get_delivery_forecast(programa=programa)
        
        # Calculate summary metrics like v4
        if data:
            total_months = len(set(item['ano_mes'] for item in data))
            total_uh_forecast = sum(item['numero_uhs'] for item in data)
            
            # Find peak month
            monthly_totals = {}
            for item in data:
                if item['ano_mes'] not in monthly_totals:
                    monthly_totals[item['ano_mes']] = 0
                monthly_totals[item['ano_mes']] += item['numero_uhs']
            
            peak_month = max(monthly_totals.items(), key=lambda x: x[1])[0] if monthly_totals else "2024-01"
        else:
            total_months = 0
            total_uh_forecast = 0
            peak_month = "2024-01"
        
        result = DeliveryForecastResponse(
            data=data,
            summary={
                "total_months": total_months,
                "total_uh_forecast": total_uh_forecast,
                "peak_month": peak_month,
                "programs_included": list(set(item['programa'] for item in data)) if data else []
            },
            metadata={
                "programa": programa,
                "execution_time": f"{time.time() - start_time:.3f}s",
                "data_points": len(data),
                "cache_ttl": cache_ttl
            }
        )
        
        # Cache result
        await cache_manager.set(cache_key, result.dict(), expire=cache_ttl)
        
        logger.info("Delivery forecast served from database",
                   programa=programa,
                   data_points=len(data),
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return result
        
    except Exception as e:
        logger.error("Failed to get delivery forecast", programa=programa, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve delivery forecast")

# ================================================
# FILTER ENDPOINTS
# ================================================

@app.get(f"{settings.api.base_path}/filters/regions")
async def get_regions():
    """Get all available regions with project counts"""
    
    cache_key = "filters:regions"
    cache_ttl = settings.business_rules.get_cache_ttl('static_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Regions served from cache")
        return cached_result
    
    try:
        regions = await filter_service.get_regions()
        
        result = {
            "data": regions,
            "metadata": {
                "count": len(regions),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Regions served from database", count=len(regions))
        return result
        
    except Exception as e:
        logger.error("Failed to get regions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve regions")

@app.get(f"{settings.api.base_path}/filters/states")
async def get_states(
    region: Optional[str] = Query(None, description="Filter by region")
):
    """Get states, optionally filtered by region"""
    
    cache_key = f"filters:states:{region or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('static_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("States served from cache", region=region)
        return cached_result
    
    try:
        states = await filter_service.get_states(region=region)
        
        result = {
            "data": states,
            "metadata": {
                "region": region,
                "count": len(states),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("States served from database", region=region, count=len(states))
        return result
        
    except Exception as e:
        logger.error("Failed to get states", region=region, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve states")

@app.get(f"{settings.api.base_path}/filters/municipalities")
async def get_municipalities(
    region: Optional[str] = Query(None, description="Filter by region"),
    state: Optional[str] = Query(None, description="Filter by state")
):
    """Get municipalities, optionally filtered by region and/or state"""
    
    cache_key = f"filters:municipalities:{region or 'ALL'}:{state or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('detailed_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Municipalities served from cache", region=region, state=state)
        return cached_result
    
    try:
        municipalities = await filter_service.get_municipalities(region=region, state=state)
        
        result = {
            "data": municipalities,
            "metadata": {
                "region": region,
                "state": state,
                "count": len(municipalities),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Municipalities served from database", 
                   region=region, state=state, count=len(municipalities))
        return result
        
    except Exception as e:
        logger.error("Failed to get municipalities", 
                    region=region, state=state, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve municipalities")

@app.get(f"{settings.api.base_path}/filters/status")
async def get_status_options():
    """Get available status options with project counts"""
    
    cache_key = "filters:status"
    cache_ttl = settings.business_rules.get_cache_ttl('static_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Status options served from cache")
        return cached_result
    
    try:
        status_options = await filter_service.get_status_options()
        
        result = {
            "data": status_options,
            "metadata": {
                "count": len(status_options),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Status options served from database", count=len(status_options))
        return result
        
    except Exception as e:
        logger.error("Failed to get status options", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve status options")

@app.get(f"{settings.api.base_path}/filters/programs")
async def get_programs(
    region: Optional[str] = Query(None, description="Filter by region"),
    state: Optional[str] = Query(None, description="Filter by state"),
    municipality: Optional[str] = Query(None, description="Filter by municipality")
):
    """Get programs with optional geographic filters"""
    
    cache_key = f"filters:programs:{region or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('detailed_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Programs served from cache", 
                   region=region, state=state, municipality=municipality)
        return cached_result
    
    try:
        programs = await filter_service.get_programs(
            region=region, state=state, municipality=municipality)
        
        result = {
            "data": programs,
            "metadata": {
                "region": region,
                "state": state,
                "municipality": municipality,
                "count": len(programs),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Programs served from database", 
                   region=region, state=state, municipality=municipality, 
                   count=len(programs))
        return result
        
    except Exception as e:
        logger.error("Failed to get programs", 
                    region=region, state=state, municipality=municipality, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve programs")

@app.get(f"{settings.api.base_path}/filters/summary")
async def get_filter_summary(
    region: Optional[str] = Query(None, description="Filter by region"),
    state: Optional[str] = Query(None, description="Filter by state"),
    municipality: Optional[str] = Query(None, description="Filter by municipality"),
    status: Optional[str] = Query(None, description="Filter by status"),
    programa: Optional[str] = Query(None, description="Filter by program")
):
    """Get summary statistics for filter combination"""
    
    filters = {
        'region': region,
        'state': state,
        'municipality': municipality,
        'status': status,
        'programa': programa
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    cache_key = f"filters:summary:{':'.join(f'{k}={v}' for k, v in sorted(filters.items()))}"
    cache_ttl = settings.business_rules.get_cache_ttl('detailed_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Filter summary served from cache", filters=filters)
        return cached_result
    
    try:
        summary = await filter_service.get_filter_summary(filters)
        
        result = {
            "data": summary,
            "filters": filters,
            "metadata": {
                "filters_applied": len(filters),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Filter summary served from database", filters=filters)
        return result
        
    except Exception as e:
        logger.error("Failed to get filter summary", filters=filters, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve filter summary")

# ================================================
# ADMIN ENDPOINTS
# ================================================

# Background task for cache warming
@app.post(f"{settings.api.base_path}/admin/warm-cache")
async def warm_cache(background_tasks: BackgroundTasks):
    """Warm up cache with commonly requested data"""
    
    if not settings.is_development:
        raise HTTPException(status_code=404, detail="Admin endpoints disabled in production")
    
    background_tasks.add_task(_warm_cache_task)
    return {"message": "Cache warming started"}

async def _warm_cache_task():
    """Background task to warm up cache"""
    logger.info("Starting cache warming")
    
    programs = ['RURAL', 'FAR', 'FDS']
    regions = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
    
    try:
        # Warm up KPIs
        for programa in [None] + programs:
            await get_kpis(programa=programa, database=db_manager)
            
        # Warm up regional summaries
        for programa in [None] + programs:
            await get_regional_summary(programa=programa, database=db_manager)
            
        logger.info("Cache warming completed successfully")
        
    except Exception as e:
        logger.error("Cache warming failed", error=str(e))

# ================================================
# RURAL-SPECIFIC ENDPOINTS
# ================================================

@app.get(f"{settings.api.base_path}/rural/charts/region-status")
async def get_rural_region_status_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get RURAL UH by Region and Status chart data"""
    
    cache_key = f"rural:region_status:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'RURAL'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (RURAL-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            CASE 
                WHEN sg_uf IN ('AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO') THEN 'Norte'
                WHEN sg_uf IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Nordeste'
                WHEN sg_uf IN ('DF', 'GO', 'MT', 'MS') THEN 'Centro-Oeste'
                WHEN sg_uf IN ('ES', 'MG', 'RJ', 'SP') THEN 'Sudeste'
                WHEN sg_uf IN ('PR', 'RS', 'SC') THEN 'Sul'
                ELSE 'Outros'
            END as regiao,
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END as situacao_obra,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY 
            CASE 
                WHEN sg_uf IN ('AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO') THEN 'Norte'
                WHEN sg_uf IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Nordeste'
                WHEN sg_uf IN ('DF', 'GO', 'MT', 'MS') THEN 'Centro-Oeste'
                WHEN sg_uf IN ('ES', 'MG', 'RJ', 'SP') THEN 'Sudeste'
                WHEN sg_uf IN ('PR', 'RS', 'SC') THEN 'Sul'
                ELSE 'Outros'
            END,
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END
        ORDER BY regiao, situacao_obra
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "RURAL",
                "chart_type": "region_status",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get RURAL region-status chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve RURAL region-status chart data")

@app.get(f"{settings.api.base_path}/rural/charts/status-donut")
async def get_rural_status_donut_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get RURAL UH by Status donut chart data"""
    
    cache_key = f"rural:status_donut:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'RURAL'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (RURAL-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END as status,
            SUM(uh_contratadas) as total_uh,
            COUNT(DISTINCT nu_apf) as project_count
        FROM mcmv_v2.projetos 
        WHERE {where_clause}
        GROUP BY CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END
        ORDER BY total_uh DESC
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "RURAL",
                "chart_type": "status_donut",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get RURAL status donut chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve RURAL status donut chart data")

@app.get(f"{settings.api.base_path}/rural/charts/timeline")
async def get_rural_timeline_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get RURAL delivery timeline forecast chart data"""
    
    cache_key = f"rural:timeline:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause  
        where_conditions = ["programa = 'RURAL'", "dt_previsao_conclusao_obra IS NOT NULL"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to progress condition
            status_conditions = {
                'Não Iniciada': 'pc_obra_realizada = 0',
                'Em Execução': 'pc_obra_realizada BETWEEN 1 AND 99',
                'Concluída': 'pc_obra_realizada = 100',
                'Indefinida': 'pc_obra_realizada IS NULL'
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            DATE_TRUNC('month', dt_previsao_conclusao_obra) as delivery_month,
            SUM(uh_contratadas) as total_uh,
            COUNT(DISTINCT nu_apf) as project_count
        FROM mcmv_v2.projetos 
        WHERE {where_clause}
        GROUP BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
        ORDER BY delivery_month
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "RURAL",
                "chart_type": "timeline",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get RURAL timeline chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve RURAL timeline chart data")

@app.get(f"{settings.api.base_path}/rural/financial-table")
async def get_rural_financial_table(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get RURAL financial breakdown by municipality"""
    
    cache_key = f"rural:financial_table:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('tables')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'RURAL'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to progress condition
            status_conditions = {
                'Não Iniciada': 'pc_obra_realizada = 0',
                'Em Execução': 'pc_obra_realizada BETWEEN 1 AND 99',
                'Concluída': 'pc_obra_realizada = 100',
                'Indefinida': 'pc_obra_realizada IS NULL'
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            sg_uf as uf,
            no_municipio as municipio,
            COUNT(DISTINCT nu_apf) as total_projetos,
            SUM(uh_contratadas) as total_uh_contratadas,
            SUM(COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) as total_valor_contratado,
            SUM(COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) as total_investimento,
            ROUND(AVG((COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) / NULLIF(uh_contratadas, 0)), 2) as investimento_medio_uh
        FROM mcmv_v2.projetos 
        WHERE {where_clause}
        GROUP BY sg_uf, no_municipio
        ORDER BY sg_uf, no_municipio, total_valor_contratado DESC
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "RURAL",
                "table_type": "financial_breakdown",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get RURAL financial table", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve RURAL financial table data")

# ================================================
# FAR-SPECIFIC ENDPOINTS
# ================================================

@app.get(f"{settings.api.base_path}/far/charts/region-status")
async def get_far_region_status_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FAR UH by Region and Status chart data"""
    
    cache_key = f"far:region_status:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FAR'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (FAR-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            CASE 
                WHEN sg_uf IN ('AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO') THEN 'Norte'
                WHEN sg_uf IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Nordeste'
                WHEN sg_uf IN ('DF', 'GO', 'MT', 'MS') THEN 'Centro-Oeste'
                WHEN sg_uf IN ('ES', 'MG', 'RJ', 'SP') THEN 'Sudeste'
                WHEN sg_uf IN ('PR', 'RS', 'SC') THEN 'Sul'
                ELSE 'Outros'
            END as regiao,
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END as situacao_obra,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY 
            CASE 
                WHEN sg_uf IN ('AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO') THEN 'Norte'
                WHEN sg_uf IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Nordeste'
                WHEN sg_uf IN ('DF', 'GO', 'MT', 'MS') THEN 'Centro-Oeste'
                WHEN sg_uf IN ('ES', 'MG', 'RJ', 'SP') THEN 'Sudeste'
                WHEN sg_uf IN ('PR', 'RS', 'SC') THEN 'Sul'
                ELSE 'Outros'
            END,
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END
        ORDER BY regiao, situacao_obra
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FAR",
                "chart_type": "region_status",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FAR region-status chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FAR region-status chart data")

@app.get(f"{settings.api.base_path}/far/charts/status-donut")
async def get_far_status_donut_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FAR UH by Status donut chart data"""
    
    cache_key = f"far:status_donut:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FAR'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (FAR-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END as status,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY 
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END
        ORDER BY total_uh DESC
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FAR",
                "chart_type": "status_donut",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FAR status donut chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FAR status donut chart data")

@app.get(f"{settings.api.base_path}/far/charts/timeline")
async def get_far_timeline_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FAR delivery timeline chart data"""
    
    cache_key = f"far:timeline:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FAR'", "dt_previsao_conclusao_obra IS NOT NULL"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to progress condition
            status_conditions = {
                'Não Iniciada': 'pc_obra_realizada = 0',
                'Em Execução': 'pc_obra_realizada BETWEEN 1 AND 99',
                'Concluída': 'pc_obra_realizada = 100',
                'Indefinida': 'pc_obra_realizada IS NULL'
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            DATE_TRUNC('month', dt_previsao_conclusao_obra) as delivery_month,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
        ORDER BY delivery_month
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FAR",
                "chart_type": "timeline",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FAR timeline chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FAR timeline chart data")

@app.get(f"{settings.api.base_path}/far/financial-table")
async def get_far_financial_table(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FAR financial breakdown by municipality"""
    
    cache_key = f"far:financial_table:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('tables')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FAR'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to progress condition
            status_conditions = {
                'Não Iniciada': 'pc_obra_realizada = 0',
                'Em Execução': 'pc_obra_realizada BETWEEN 1 AND 99',
                'Concluída': 'pc_obra_realizada = 100',
                'Indefinida': 'pc_obra_realizada IS NULL'
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            sg_uf as uf,
            no_municipio as municipio,
            COUNT(DISTINCT nu_apf) as total_projetos,
            SUM(uh_contratadas) as total_uh_contratadas,
            SUM(COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) as total_valor_contratado,
            SUM(COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) as total_investimento,
            ROUND(AVG((COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) / NULLIF(uh_contratadas, 0)), 2) as investimento_medio_uh
        FROM mcmv_v2.projetos 
        WHERE {where_clause}
        GROUP BY sg_uf, no_municipio
        ORDER BY sg_uf, no_municipio, total_valor_contratado DESC
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FAR",
                "table_type": "financial_breakdown",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FAR financial table", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FAR financial table data")

# ================================================
# FDS-SPECIFIC ENDPOINTS
# ================================================

@app.get(f"{settings.api.base_path}/fds/charts/region-status")
async def get_fds_region_status_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FDS UH by Region and Status chart data"""
    
    cache_key = f"fds:region_status:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FDS'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (FDS-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            CASE 
                WHEN sg_uf IN ('AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO') THEN 'Norte'
                WHEN sg_uf IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Nordeste'
                WHEN sg_uf IN ('DF', 'GO', 'MT', 'MS') THEN 'Centro-Oeste'
                WHEN sg_uf IN ('ES', 'MG', 'RJ', 'SP') THEN 'Sudeste'
                WHEN sg_uf IN ('PR', 'RS', 'SC') THEN 'Sul'
                ELSE 'Outros'
            END as regiao,
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END as situacao_obra,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY 
            CASE 
                WHEN sg_uf IN ('AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO') THEN 'Norte'
                WHEN sg_uf IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Nordeste'
                WHEN sg_uf IN ('DF', 'GO', 'MT', 'MS') THEN 'Centro-Oeste'
                WHEN sg_uf IN ('ES', 'MG', 'RJ', 'SP') THEN 'Sudeste'
                WHEN sg_uf IN ('PR', 'RS', 'SC') THEN 'Sul'
                ELSE 'Outros'
            END,
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END
        ORDER BY regiao, situacao_obra
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FDS",
                "chart_type": "region_status",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FDS region-status chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FDS region-status chart data")

@app.get(f"{settings.api.base_path}/fds/charts/status-donut")
async def get_fds_status_donut_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FDS UH by Status donut chart data"""
    
    cache_key = f"fds:status_donut:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FDS'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (FDS-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END as status,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY 
            CASE co_situacao_operacao
                WHEN '1' THEN 'Em Andamento'
                WHEN '2' THEN 'Atrasada'
                WHEN '3' THEN 'Paralisada'
                WHEN '11' THEN 'Normal'
                WHEN '16' THEN 'Outras'
                ELSE 'Não Iniciada'
            END
        ORDER BY total_uh DESC
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FDS",
                "chart_type": "status_donut",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FDS status donut chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FDS status donut chart data")

@app.get(f"{settings.api.base_path}/fds/charts/timeline")
async def get_fds_timeline_chart(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FDS delivery timeline chart data"""
    
    cache_key = f"fds:timeline:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('charts')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FDS'", "dt_previsao_conclusao_obra IS NOT NULL"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (FDS-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            DATE_TRUNC('month', dt_previsao_conclusao_obra) as delivery_month,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
        ORDER BY delivery_month
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FDS",
                "chart_type": "timeline",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FDS timeline chart", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FDS timeline chart data")

@app.get(f"{settings.api.base_path}/fds/financial-table")
async def get_fds_financial_table(
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    database = Depends(get_database)
):
    """Get FDS financial breakdown by municipality"""
    
    cache_key = f"fds:financial_table:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('tables')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause
        where_conditions = ["programa = 'FDS'"]
        params = {}
        
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
                states_list = "','".join(region_states[regiao])
                where_conditions.append(f"sg_uf IN ('{states_list}')")
        if state:
            where_conditions.append("sg_uf = :state")
            params['state'] = state
        if municipality:
            where_conditions.append("no_municipio = :municipality")
            params['municipality'] = municipality
        if status:
            # Map status to co_situacao_operacao condition (FDS-specific)
            status_conditions = {
                'Em Andamento': "co_situacao_operacao = '1'",
                'Atrasada': "co_situacao_operacao = '2'", 
                'Paralisada': "co_situacao_operacao = '3'",
                'Normal': "co_situacao_operacao = '11'",
                'Outras': "co_situacao_operacao = '16'",
                'Não Iniciada': "co_situacao_operacao NOT IN ('1', '2', '3', '11', '16')"
            }
            if status in status_conditions:
                where_conditions.append(f"({status_conditions[status]})")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            sg_uf as uf,
            no_municipio as municipio,
            COUNT(DISTINCT nu_apf) as total_projetos,
            SUM(uh_contratadas) as total_uh_contratadas,
            SUM(COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) as total_valor_contratado,
            SUM(COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) as total_investimento,
            ROUND(AVG((COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)) / NULLIF(uh_contratadas, 0)), 2) as investimento_medio_uh
        FROM mcmv_v2.projetos 
        WHERE {where_clause}
        GROUP BY sg_uf, no_municipio
        ORDER BY sg_uf, no_municipio, total_valor_contratado DESC
        """
        
        data = await database.get_chart_data(query, params)
        
        result = {
            "data": data,
            "metadata": {
                "programa": "FDS",
                "table_type": "financial_breakdown",
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get FDS financial table", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve FDS financial table data")

# ================================================
# DADOS PRIORITÁRIOS ENDPOINT  
# ================================================

@app.get(f"{settings.api.base_path}/dados-prioritarios")
async def get_dados_prioritarios(
    ano_contratacao: Optional[int] = Query(None, description="Contract year filter (EXTRACT(year FROM dt_contratacao))"),
    mes_movimento: Optional[int] = Query(None, description="Movement month filter (1-12)"),
    ano_movimento: Optional[int] = Query(None, description="Movement year filter"),
    situacao_empreendimento: Optional[str] = Query(None, description="Project status filter"),
    database = Depends(get_database)
):
    """Get dados prioritarios table data with programa and situacao_empreendimento grouping"""
    
    # Create cache key including all filter parameters
    filters_str = f"{ano_contratacao or 'ALL'}:{mes_movimento or 'ALL'}:{ano_movimento or 'ALL'}:{situacao_empreendimento or 'ALL'}"
    cache_key = f"dados_prioritarios:table:{filters_str}"
    cache_ttl = settings.business_rules.get_cache_ttl('tables')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause - no fl_dados_prioritarios needed as we're querying the dedicated table
        where_conditions = ["1=1"]
        params = {}
        
        if ano_contratacao:
            where_conditions.append("EXTRACT(year FROM data_contratacao) = :ano_contratacao")
            params["ano_contratacao"] = ano_contratacao
            
        if mes_movimento:
            where_conditions.append("EXTRACT(month FROM data_movimento) = :mes_movimento")
            params["mes_movimento"] = mes_movimento
            
        if ano_movimento:
            where_conditions.append("EXTRACT(year FROM data_movimento) = :ano_movimento")
            params["ano_movimento"] = ano_movimento
            
        if situacao_empreendimento:
            where_conditions.append("situacao_empreendimento = :situacao_empreendimento")
            params["situacao_empreendimento"] = situacao_empreendimento
        
        where_clause = " AND ".join(where_conditions)
        
        # Query for dados prioritarios table
        # Using corrected data from Excel source with proper modalidade mapping
        # Count rows, not distinct APFs, to match expected output
        query = f"""
        SELECT 
            modalidade as programa,
            situacao_empreendimento,
            COUNT(*) as projetos,
            SUM(COALESCE(uh_contratadas, 0))::INTEGER as uh_contratadas,
            SUM(COALESCE(uh_entregues, 0))::INTEGER as uh_entregues,
            CASE 
                WHEN SUM(COALESCE(uh_contratadas, 0)) > 0 
                THEN ROUND((SUM(COALESCE(uh_entregues, 0))::NUMERIC / SUM(COALESCE(uh_contratadas, 0))::NUMERIC) * 100, 2)
                ELSE 0
            END as percentual_entregues,
            SUM(COALESCE(uh_vigentes, 0))::INTEGER as uh_vigentes
        FROM mcmv_v2.dados_prioritarios 
        WHERE {where_clause}
        GROUP BY modalidade, situacao_empreendimento
        ORDER BY programa, situacao_empreendimento
        """
        
        data = await database.get_chart_data(query, params)
        
        # Calculate totals for summary
        total_projetos = sum(row.get('projetos', 0) for row in data)
        total_uh_contratadas = sum(row.get('uh_contratadas', 0) for row in data)
        total_uh_entregues = sum(row.get('uh_entregues', 0) for row in data)
        total_uh_vigentes = sum(row.get('uh_vigentes', 0) for row in data)
        
        # Calculate overall percentage
        overall_percentual = round((total_uh_entregues / total_uh_contratadas * 100), 2) if total_uh_contratadas > 0 else 0
        
        result = {
            "data": data,
            "summary": {
                "total_projetos": total_projetos,
                "total_uh_contratadas": total_uh_contratadas,
                "total_uh_entregues": total_uh_entregues,
                "total_uh_vigentes": total_uh_vigentes,
                "overall_percentual_entregues": overall_percentual
            },
            "metadata": {
                "source": "dados_prioritarios",
                "filters": {
                    "ano_contratacao": ano_contratacao,
                    "mes_movimento": mes_movimento,
                    "ano_movimento": ano_movimento
                },
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get dados prioritarios data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dados prioritarios data")

# ================================================
# DADOS PRIORITÁRIOS FILTER OPTIONS
# ================================================

@app.get(f"{settings.api.base_path}/dados-prioritarios/filters")
async def get_dados_prioritarios_filters(database = Depends(get_database)):
    """Get available filter options for dados prioritarios"""
    
    cache_key = "dados_prioritarios:filters"
    cache_ttl = settings.business_rules.get_cache_ttl('filters')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get available years from contract dates
        anos_query = """
        SELECT DISTINCT EXTRACT(year FROM data_contratacao) as ano
        FROM mcmv_v2.dados_prioritarios 
        WHERE data_contratacao IS NOT NULL
        ORDER BY ano DESC
        """
        
        # Get available months/years from movement dates  
        movimento_query = """
        SELECT DISTINCT 
            EXTRACT(month FROM data_movimento) as mes,
            EXTRACT(year FROM data_movimento) as ano
        FROM mcmv_v2.dados_prioritarios 
        WHERE data_movimento IS NOT NULL
        ORDER BY ano DESC, mes ASC
        """
        
        # Get available situações do empreendimento
        situacoes_query = """
        SELECT DISTINCT situacao_empreendimento
        FROM mcmv_v2.dados_prioritarios 
        WHERE situacao_empreendimento IS NOT NULL
        ORDER BY situacao_empreendimento ASC
        """
        
        anos_data = await database.get_chart_data(anos_query, {})
        movimento_data = await database.get_chart_data(movimento_query, {})
        situacoes_data = await database.get_chart_data(situacoes_query, {})
        
        # Process movement data into grouped format
        movimento_options = {}
        for row in movimento_data:
            ano = int(row['ano'])
            mes = int(row['mes'])
            if ano not in movimento_options:
                movimento_options[ano] = []
            if mes not in movimento_options[ano]:
                movimento_options[ano].append(mes)
        
        # Sort months within each year
        for ano in movimento_options:
            movimento_options[ano].sort()
        
        result = {
            "anos_contratacao": [int(row['ano']) for row in anos_data],
            "movimento_dates": movimento_options,
            "situacoes_empreendimento": [row['situacao_empreendimento'] for row in situacoes_data],
            "metadata": {
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get dados prioritarios filters", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dados prioritarios filter options")

# Configuration endpoint
@app.get(f"{settings.api.base_path}/config")
async def get_configuration():
    """Get frontend configuration from business rules"""
    
    return {
        "programs": settings.business_rules.programs,
        "status_definitions": settings.business_rules.status_definitions,
        "regions": settings.business_rules.regions,
        "charts": settings.business_rules.charts,
        "kpis": settings.business_rules.kpis,
        "api_version": settings.api.version,
        "performance": {
            "cache_ttl": settings.business_rules.performance.get('cache_ttl', {}),
            "frontend": settings.business_rules.performance.get('frontend', {})
        }
    }