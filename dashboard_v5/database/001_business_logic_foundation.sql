-- ================================================
-- MCMV Dashboard v5 - Business Logic Foundation
-- Single Source of Truth for all business rules
-- ================================================

-- Create schema for v5
CREATE SCHEMA IF NOT EXISTS mcmv_v5;

-- ================================================
-- 1. CANONICAL STATUS DEFINITIONS
-- ================================================

CREATE OR REPLACE VIEW mcmv_v5.vw_canonical_project_status AS
SELECT 
    p.*,
    -- CANONICAL STATUS LOGIC - Single source of truth
    CASE 
        WHEN COALESCE(p.pc_obra_realizada, 0) = 0 THEN 'nao_iniciada'
        WHEN p.pc_obra_realizada >= 100 THEN 'concluida'
        WHEN p.pc_obra_realizada > 0 AND p.pc_obra_realizada < 100 THEN 'em_execucao'
        ELSE 'indefinida'
    END as status_canonico,
    
    -- EXECUTION PHASE CLASSIFICATION
    CASE 
        WHEN COALESCE(p.pc_obra_realizada, 0) = 0 THEN 'Pre-Execution'
        WHEN p.pc_obra_realizada < 25 THEN 'Early-Stage'
        WHEN p.pc_obra_realizada < 75 THEN 'Mid-Stage'
        WHEN p.pc_obra_realizada < 100 THEN 'Near-Completion'
        WHEN p.pc_obra_realizada >= 100 THEN 'Completed'
        ELSE 'Unknown'
    END as fase_execucao,
    
    -- RISK CLASSIFICATION
    CASE 
        WHEN p.programa = 'RURAL' AND COALESCE(p.pc_obra_realizada, 0) = 0 AND 
             EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM p.dt_contratacao) > 3 THEN 'alto_risco'
        WHEN p.programa IN ('FAR', 'FDS') AND COALESCE(p.pc_obra_realizada, 0) = 0 AND 
             EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM p.dt_contratacao) > 2 THEN 'alto_risco'
        WHEN COALESCE(p.pc_obra_realizada, 0) > 0 THEN 'baixo_risco'
        ELSE 'medio_risco'
    END as classificacao_risco,
    
    -- INVESTMENT EFFICIENCY
    CASE 
        WHEN p.uh_contratadas > 0 THEN p.vr_total_investimento / p.uh_contratadas
        ELSE 0
    END as investimento_por_uh,
    
    -- GEOGRAPHICAL CONTEXT
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
        ELSE 'Não Identificado' 
    END as regiao_canonica
FROM mcmv_v2.projetos p
WHERE p.vr_total_investimento > 0;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_canonical_status_programa_regiao 
ON mcmv_v2.projetos(programa, sg_uf) 
WHERE vr_total_investimento > 0;

-- ================================================
-- 2. PRE-COMPUTED KPI AGGREGATIONS
-- ================================================

CREATE MATERIALIZED VIEW mcmv_v5.vw_mat_kpi_aggregations AS
SELECT 
    programa,
    regiao_canonica as regiao,
    status_canonico,
    
    -- CORE METRICS
    COUNT(*) as total_projetos,
    SUM(uh_contratadas) as total_uh_contratadas,
    SUM(vr_total_operacao) as total_contratado,
    SUM(vr_total_investimento) as total_investimento,
    SUM(vr_ts) as total_trabalho_social,
    SUM(vr_total_contrapartidas) as total_contrapartidas,
    
    -- EXECUTION METRICS
    AVG(COALESCE(pc_obra_realizada, 0)) as percentual_execucao_medio,
    SUM(CASE WHEN status_canonico = 'em_execucao' THEN uh_contratadas ELSE 0 END) as uh_em_execucao,
    SUM(CASE WHEN status_canonico = 'nao_iniciada' THEN uh_contratadas ELSE 0 END) as uh_nao_iniciadas,
    SUM(CASE WHEN status_canonico = 'concluida' THEN uh_contratadas ELSE 0 END) as uh_concluidas,
    
    -- EFFICIENCY METRICS
    AVG(investimento_por_uh) as investimento_medio_por_uh,
    STDDEV(investimento_por_uh) as desvio_investimento_uh,
    
    -- RISK METRICS
    SUM(CASE WHEN classificacao_risco = 'alto_risco' THEN 1 ELSE 0 END) as projetos_alto_risco,
    SUM(CASE WHEN classificacao_risco = 'alto_risco' THEN uh_contratadas ELSE 0 END) as uh_alto_risco,
    
    -- TEMPORAL CONTEXT
    CURRENT_TIMESTAMP as data_atualizacao,
    EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) as timestamp_atualizacao
    
FROM mcmv_v5.vw_canonical_project_status
GROUP BY GROUPING SETS (
    (programa),                                    -- Program-level KPIs
    (programa, regiao),                           -- Program x Region KPIs  
    (programa, status_canonico),                  -- Program x Status KPIs
    (regiao),                                     -- Region-only KPIs
    ()                                            -- Global KPIs
);

-- Create unique index for fast lookups
CREATE UNIQUE INDEX idx_mat_kpi_unique 
ON mcmv_v5.vw_mat_kpi_aggregations(
    COALESCE(programa, 'ALL'),
    COALESCE(regiao, 'ALL'), 
    COALESCE(status_canonico, 'ALL')
);

-- ================================================
-- 3. TEMPORAL ANALYSIS FOUNDATION
-- ================================================

CREATE MATERIALIZED VIEW mcmv_v5.vw_mat_temporal_trends AS
SELECT 
    programa,
    regiao_canonica as regiao,
    mes_contratacao,
    EXTRACT(QUARTER FROM mes_contratacao) as trimestre_contratacao,
    EXTRACT(YEAR FROM mes_contratacao) as ano_contratacao,
    
    -- MONTHLY AGGREGATIONS
    projetos_contratados,
    uh_contratadas_mes,
    investimento_mes,
    
    -- CUMULATIVE CALCULATIONS
    SUM(projetos_contratados) OVER (
        PARTITION BY programa, regiao 
        ORDER BY mes_contratacao
        ROWS UNBOUNDED PRECEDING
    ) as projetos_acumulados,
    
    SUM(uh_contratadas_mes) OVER (
        PARTITION BY programa, regiao 
        ORDER BY mes_contratacao
        ROWS UNBOUNDED PRECEDING
    ) as uh_acumuladas,
    
    -- MOVING AVERAGES
    AVG(projetos_contratados) OVER (
        PARTITION BY programa, regiao 
        ORDER BY mes_contratacao
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as media_movel_3meses
    
FROM (
    SELECT 
        programa,
        regiao_canonica as regiao,
        DATE_TRUNC('month', dt_contratacao) as mes_contratacao,
        COUNT(*) as projetos_contratados,
        SUM(uh_contratadas) as uh_contratadas_mes,
        SUM(vr_total_investimento) as investimento_mes
    FROM mcmv_v5.vw_canonical_project_status
    WHERE dt_contratacao IS NOT NULL
    GROUP BY programa, regiao_canonica, DATE_TRUNC('month', dt_contratacao)
) temporal_base
ORDER BY programa, regiao, mes_contratacao;

-- Create index for temporal queries
CREATE INDEX idx_mat_temporal_programa_regiao_mes 
ON mcmv_v5.vw_mat_temporal_trends(programa, regiao, mes_contratacao);

-- ================================================
-- 4. DATA QUALITY MONITORING
-- ================================================

CREATE MATERIALIZED VIEW mcmv_v5.vw_data_quality_metrics AS
SELECT 
    programa,
    
    -- COMPLETENESS METRICS
    COUNT(*) as total_records,
    COUNT(CASE WHEN dt_contratacao IS NULL THEN 1 END) as missing_dt_contratacao,
    COUNT(CASE WHEN dt_inicio_obra IS NULL THEN 1 END) as missing_dt_inicio_obra,
    COUNT(CASE WHEN pc_obra_realizada IS NULL THEN 1 END) as missing_pc_obra,
    COUNT(CASE WHEN no_empreendimento IS NULL OR no_empreendimento = '' THEN 1 END) as missing_empreendimento,
    
    -- CONSISTENCY CHECKS
    COUNT(CASE WHEN pc_obra_realizada > 100 THEN 1 END) as invalid_percentual_obra,
    COUNT(CASE WHEN uh_contratadas <= 0 THEN 1 END) as invalid_uh_contratadas,
    COUNT(CASE WHEN vr_total_investimento <= 0 THEN 1 END) as invalid_investimento,
    
    -- LOGICAL INCONSISTENCIES
    COUNT(CASE WHEN dt_inicio_obra < dt_contratacao THEN 1 END) as inicio_antes_contratacao,
    COUNT(CASE WHEN pc_obra_realizada > 0 AND dt_inicio_obra IS NULL THEN 1 END) as progresso_sem_inicio,
    
    -- QUALITY SCORE (0-100)
    ROUND(
        (100.0 * (1.0 - (
            COALESCE(COUNT(CASE WHEN dt_contratacao IS NULL THEN 1 END), 0) +
            COALESCE(COUNT(CASE WHEN pc_obra_realizada > 100 THEN 1 END), 0) +
            COALESCE(COUNT(CASE WHEN uh_contratadas <= 0 THEN 1 END), 0) +
            COALESCE(COUNT(CASE WHEN vr_total_investimento <= 0 THEN 1 END), 0)
        )::NUMERIC / NULLIF(COUNT(*), 0)
        ))::NUMERIC, 2
    ) as data_quality_score,
    
    CURRENT_TIMESTAMP as ultima_verificacao
    
FROM mcmv_v2.projetos
WHERE vr_total_investimento > 0
GROUP BY programa;

-- ================================================
-- 5. REFRESH FUNCTIONS
-- ================================================

CREATE OR REPLACE FUNCTION mcmv_v5.refresh_all_materialized_views()
RETURNS TEXT AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration INTERVAL;
BEGIN
    start_time := CURRENT_TIMESTAMP;
    
    -- Refresh in dependency order
    REFRESH MATERIALIZED VIEW mcmv_v5.vw_mat_kpi_aggregations;
    REFRESH MATERIALIZED VIEW mcmv_v5.vw_mat_temporal_trends;
    REFRESH MATERIALIZED VIEW mcmv_v5.vw_data_quality_metrics;
    
    end_time := CURRENT_TIMESTAMP;
    duration := end_time - start_time;
    
    RETURN format('All materialized views refreshed successfully in %s', duration);
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- INITIAL DATA LOAD
-- ================================================

-- Refresh all materialized views
SELECT mcmv_v5.refresh_all_materialized_views();

-- Create refresh schedule (can be called by cron or app)
COMMENT ON FUNCTION mcmv_v5.refresh_all_materialized_views() IS 
'Refreshes all v5 materialized views. Call every 30 minutes for optimal performance.';