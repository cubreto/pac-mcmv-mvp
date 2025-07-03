"""
MCMV Dashboard v5 - Pydantic Models
Type-safe API response models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class KPIResponse(BaseModel):
    """KPI response model with full metrics"""
    total_projetos: int = Field(..., description="Total number of projects")
    total_uh_contratadas: int = Field(..., description="Total contracted housing units")
    total_contratado: float = Field(..., description="Total contracted value")
    total_investimento: float = Field(..., description="Total investment value")
    investimento_medio_por_uh: float = Field(..., description="Average investment per housing unit")
    percentual_execucao_medio: float = Field(..., description="Average execution percentage")
    uh_em_execucao: int = Field(..., description="Housing units in execution")
    uh_nao_iniciadas: int = Field(..., description="Housing units not started")
    uh_concluidas: int = Field(..., description="Completed housing units")
    projetos_alto_risco: int = Field(..., description="High-risk projects count")
    data_atualizacao: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

class RegionalData(BaseModel):
    """Regional summary data point"""
    regiao: str = Field(..., description="Region name")
    total_projetos: int = Field(..., description="Total projects in region")
    total_uh: int = Field(..., description="Total housing units in region")
    total_contratado: float = Field(..., description="Total contracted value in region")
    total_investimento: float = Field(..., description="Total investment in region")
    trabalho_social: Optional[float] = Field(None, description="Social work value")
    contrapartida: Optional[float] = Field(None, description="Counterpart value")
    percentual_execucao_medio: Optional[float] = Field(None, description="Average execution percentage")
    em_execucao: Optional[int] = Field(None, description="Units in execution")
    nao_iniciadas: Optional[int] = Field(None, description="Units not started")
    concluidas: Optional[int] = Field(None, description="Completed units")
    color: Optional[str] = Field(None, description="Region color for charts")

class RegionalSummaryResponse(BaseModel):
    """Regional summary response"""
    data: List[RegionalData] = Field(..., description="Regional data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

class ProgramData(BaseModel):
    """Program summary data point"""
    programa: str = Field(..., description="Program name")
    total_projetos: int = Field(..., description="Total projects in program")
    total_uh: int = Field(..., description="Total housing units in program")
    total_contratado: float = Field(..., description="Total contracted value in program")
    total_investimento: float = Field(..., description="Total investment in program")
    trabalho_social: Optional[float] = Field(None, description="Social work value")
    contrapartida: Optional[float] = Field(None, description="Counterpart value")
    percentual_execucao_medio: Optional[float] = Field(None, description="Average execution percentage")
    em_execucao: Optional[int] = Field(None, description="Units in execution")
    nao_iniciadas: Optional[int] = Field(None, description="Units not started")
    concluidas: Optional[int] = Field(None, description="Completed units")
    color: Optional[str] = Field(None, description="Program color for charts")

class ProgramSummaryResponse(BaseModel):
    """Program summary response"""
    data: List[ProgramData] = Field(..., description="Program data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

class TemporalDataPoint(BaseModel):
    """Temporal trend data point"""
    mes_contratacao: datetime = Field(..., description="Contract month")
    programa: str = Field(..., description="Program name")
    regiao: Optional[str] = Field(None, description="Region name")
    projetos_contratados: int = Field(..., description="Projects contracted in month")
    uh_contratadas_mes: int = Field(..., description="Housing units contracted in month")
    investimento_mes: float = Field(..., description="Investment in month")
    projetos_acumulados: int = Field(..., description="Cumulative projects")
    uh_acumuladas: int = Field(..., description="Cumulative housing units")
    media_movel_3meses: float = Field(..., description="3-month moving average")

class TemporalTrendsResponse(BaseModel):
    """Temporal trends response"""
    data: List[TemporalDataPoint] = Field(..., description="Temporal data points")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

class DataQualityProgram(BaseModel):
    """Data quality metrics for a program"""
    programa: str = Field(..., description="Program name")
    total_records: int = Field(..., description="Total records analyzed")
    missing_dt_contratacao: int = Field(..., description="Records missing contract date")
    missing_dt_inicio_obra: int = Field(..., description="Records missing start date")
    missing_pc_obra: int = Field(..., description="Records missing execution percentage")
    missing_empreendimento: int = Field(..., description="Records missing enterprise name")
    invalid_percentual_obra: int = Field(..., description="Records with invalid execution percentage")
    invalid_uh_contratadas: int = Field(..., description="Records with invalid housing units")
    invalid_investimento: int = Field(..., description="Records with invalid investment")
    inicio_antes_contratacao: int = Field(..., description="Records with start before contract")
    progresso_sem_inicio: int = Field(..., description="Records with progress but no start date")
    data_quality_score: float = Field(..., description="Overall data quality score (0-100)")
    ultima_verificacao: datetime = Field(..., description="Last verification timestamp")

class DataQualityResponse(BaseModel):
    """Data quality response"""
    programs: List[DataQualityProgram] = Field(..., description="Quality metrics by program")
    overall_score: float = Field(..., description="Overall quality score across all programs")
    minimum_acceptable_score: float = Field(..., description="Minimum acceptable quality score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

class FilterOptions(BaseModel):
    """Available filter options"""
    programs: List[str] = Field(..., description="Available programs")
    regions: List[str] = Field(..., description="Available regions")
    states: List[str] = Field(..., description="Available states")
    status_options: List[str] = Field(..., description="Available status options")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class DeliveryForecastDataPoint(BaseModel):
    """Delivery forecast data point"""
    ano_mes: str = Field(..., description="Year-month (YYYY-MM)")
    programa: str = Field(..., description="Program name")
    numero_uhs: int = Field(..., description="Number of housing units to be delivered")
    numero_projetos: int = Field(..., description="Number of projects to be delivered")

class DeliveryForecastResponse(BaseModel):
    """Delivery forecast response"""
    data: List[DeliveryForecastDataPoint] = Field(..., description="Delivery forecast data points")
    summary: Dict[str, Any] = Field(..., description="Summary metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    timestamp: float = Field(..., description="Response timestamp")
    database_status: Optional[str] = Field(None, description="Database health status")
    cache_status: Optional[str] = Field(None, description="Cache health status")

class ConfigurationResponse(BaseModel):
    """Configuration response for frontend"""
    programs: Dict[str, Any] = Field(..., description="Program configurations")
    status_definitions: Dict[str, Any] = Field(..., description="Status definitions")
    regions: Dict[str, Any] = Field(..., description="Region configurations")
    charts: Dict[str, Any] = Field(..., description="Chart configurations")
    kpis: Dict[str, Any] = Field(..., description="KPI definitions")
    api_version: str = Field(..., description="API version")
    performance: Dict[str, Any] = Field(..., description="Performance settings")