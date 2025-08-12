"""
MCMV Dashboard v5 - FastAPI Main Application
High-performance backend with materialized views and smart caching
"""

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import structlog
import time
import asyncio
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import json
import csv
import io
import pandas as pd
from io import BytesIO

from .config import settings
from .database import db_manager, get_database
from .models import KPIResponse, RegionalSummaryResponse, ProgramSummaryResponse, TemporalTrendsResponse, DataQualityResponse, DeliveryForecastResponse
from .cache import cache_manager
from .filters import FilterService
from .data_quality_service import DataQualityService
from .etl_quality_service import ETLQualityService
from .cache_warmer import warm_cache_on_startup

logger = structlog.get_logger()

def decimal_to_float(obj):
    """Convert Decimal and date objects to JSON-serializable types"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

# Prometheus metrics
REQUEST_COUNT = Counter('mcmv_dashboard_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('mcmv_dashboard_request_duration_seconds', 'Request duration', ['endpoint'])

app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    docs_url="/docs",  # Temporarily enabled for API exploration
    redoc_url="/redoc"  # Temporarily enabled for API exploration
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
    
    # Initialize data quality service
    global data_quality_service
    data_quality_service = DataQualityService(db_manager)
    
    # Start cache warming in background
    asyncio.create_task(warm_cache_on_startup())
    
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
    tipo: Optional[str] = Query(None, description="RURAL tipo filter"),
    modalidade_proposta: Optional[str] = Query(None, description="RURAL modalidade proposta filter"),
    database = Depends(get_database)
):
    """Get KPI data with smart caching and materialized view optimization"""
    
    cache_key = f"kpis:{programa or 'ALL'}:{regiao or 'ALL'}:{status or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{tipo or 'ALL'}:{modalidade_proposta or 'ALL'}"
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
        data = await database.get_kpi_data(programa=programa, regiao=regiao, status=status, state=state, municipality=municipality, tipo=tipo, modalidade_proposta=modalidade_proposta)
        
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
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter (UF)"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    database = Depends(get_database)
):
    """Get regional summary with materialized view optimization"""
    
    # Create cache key with all filters
    filters = {
        "programa": programa,
        "regiao": regiao,
        "state": state,
        "municipality": municipality
    }
    # Filter out None values for cache key
    active_filters = {k: v for k, v in filters.items() if v is not None}
    cache_key = f"regional:{':'.join(f'{k}={v}' for k, v in active_filters.items()) or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('aggregated_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Regional summary served from cache", **active_filters)
        # Ensure cached result is in the correct format
        if isinstance(cached_result, list):
            # Fix legacy cache format
            return RegionalSummaryResponse(
                data=cached_result,
                metadata={
                    "programa": programa,
                    "source": "cache",
                    "regions_count": len(cached_result),
                    "cache_ttl": cache_ttl
                }
            )
        return cached_result
    
    start_time = time.time()
    
    try:
        data = await database.get_regional_summary(
            programa=programa,
            regiao=regiao,
            state=state,
            municipality=municipality
        )
        
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
    tipo: Optional[str] = Query(None, description="RURAL tipo filter"),
    modalidade_proposta: Optional[str] = Query(None, description="RURAL modalidade proposta filter"),
    database = Depends(get_database)
):
    """Get program summary with financial breakdown and execution status"""
    
    # Create cache key with all filters
    filter_parts = [
        regiao or 'ALL',
        state or 'ALL', 
        municipality or 'ALL',
        status or 'ALL',
        programa or 'ALL',
        tipo or 'ALL',
        modalidade_proposta or 'ALL'
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
            programa=programa,
            tipo=tipo,
            modalidade_proposta=modalidade_proposta
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

@app.get(f"{settings.api.base_path}/data-quality/comprehensive")
async def get_comprehensive_data_quality():
    """Get comprehensive data quality metrics including program-specific and Dados Prioritários"""
    
    cache_key = "data_quality:comprehensive"
    cache_ttl = settings.business_rules.get_cache_ttl('static_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Comprehensive data quality metrics served from cache")
        return JSONResponse(content=cached_result)
    
    start_time = time.time()
    
    try:
        # Get comprehensive quality report
        result = await data_quality_service.get_comprehensive_quality_report()
        
        # Convert Decimal values to float for JSON serialization
        result = decimal_to_float(result)
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Comprehensive data quality metrics retrieved",
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error("Failed to get comprehensive data quality metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve comprehensive data quality metrics")

@app.get(f"{settings.api.base_path}/data-quality/programs/{{programa}}")
async def get_program_quality_metrics(programa: str):
    """Get data quality metrics for a specific program"""
    
    if programa not in ['FAR', 'FDS', 'RURAL']:
        raise HTTPException(status_code=400, detail="Invalid program. Must be FAR, FDS, or RURAL")
    
    cache_key = f"data_quality:program:{programa}"
    cache_ttl = settings.business_rules.get_cache_ttl('static_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Program data quality metrics served from cache", programa=programa)
        return JSONResponse(content=cached_result)
    
    start_time = time.time()
    
    try:
        # Get program-specific metrics
        metrics = await data_quality_service.get_program_quality_metrics(programa)
        
        result = {
            "programa": programa,
            "metrics": metrics[0] if metrics else None,
            "metadata": {
                "execution_time": f"{time.time() - start_time:.3f}s",
                "source": "mcmv_v2.projetos",
                "cache_ttl": cache_ttl
            }
        }
        
        # Convert Decimal values to float for JSON serialization
        result = decimal_to_float(result)
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Program data quality metrics retrieved",
                   programa=programa,
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error("Failed to get program data quality metrics", programa=programa, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve program data quality metrics")

@app.get(f"{settings.api.base_path}/data-quality/dados-prioritarios")
async def get_dados_prioritarios_quality_metrics():
    """Get data quality metrics for Dados Prioritários"""
    
    cache_key = "data_quality:dados_prioritarios"
    cache_ttl = settings.business_rules.get_cache_ttl('static_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Dados Prioritários quality metrics served from cache")
        return JSONResponse(content=cached_result)
    
    start_time = time.time()
    
    try:
        # Get Dados Prioritários metrics
        result = await data_quality_service.get_dados_prioritarios_quality_metrics()
        result["metadata"]["execution_time"] = f"{time.time() - start_time:.3f}s"
        result["metadata"]["cache_ttl"] = cache_ttl
        
        # Convert Decimal values to float for JSON serialization
        result = decimal_to_float(result)
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Dados Prioritários quality metrics retrieved",
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error("Failed to get Dados Prioritários quality metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve Dados Prioritários quality metrics")

@app.get(f"{settings.api.base_path}/data-quality/trends")
async def get_quality_trends(
    programa: Optional[str] = Query(None, description="Program filter"),
    days: int = Query(30, description="Number of days to retrieve")
):
    """Get quality trends over time"""
    
    cache_key = f"data_quality:trends:{programa or 'ALL'}:{days}"
    cache_ttl = settings.business_rules.get_cache_ttl('aggregated_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Quality trends served from cache", programa=programa, days=days)
        return JSONResponse(content=cached_result)
    
    start_time = time.time()
    
    try:
        trends = await data_quality_service.get_quality_trends(programa=programa, days=days)
        
        result = {
            "trends": trends,
            "metadata": {
                "programa": programa,
                "days": days,
                "execution_time": f"{time.time() - start_time:.3f}s",
                "data_points": len(trends),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Quality trends retrieved",
                   programa=programa,
                   days=days,
                   data_points=len(trends),
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error("Failed to get quality trends", programa=programa, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve quality trends")

@app.get(f"{settings.api.base_path}/data-quality/alerts")
async def get_quality_alerts(
    active_only: bool = Query(True, description="Return only active alerts")
):
    """Get configured quality alerts"""
    
    try:
        alerts = await data_quality_service.get_quality_alerts(active_only=active_only)
        
        return JSONResponse(content={
            "alerts": alerts,
            "metadata": {
                "count": len(alerts),
                "active_only": active_only
            }
        })
        
    except Exception as e:
        logger.error("Failed to get quality alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve quality alerts")

@app.post(f"{settings.api.base_path}/data-quality/snapshot")
async def capture_quality_snapshot(background_tasks: BackgroundTasks):
    """Capture a snapshot of current quality metrics"""
    
    try:
        # Add to background tasks for async processing
        background_tasks.add_task(data_quality_service.capture_quality_snapshot)
        
        return JSONResponse(content={
            "status": "scheduled",
            "message": "Quality snapshot capture has been scheduled"
        })
        
    except Exception as e:
        logger.error("Failed to schedule quality snapshot", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to schedule quality snapshot")

@app.post(f"{settings.api.base_path}/data-quality/check-alerts")
async def check_quality_alerts_endpoint(background_tasks: BackgroundTasks):
    """Check and trigger quality alerts"""
    
    try:
        # Run synchronously for immediate feedback
        result = await data_quality_service.check_quality_alerts()
        
        return JSONResponse(content={
            "status": "completed",
            "alerts_triggered": result.get("alerts_triggered", 0),
            "alerts_checked": result.get("alerts_checked", 0)
        })
        
    except Exception as e:
        logger.error("Failed to check quality alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check quality alerts")

@app.get(f"{settings.api.base_path}/data-quality/export/{{format}}")
async def export_quality_report(
    format: str,
    programa: Optional[str] = Query(None, description="Program filter"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Export quality report in specified format"""
    
    if format not in ['csv', 'json', 'excel']:
        raise HTTPException(status_code=400, detail="Format must be 'csv', 'json' or 'excel'")
    
    try:
        data = await data_quality_service.export_quality_report(
            format=format,
            programa=programa,
            start_date=start_date,
            end_date=end_date
        )
        
        if format == 'csv':
            return Response(
                content=data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=quality_report_{time.strftime('%Y%m%d')}.csv"
                }
            )
        elif format == 'excel':
            return Response(
                content=data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=quality_report_{time.strftime('%Y%m%d')}.xlsx"
                }
            )
        else:
            return JSONResponse(content=data)
            
    except Exception as e:
        logger.error("Failed to export quality report", format=format, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export quality report")

# ================================================
# ETL QUALITY ANALYSIS ENDPOINTS
# ================================================

@app.get(f"{settings.api.base_path}/etl-quality/analysis")
async def get_etl_quality_analysis(
    table: str = Query("dados_prioritarios", description="Table to analyze"),
    database = Depends(get_database)
):
    """Run comprehensive ETL quality analysis for forensic data issues"""
    
    cache_key = f"etl_quality:analysis:{table}"
    cache_ttl = 3600  # 1 hour cache
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Initialize quality service
        quality_service = ETLQualityService(database)
        
        # Run appropriate analysis based on table
        if table == "dados_prioritarios":
            result = await quality_service.analyze_dados_prioritarios_quality()
        elif table == "projetos":
            result = await quality_service.analyze_projetos_quality()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported table: {table}")
        
        # Save report to database
        # await quality_service.save_quality_report(result)  # TODO: Implement insert method
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to run ETL quality analysis", table=table, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to run ETL quality analysis")

@app.get(f"{settings.api.base_path}/etl-quality/history")
async def get_etl_quality_history(
    table: Optional[str] = Query(None, description="Filter by table name"),
    days: int = Query(30, description="Number of days to retrieve"),
    database = Depends(get_database)
):
    """Get ETL quality report history"""
    
    try:
        where_conditions = []
        params = {}
        
        if table:
            where_conditions.append("table_name = :table")
            params['table'] = table
            
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT 
            id,
            report_date,
            table_name,
            total_issues,
            quality_score,
            report_data->>'statistics' as statistics,
            created_at
        FROM mcmv_v2.etl_quality_reports
        {where_clause}
        AND report_date >= CURRENT_DATE - INTERVAL '{days} days'
        ORDER BY report_date DESC, table_name
        """
        
        data = await database.fetch_all(query, params)
        
        return {
            "data": data,
            "metadata": {
                "total_reports": len(data),
                "days_covered": days,
                "tables": list(set(row['table_name'] for row in data))
            }
        }
        
    except Exception as e:
        logger.error("Failed to get ETL quality history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve ETL quality history")

@app.get(f"{settings.api.base_path}/etl-quality/issues")
async def get_etl_quality_issues(
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    unresolved_only: bool = Query(False, description="Show only unresolved issues"),
    database = Depends(get_database)
):
    """Get detailed ETL quality issues"""
    
    try:
        where_conditions = []
        params = {}
        
        if severity:
            where_conditions.append("qi.severity = :severity")
            params['severity'] = severity
            
        if issue_type:
            where_conditions.append("qi.issue_type = :issue_type")
            params['issue_type'] = issue_type
            
        if unresolved_only:
            where_conditions.append("NOT qi.resolved")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT 
            qi.*,
            qr.table_name,
            qr.report_date
        FROM mcmv_v2.etl_quality_issues qi
        JOIN mcmv_v2.etl_quality_reports qr ON qi.report_id = qr.id
        {where_clause}
        ORDER BY qi.created_at DESC
        LIMIT 100
        """
        
        data = await database.fetch_all(query, params)
        
        # Group by issue type for summary
        issue_summary = {}
        for row in data:
            issue_type = row['issue_type']
            if issue_type not in issue_summary:
                issue_summary[issue_type] = {
                    'count': 0,
                    'severities': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
                }
            issue_summary[issue_type]['count'] += 1
            issue_summary[issue_type]['severities'][row['severity']] += 1
        
        return {
            "issues": data,
            "summary": issue_summary,
            "metadata": {
                "total_issues": len(data),
                "filters_applied": {
                    "severity": severity,
                    "issue_type": issue_type,
                    "unresolved_only": unresolved_only
                }
            }
        }
        
    except Exception as e:
        logger.error("Failed to get ETL quality issues", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve ETL quality issues")

@app.get(f"{settings.api.base_path}/etl-quality/latest-status")
async def get_etl_quality_latest_status(database = Depends(get_database)):
    """Get latest quality status for all tables"""
    
    try:
        query = """
        SELECT * FROM mcmv_v2.vw_latest_quality_status
        ORDER BY quality_score DESC
        """
        
        data = await database.fetch_all(query)
        
        return {
            "status": data,
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "tables_monitored": len(data)
            }
        }
        
    except Exception as e:
        logger.error("Failed to get latest ETL quality status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve latest ETL quality status")

@app.get(f"{settings.api.base_path}/delivery-forecast", response_model=DeliveryForecastResponse)
async def get_delivery_forecast(
    programa: Optional[str] = Query(None, description="Program filter"),
    regiao: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    database = Depends(get_database)
):
    """Get delivery forecast data with full filter support"""
    
    cache_key = f"delivery_forecast:{programa or 'ALL'}:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('detailed_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Delivery forecast served from cache", programa=programa, regiao=regiao, state=state, municipality=municipality)
        return cached_result
    
    start_time = time.time()
    
    try:
        data = await database.get_delivery_forecast(
            programa=programa,
            regiao=regiao,
            state=state,
            municipality=municipality
        )
        
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
                   regiao=regiao,
                   state=state,
                   municipality=municipality,
                   data_points=len(data),
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return result
        
    except Exception as e:
        logger.error("Failed to get delivery forecast", 
                    programa=programa, regiao=regiao, state=state, municipality=municipality, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve delivery forecast")

@app.get(f"{settings.api.base_path}/dados-prioritarios/previsao-entrega")
async def get_dados_prioritarios_previsao_entrega(
    ano_contratacao: Optional[int] = Query(None, description="Ano de contratação filter"),
    mes_movimento: Optional[int] = Query(None, description="Mês de movimento filter"),
    ano_movimento: Optional[int] = Query(None, description="Ano de movimento filter"),
    situacao_empreendimento: Optional[str] = Query(None, description="Situação do empreendimento filter"),
    uf: Optional[str] = Query(None, description="UF filter"),
    database = Depends(get_database)
):
    """Get delivery forecast data from Dados Prioritários with full filtering support"""
    
    cache_key = f"dados_prioritarios:previsao_entrega:{ano_contratacao or 'ALL'}:{mes_movimento or 'ALL'}:{ano_movimento or 'ALL'}:{situacao_empreendimento or 'ALL'}:{uf or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('detailed_data')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("Dados Prioritários previsão entrega served from cache", 
                   ano_contratacao=ano_contratacao, mes_movimento=mes_movimento, 
                   ano_movimento=ano_movimento, situacao=situacao_empreendimento, uf=uf)
        return JSONResponse(content=cached_result)
    
    start_time = time.time()
    
    try:
        # Build filters
        filters = ["data_previsao_entrega IS NOT NULL"]
        params = {}
        
        if ano_contratacao:
            filters.append("EXTRACT(YEAR FROM data_contratacao) = :ano_contratacao")
            params['ano_contratacao'] = ano_contratacao
            
        if ano_movimento:
            filters.append("EXTRACT(YEAR FROM data_movimento) = :ano_movimento")
            params['ano_movimento'] = ano_movimento
            
        if mes_movimento and ano_movimento:
            filters.append("EXTRACT(MONTH FROM data_movimento) = :mes_movimento")
            params['mes_movimento'] = mes_movimento
            
        if situacao_empreendimento:
            filters.append("situacao_empreendimento = :situacao_empreendimento")
            params['situacao_empreendimento'] = situacao_empreendimento
            
        if uf:
            filters.append("sg_uf = :uf") 
            params['uf'] = uf
        
        where_clause = " AND ".join(filters)
        
        # Query from main table to support all filters, using latest data if no movimento filter
        if not ano_movimento and not mes_movimento:
            # Get latest snapshot when no date filters specified
            query = f"""
            WITH latest AS (
                SELECT dp.*
                FROM mcmv_v2.dados_prioritarios dp
                JOIN (
                    SELECT MAX(data_movimento) AS max_mov
                    FROM mcmv_v2.dados_prioritarios
                ) mx ON dp.data_movimento = mx.max_mov
            )
            SELECT 
                apf,
                sg_uf,
                municipio,
                nome_empreendimento,
                modalidade,
                data_contratacao,
                data_previsao_entrega,
                COALESCE(uh_vigentes, GREATEST(0, uh_original_contratadas - COALESCE(uh_entregues, 0))) AS uh_a_entregar,
                DATE_TRUNC('month', data_previsao_entrega) as mes_entrega
            FROM latest
            WHERE {where_clause}
            ORDER BY data_previsao_entrega, apf
            """
        else:
            # Use specific movimento date when filters are applied
            query = f"""
            SELECT 
                apf,
                sg_uf,
                municipio,
                nome_empreendimento,
                modalidade,
                data_contratacao,
                data_previsao_entrega,
                COALESCE(uh_vigentes, GREATEST(0, uh_original_contratadas - COALESCE(uh_entregues, 0))) AS uh_a_entregar,
                DATE_TRUNC('month', data_previsao_entrega) as mes_entrega
            FROM mcmv_v2.dados_prioritarios
            WHERE {where_clause}
            ORDER BY data_previsao_entrega, apf
            """
        
        data = await database.execute_query(query, params)
        
        # Calculate summary metrics
        if data:
            total_projetos = len(data)
            total_uh = sum(record['uh_a_entregar'] for record in data if record['uh_a_entregar'])
            
            # Group by month for timeline
            monthly_summary = {}
            for record in data:
                if record['mes_entrega']:
                    month_key = record['mes_entrega'].strftime('%Y-%m')
                    if month_key not in monthly_summary:
                        monthly_summary[month_key] = {
                            'month': month_key,
                            'projetos': 0,
                            'uh_total': 0,
                            'modalidades': set()
                        }
                    monthly_summary[month_key]['projetos'] += 1
                    monthly_summary[month_key]['uh_total'] += record['uh_a_entregar'] or 0
                    monthly_summary[month_key]['modalidades'].add(record['modalidade'])
            
            # Convert sets to lists for JSON serialization
            for month_data in monthly_summary.values():
                month_data['modalidades'] = list(month_data['modalidades'])
            
            timeline = list(monthly_summary.values())
            timeline.sort(key=lambda x: x['month'])
            
        else:
            total_projetos = 0
            total_uh = 0
            timeline = []
        
        result = {
            "projetos": data,
            "timeline": timeline,
            "summary": {
                "total_projetos": total_projetos,
                "total_uh": total_uh,
                "meses_com_entregas": len(timeline),
                "modalidades_incluidas": list(set(record['modalidade'] for record in data)) if data else []
            },
            "metadata": {
                "ano_contratacao": ano_contratacao,
                "mes_movimento": mes_movimento,
                "ano_movimento": ano_movimento,
                "situacao_empreendimento": situacao_empreendimento,
                "uf": uf,
                "execution_time": f"{time.time() - start_time:.3f}s",
                "data_points": len(data),
                "cache_ttl": cache_ttl,
                "source": "mcmv_v2.dados_prioritarios"
            }
        }
        
        # Convert Decimal values to float for JSON serialization
        result = decimal_to_float(result)
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("Dados Prioritários previsão entrega served from database",
                   ano_contratacao=ano_contratacao,
                   mes_movimento=mes_movimento,
                   ano_movimento=ano_movimento,
                   situacao=situacao_empreendimento,
                   uf=uf,
                   projetos=total_projetos,
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error("Failed to get Dados Prioritários previsão entrega", 
                    ano_contratacao=ano_contratacao,
                    mes_movimento=mes_movimento,
                    ano_movimento=ano_movimento,
                    situacao=situacao_empreendimento,
                    uf=uf,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve previsão de entrega data")

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

@app.get(f"{settings.api.base_path}/filters/rural")
async def get_rural_filters(
    database = Depends(get_database)
):
    """Get available filter values for RURAL program (tipo and modalidade_proposta)"""
    
    cache_key = "filters:rural"
    cache_ttl = settings.business_rules.get_cache_ttl('filters')
    
    # Try cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info("RURAL filters served from cache")
        return cached_result
    
    try:
        # Get tipo values
        tipo_query = """
        SELECT DISTINCT tipo, COUNT(*) as count
        FROM mcmv_v2.projetos
        WHERE programa = 'RURAL' AND tipo IS NOT NULL
        GROUP BY tipo
        ORDER BY tipo
        """
        tipo_data = await database.get_chart_data(tipo_query, {})
        
        # Get modalidade_proposta values
        modalidade_query = """
        SELECT DISTINCT modalidade_proposta, COUNT(*) as count
        FROM mcmv_v2.projetos
        WHERE programa = 'RURAL' AND modalidade_proposta IS NOT NULL
        GROUP BY modalidade_proposta
        ORDER BY modalidade_proposta
        """
        modalidade_data = await database.get_chart_data(modalidade_query, {})
        
        result = {
            "data": {
                "tipos": [{"value": row["tipo"], "label": row["tipo"], "count": row["count"]} for row in tipo_data],
                "modalidades": [{"value": row["modalidade_proposta"], "label": row["modalidade_proposta"], "count": row["count"]} for row in modalidade_data]
            },
            "metadata": {
                "cache_ttl": cache_ttl,
                "tipo_count": len(tipo_data),
                "modalidade_count": len(modalidade_data)
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        logger.info("RURAL filters served from database", 
                   tipo_count=len(tipo_data),
                   modalidade_count=len(modalidade_data))
        return result
        
    except Exception as e:
        logger.error("Failed to get RURAL filters", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve RURAL filters")

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
    tipo: Optional[str] = Query(None, description="Tipo filter (RURAL, RURAL-CALAMIDADES)"),
    modalidade_proposta: Optional[str] = Query(None, description="Modalidade proposta filter"),
    database = Depends(get_database)
):
    """Get RURAL UH by Region and Status chart data"""
    
    cache_key = f"rural:region_status:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}:{tipo or 'ALL'}:{modalidade_proposta or 'ALL'}"
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
    tipo: Optional[str] = Query(None, description="Tipo filter (RURAL, RURAL-CALAMIDADES)"),
    modalidade_proposta: Optional[str] = Query(None, description="Modalidade proposta filter"),
    database = Depends(get_database)
):
    """Get RURAL UH by Status donut chart data"""
    
    cache_key = f"rural:status_donut:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}:{tipo or 'ALL'}:{modalidade_proposta or 'ALL'}"
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
    tipo: Optional[str] = Query(None, description="Tipo filter (RURAL, RURAL-CALAMIDADES)"),
    modalidade_proposta: Optional[str] = Query(None, description="Modalidade proposta filter"),
    database = Depends(get_database)
):
    """Get RURAL delivery timeline forecast chart data"""
    
    cache_key = f"rural:timeline:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}:{tipo or 'ALL'}:{modalidade_proposta or 'ALL'}"
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
            TO_CHAR(DATE_TRUNC('month', dt_previsao_conclusao_obra), 'YYYY-MM-DD')::text as delivery_month,
            SUM(uh_contratadas) as total_uh,
            COUNT(DISTINCT nu_apf) as project_count
        FROM mcmv_v2.projetos 
        WHERE {where_clause}
        GROUP BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
        ORDER BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
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
    tipo: Optional[str] = Query(None, description="Tipo filter (RURAL, RURAL-CALAMIDADES)"),
    modalidade_proposta: Optional[str] = Query(None, description="Modalidade proposta filter"),
    database = Depends(get_database)
):
    """Get RURAL financial breakdown by municipality"""
    
    cache_key = f"rural:financial_table:{regiao or 'ALL'}:{state or 'ALL'}:{municipality or 'ALL'}:{status or 'ALL'}:{tipo or 'ALL'}:{modalidade_proposta or 'ALL'}"
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
            SUM(COALESCE(vr_total_investimento, 0)) as total_valor_contratado,
            SUM(COALESCE(vr_total_investimento, 0)) as total_investimento,
            CASE 
                WHEN SUM(uh_contratadas) > 0 
                THEN ROUND(SUM(COALESCE(vr_total_investimento, 0))::numeric / SUM(uh_contratadas)::numeric, 2)
                ELSE 0
            END as investimento_medio_uh
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
            TO_CHAR(DATE_TRUNC('month', dt_previsao_conclusao_obra), 'YYYY-MM-DD')::text as delivery_month,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
        ORDER BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
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
            SUM(COALESCE(vr_total_investimento, 0)) as total_valor_contratado,
            SUM(COALESCE(vr_total_investimento, 0)) as total_investimento,
            CASE 
                WHEN SUM(uh_contratadas) > 0 
                THEN ROUND(SUM(COALESCE(vr_total_investimento, 0))::numeric / SUM(uh_contratadas)::numeric, 2)
                ELSE 0
            END as investimento_medio_uh
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
            TO_CHAR(DATE_TRUNC('month', dt_previsao_conclusao_obra), 'YYYY-MM-DD')::text as delivery_month,
            SUM(uh_contratadas) as total_uh
        FROM mcmv_v2.projetos
        WHERE {where_clause}
        GROUP BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
        ORDER BY DATE_TRUNC('month', dt_previsao_conclusao_obra)
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
            SUM(COALESCE(vr_total_investimento, 0)) as total_valor_contratado,
            SUM(COALESCE(vr_total_investimento, 0)) as total_investimento,
            CASE 
                WHEN SUM(uh_contratadas) > 0 
                THEN ROUND(SUM(COALESCE(vr_total_investimento, 0))::numeric / SUM(uh_contratadas)::numeric, 2)
                ELSE 0
            END as investimento_medio_uh
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
    uf: Optional[str] = Query(None, description="State (UF) filter"),
    database = Depends(get_database)
):
    """Get dados prioritarios table data with programa and situacao_empreendimento grouping - showing ALL historical movement data"""
    
    # Create cache key including all filter parameters
    filters_str = f"{ano_contratacao or 'ALL'}:{mes_movimento or 'ALL'}:{ano_movimento or 'ALL'}:{situacao_empreendimento or 'ALL'}:{uf or 'ALL'}"
    cache_key = f"dados_prioritarios:table:{filters_str}"
    cache_ttl = settings.business_rules.get_cache_ttl('tables')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause - using the full table to show ALL historical data
        where_conditions = ["1=1"]
        params = {}
        
        # Note: ano_contratacao filter not available in materialized view
        # The view is aggregated by movement month/year, not contract year
            
        if mes_movimento:
            where_conditions.append("mes_movimento = :mes_movimento")
            params["mes_movimento"] = mes_movimento
            
        if ano_movimento:
            where_conditions.append("ano_movimento = :ano_movimento")
            params["ano_movimento"] = ano_movimento
            
        if situacao_empreendimento:
            where_conditions.append("situacao_empreendimento = :situacao_empreendimento")
            params["situacao_empreendimento"] = situacao_empreendimento
            
        if uf:
            where_conditions.append("sg_uf = :uf")
            params["uf"] = uf
        
        where_clause = " AND ".join(where_conditions)
        
        # Use materialized view for better performance (1088 rows vs 66k)
        # The view is pre-aggregated by programa/situacao/month/uf
        query = f"""
        SELECT 
            programa,
            situacao_empreendimento,
            ano_movimento,
            mes_movimento,
            sg_uf,
            projetos,
            uh_contratadas::INTEGER,
            uh_entregues::INTEGER,
            uh_vigentes::INTEGER,
            percentual_entregues,
            valor_contratado::NUMERIC,
            valor_desembolsado::NUMERIC,
            -- Add computed investment total
            (valor_contratado + valor_desembolsado)::NUMERIC as investimento_total
        FROM mcmv_v2.mv_dados_prioritarios_historico
        WHERE {where_clause}
        ORDER BY ano_movimento DESC, mes_movimento DESC, programa, situacao_empreendimento
        """
        
        data = await database.get_chart_data(query, params)
        
        # Calculate totals from the materialized view
        summary_query = f"""
        SELECT 
            SUM(projetos) as total_projetos,
            SUM(uh_contratadas)::INTEGER as total_uh_contratadas,
            SUM(uh_entregues)::INTEGER as total_uh_entregues,
            SUM(uh_vigentes)::INTEGER as total_uh_vigentes,
            SUM(valor_contratado)::NUMERIC as total_valor_contratado,
            SUM(valor_desembolsado)::NUMERIC as total_valor_desembolsado
        FROM mcmv_v2.mv_dados_prioritarios_historico
        WHERE {where_clause}
        """
        
        summary_data = await database.get_chart_data(summary_query, params)
        summary_row = summary_data[0] if summary_data else {}
        
        # Extract summary values with proper None handling
        total_projetos = summary_row.get('total_projetos', 0) or 0
        total_uh_contratadas = summary_row.get('total_uh_contratadas', 0) or 0
        total_uh_entregues = summary_row.get('total_uh_entregues', 0) or 0
        total_uh_vigentes = summary_row.get('total_uh_vigentes', 0) or 0
        total_valor_contratado = float(summary_row.get('total_valor_contratado') or 0)
        total_valor_desembolsado = float(summary_row.get('total_valor_desembolsado') or 0)
        
        # Calculate overall percentage
        overall_percentual = round((total_uh_entregues / total_uh_contratadas * 100), 2) if total_uh_contratadas > 0 else 0
        
        result = {
            "data": data,
            "summary": {
                "total_projetos": total_projetos,
                "total_uh_contratadas": total_uh_contratadas,
                "total_uh_entregues": total_uh_entregues,
                "total_uh_vigentes": total_uh_vigentes,
                "overall_percentual_entregues": overall_percentual,
                "total_valor_contratado": total_valor_contratado,
                "total_valor_desembolsado": total_valor_desembolsado
            },
            "metadata": {
                "source": "dados_prioritarios",
                "filters": {
                    "ano_contratacao": ano_contratacao,
                    "mes_movimento": mes_movimento,
                    "ano_movimento": ano_movimento,
                    "situacao_empreendimento": situacao_empreendimento,
                    "uf": uf
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

@app.get(f"{settings.api.base_path}/dados-prioritarios/estado-atual")
async def get_dados_prioritarios_estado_atual(
    uf: Optional[str] = Query(None, description="State (UF) filter"),
    database = Depends(get_database)
):
    """Get estado atual data - May 2025 snapshot only"""
    
    # Create cache key
    cache_key = f"dados_prioritarios:estado_atual:may2025:{uf or 'ALL'}"
    cache_ttl = settings.business_rules.get_cache_ttl('tables')
    
    try:
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build WHERE clause - filtering for May 2025 only
        where_conditions = [
            "EXTRACT(month FROM data_movimento) = 5",
            "EXTRACT(year FROM data_movimento) = 2025"
        ]
        params = {}
        
        if uf:
            where_conditions.append("sg_uf = :uf")
            params["uf"] = uf
        
        where_clause = " AND ".join(where_conditions)
        
        # Aggregate Estado Atual data by programa and situacao
        # The materialized view has data by state, so we need to sum it up
        query = """
        SELECT 
            programa,
            situacao_empreendimento,
            SUM(projetos) as projetos,
            SUM(uh_contratadas)::INTEGER as uh_contratadas,
            SUM(uh_entregues)::INTEGER as uh_entregues,
            CASE 
                WHEN SUM(uh_contratadas) > 0 
                THEN ROUND((SUM(uh_entregues)::NUMERIC / SUM(uh_contratadas)::NUMERIC) * 100, 2)
                ELSE 0
            END as percentual_entregues,
            SUM(uh_vigentes)::INTEGER as uh_vigentes,
            SUM(valor_contratado)::NUMERIC as valor_contratado,
            SUM(valor_desembolsado)::NUMERIC as valor_desembolsado,
            SUM(investimento_total)::NUMERIC as investimento_total
        FROM mcmv_v2.mv_dados_prioritarios_estado_atual
        WHERE 1=1
        """
        
        # Add UF filter if provided
        if uf:
            query += " AND sg_uf = :uf"
        
        query += " GROUP BY programa, situacao_empreendimento ORDER BY programa, situacao_empreendimento"
        
        data = await database.get_chart_data(query, params)
        
        # Calculate totals for summary
        total_projetos = sum(row.get('projetos', 0) for row in data)
        total_uh_contratadas = sum(row.get('uh_contratadas', 0) for row in data)
        total_uh_entregues = sum(row.get('uh_entregues', 0) for row in data)
        total_uh_vigentes = sum(row.get('uh_vigentes', 0) for row in data)
        total_valor_contratado = sum(float(row.get('valor_contratado', 0)) for row in data)
        total_valor_desembolsado = sum(float(row.get('valor_desembolsado', 0)) for row in data)
        
        # Calculate overall percentage
        overall_percentual = round((total_uh_entregues / total_uh_contratadas * 100), 2) if total_uh_contratadas > 0 else 0
        
        result = {
            "data": data,
            "summary": {
                "total_projetos": total_projetos,
                "total_uh_contratadas": total_uh_contratadas,
                "total_uh_entregues": total_uh_entregues,
                "total_uh_vigentes": total_uh_vigentes,
                "overall_percentual_entregues": overall_percentual,
                "total_valor_contratado": total_valor_contratado,
                "total_valor_desembolsado": total_valor_desembolsado
            },
            "metadata": {
                "source": "dados_prioritarios_may_2025",
                "snapshot_date": "2025-05",
                "filters": {
                    "uf": uf
                },
                "total_records": len(data),
                "cache_ttl": cache_ttl
            }
        }
        
        # Cache result
        await cache_manager.set(cache_key, result, expire=cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get estado atual data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve estado atual data")

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
        
        # Get available years from contract dates - using full historical table
        anos_query = """
        SELECT DISTINCT EXTRACT(year FROM data_contratacao) as ano
        FROM mcmv_v2.dados_prioritarios 
        WHERE data_contratacao IS NOT NULL
        ORDER BY ano DESC
        """
        
        # Get available months/years from movement dates - using full historical table
        movimento_query = """
        SELECT DISTINCT 
            EXTRACT(month FROM data_movimento) as mes,
            EXTRACT(year FROM data_movimento) as ano
        FROM mcmv_v2.dados_prioritarios 
        WHERE data_movimento IS NOT NULL
        ORDER BY ano DESC, mes ASC
        """
        
        # Get available situações do empreendimento - using full historical table
        situacoes_query = """
        SELECT DISTINCT situacao_empreendimento
        FROM mcmv_v2.dados_prioritarios 
        WHERE situacao_empreendimento IS NOT NULL
        ORDER BY situacao_empreendimento ASC
        """
        
        # Get available UFs (states) - using full historical table
        ufs_query = """
        SELECT DISTINCT sg_uf
        FROM mcmv_v2.dados_prioritarios 
        WHERE sg_uf IS NOT NULL
        ORDER BY sg_uf ASC
        """
        
        anos_data = await database.get_chart_data(anos_query, {})
        movimento_data = await database.get_chart_data(movimento_query, {})
        situacoes_data = await database.get_chart_data(situacoes_query, {})
        ufs_data = await database.get_chart_data(ufs_query, {})
        
        # Debug logging
        logger.info(f"UFs query returned {len(ufs_data)} rows")
        if ufs_data:
            logger.info(f"First UF: {ufs_data[0]}")
        
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
            "ufs": [row['sg_uf'] for row in ufs_data],
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

# Export Analytical Report endpoint
@app.get(f"{settings.api.base_path}/export/analytical-report")
async def export_analytical_report(
    region: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    programa: Optional[str] = Query(None),
    database = Depends(get_database)
):
    """Export analytical report as Excel"""
    
    start_time = time.time()
    
    try:
        # Build the main data query with filters
        query = """
        SELECT 
            p.nu_apf AS codigo_projeto,
            p.programa,
            CASE p.sg_uf 
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
            p.sg_uf AS estado,
            p.no_municipio AS municipio,
            p.no_empreendimento AS nome_empreendimento,
            p.uh_contratadas,
            COALESCE(p.vr_total_operacao / 1000000.0, 0) AS valor_contratado_milhoes,
            COALESCE(p.vr_total_investimento / 1000000.0, 0) AS valor_investimento_milhoes,
            p.dt_contratacao AS data_contratacao,
            p.dt_inicio_obra AS data_inicio_obra,
            p.dt_previsao_conclusao_obra AS data_previsao_conclusao,
            COALESCE(p.pc_obra_realizada, 0) AS percentual_execucao,
            p.co_situacao_operacao AS situacao_empreendimento,
            COALESCE(p.vr_ts / 1000000.0, 0) AS trabalho_social_milhoes,
            COALESCE(p.vr_total_contrapartidas / 1000000.0, 0) AS contrapartida_milhoes
        FROM mcmv_v2.projetos p
        WHERE 1=1
        """
        
        params = {}
        
        # Apply filters
        if programa:
            query += " AND p.programa = :programa"
            params['programa'] = programa
            
        if region:
            # Use the calculated region from CASE statement
            region_condition = ""
            if region == "Norte":
                region_condition = "p.sg_uf IN ('AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO')"
            elif region == "Nordeste":
                region_condition = "p.sg_uf IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE')"
            elif region == "Centro-Oeste":
                region_condition = "p.sg_uf IN ('DF', 'GO', 'MT', 'MS')"
            elif region == "Sudeste":
                region_condition = "p.sg_uf IN ('ES', 'MG', 'RJ', 'SP')"
            elif region == "Sul":
                region_condition = "p.sg_uf IN ('PR', 'RS', 'SC')"
            
            if region_condition:
                query += f" AND {region_condition}"
            
        if state:
            query += " AND p.sg_uf = :state"
            params['state'] = state
            
        if municipality:
            query += " AND p.no_municipio = :municipality"
            params['municipality'] = municipality
            
        if status:
            query += " AND p.co_situacao_operacao = :status"
            params['status'] = status
        
        # Order results
        query += " ORDER BY regiao, p.sg_uf, p.no_municipio, p.no_empreendimento"
        
        # Execute query
        rows = await database.execute_query(query, params)
        
        if not rows:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado com os filtros aplicados")
        
        # Convert rows to DataFrame for Excel export
        data_list = []
        for row in rows:
            data_list.append({
                'Código do Projeto (APF)': row['codigo_projeto'],
                'Programa': row['programa'],
                'Região': row['regiao'],
                'UF': row['estado'],
                'Município': row['municipio'],
                'Nome do Empreendimento': row['nome_empreendimento'],
                'UH Contratadas': row['uh_contratadas'],
                'Valor Contratado (R$ Milhões)': row['valor_contratado_milhoes'],
                'Valor Investimento (R$ Milhões)': row['valor_investimento_milhoes'],
                'Data de Contratação': row['data_contratacao'],
                'Data de Início da Obra': row['data_inicio_obra'],
                'Data de Previsão de Conclusão': row['data_previsao_conclusao'],
                'Percentual de Execução (%)': row['percentual_execucao'],
                'Situação do Empreendimento': row['situacao_empreendimento'],
                'Trabalho Social (R$ Milhões)': row['trabalho_social_milhoes'],
                'Contrapartida (R$ Milhões)': row['contrapartida_milhoes']
            })
        
        # Create DataFrame
        df = pd.DataFrame(data_list)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Relatório Analítico', index=False)
        
        # Generate filename
        current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        filter_suffix = ""
        if any([region, state, municipality, status, programa]):
            filter_suffix = "_filtered"
        filename = f"relacao_analitica_mcmv_{current_date}{filter_suffix}.xlsx"
        
        # Create streaming response
        output.seek(0)
        
        logger.info("Analytical report generated successfully",
                   total_records=len(rows),
                   filters={
                       "region": region,
                       "state": state,
                       "municipality": municipality,
                       "status": status,
                       "programa": programa
                   },
                   execution_time=f"{time.time() - start_time:.3f}s")
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to generate analytical report", error=str(e))
        raise HTTPException(status_code=500, detail="Falha ao gerar relatório analítico")

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