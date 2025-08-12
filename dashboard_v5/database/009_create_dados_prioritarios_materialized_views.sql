-- ================================================
-- MCMV Dashboard v5 - Dados Prioritários Materialized Views
-- Purpose: Improve performance by pre-aggregating 66k+ records
-- Created: 2025-01-13
-- ================================================

-- Drop existing views if they exist
DROP MATERIALIZED VIEW IF EXISTS mcmv_v2.mv_dados_prioritarios_historico CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mcmv_v2.mv_dados_prioritarios_estado_atual CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mcmv_v2.mv_dados_prioritarios_previsao CASCADE;

-- ================================================
-- 1. DADOS HISTÓRICOS TAB - Aggregated by Program/Situação/Month
-- This view pre-aggregates all 66k records into ~500 summary rows
-- ================================================
CREATE MATERIALIZED VIEW mcmv_v2.mv_dados_prioritarios_historico AS
WITH individual_records AS (
    -- Get all records with computed fields
    SELECT 
        apf,
        modalidade as programa,
        situacao_empreendimento,
        sg_uf,
        municipio,
        nome_empreendimento,
        data_movimento,
        EXTRACT(month FROM data_movimento)::INTEGER as mes_movimento,
        EXTRACT(year FROM data_movimento)::INTEGER as ano_movimento,
        data_contratacao,
        COALESCE(uh_original_contratadas, 0)::INTEGER as uh_contratadas,
        COALESCE(uh_entregues, 0)::INTEGER as uh_entregues,
        CASE 
            WHEN COALESCE(uh_original_contratadas, 0) > 0 
            THEN ROUND((COALESCE(uh_entregues, 0)::NUMERIC / COALESCE(uh_original_contratadas, 0)::NUMERIC) * 100, 2)
            ELSE 0
        END as percentual_entregues,
        COALESCE(uh_vigentes, 0)::INTEGER as uh_vigentes,
        COALESCE(valor_contratado, 0)::NUMERIC as valor_contratado,
        COALESCE(valor_desembolsado, 0)::NUMERIC as valor_desembolsado
    FROM mcmv_v2.dados_prioritarios
)
SELECT 
    -- Grouping columns
    programa,
    situacao_empreendimento,
    ano_movimento,
    mes_movimento,
    sg_uf,
    
    -- Aggregated metrics
    COUNT(DISTINCT apf) as projetos,
    SUM(uh_contratadas) as uh_contratadas,
    SUM(uh_entregues) as uh_entregues,
    SUM(uh_vigentes) as uh_vigentes,
    SUM(valor_contratado) as valor_contratado,
    SUM(valor_desembolsado) as valor_desembolsado,
    
    -- Calculated percentage
    CASE 
        WHEN SUM(uh_contratadas) > 0 
        THEN ROUND((SUM(uh_entregues)::NUMERIC / SUM(uh_contratadas)::NUMERIC) * 100, 2)
        ELSE 0
    END as percentual_entregues,
    
    -- List of all APFs for drill-down if needed
    array_agg(DISTINCT apf) as apf_list
FROM individual_records
GROUP BY programa, situacao_empreendimento, ano_movimento, mes_movimento, sg_uf
ORDER BY ano_movimento DESC, mes_movimento DESC, programa, situacao_empreendimento;

-- Create indexes for fast filtering
CREATE INDEX idx_mv_dp_historico_programa ON mcmv_v2.mv_dados_prioritarios_historico(programa);
CREATE INDEX idx_mv_dp_historico_situacao ON mcmv_v2.mv_dados_prioritarios_historico(situacao_empreendimento);
CREATE INDEX idx_mv_dp_historico_movimento ON mcmv_v2.mv_dados_prioritarios_historico(ano_movimento, mes_movimento);
CREATE INDEX idx_mv_dp_historico_uf ON mcmv_v2.mv_dados_prioritarios_historico(sg_uf);
CREATE INDEX idx_mv_dp_historico_composite ON mcmv_v2.mv_dados_prioritarios_historico(programa, situacao_empreendimento, ano_movimento DESC, mes_movimento DESC);

-- ================================================
-- 2. ESTADO ATUAL TAB - Latest snapshot only
-- ================================================
CREATE MATERIALIZED VIEW mcmv_v2.mv_dados_prioritarios_estado_atual AS
WITH latest_date AS (
    SELECT MAX(data_movimento) as max_data_movimento
    FROM mcmv_v2.dados_prioritarios
),
aggregated_data AS (
    SELECT 
        modalidade as programa,
        situacao_empreendimento,
        sg_uf,
        COUNT(DISTINCT apf) as projetos,
        SUM(COALESCE(uh_original_contratadas, 0))::INTEGER as uh_contratadas,
        SUM(COALESCE(uh_entregues, 0))::INTEGER as uh_entregues,
        SUM(COALESCE(uh_vigentes, 0))::INTEGER as uh_vigentes,
        SUM(COALESCE(valor_contratado, 0))::NUMERIC as valor_contratado,
        SUM(COALESCE(valor_desembolsado, 0))::NUMERIC as valor_desembolsado
    FROM mcmv_v2.dados_prioritarios dp
    JOIN latest_date ld ON dp.data_movimento = ld.max_data_movimento
    GROUP BY modalidade, situacao_empreendimento, sg_uf
)
SELECT 
    programa,
    situacao_empreendimento,
    sg_uf,
    projetos,
    uh_contratadas,
    uh_entregues,
    uh_vigentes,
    valor_contratado,
    valor_desembolsado,
    CASE 
        WHEN uh_contratadas > 0 
        THEN ROUND((uh_entregues::NUMERIC / uh_contratadas::NUMERIC) * 100, 2)
        ELSE 0
    END as percentual_entregues,
    valor_contratado + valor_desembolsado as investimento_total
FROM aggregated_data
ORDER BY programa, situacao_empreendimento;

-- Create indexes
CREATE INDEX idx_mv_dp_estado_programa ON mcmv_v2.mv_dados_prioritarios_estado_atual(programa);
CREATE INDEX idx_mv_dp_estado_situacao ON mcmv_v2.mv_dados_prioritarios_estado_atual(situacao_empreendimento);
CREATE INDEX idx_mv_dp_estado_uf ON mcmv_v2.mv_dados_prioritarios_estado_atual(sg_uf);

-- ================================================
-- 3. PREVISÃO DE ENTREGA TAB - Aggregated by month
-- ================================================
CREATE MATERIALIZED VIEW mcmv_v2.mv_dados_prioritarios_previsao AS
WITH latest_by_project AS (
    SELECT DISTINCT ON (apf)
        apf,
        modalidade,
        sg_uf,
        municipio,
        nome_empreendimento,
        data_contratacao,
        data_previsao_entrega,
        COALESCE(uh_vigentes, GREATEST(0, uh_original_contratadas - COALESCE(uh_entregues, 0))) AS uh_a_entregar,
        DATE_TRUNC('month', data_previsao_entrega) as mes_entrega
    FROM mcmv_v2.dados_prioritarios
    WHERE data_previsao_entrega IS NOT NULL
    ORDER BY apf, data_movimento DESC
)
SELECT 
    TO_CHAR(mes_entrega, 'YYYY-MM') as month,
    COUNT(*) as projetos,
    SUM(uh_a_entregar) as uh_total,
    array_agg(DISTINCT modalidade) as modalidades,
    -- Additional groupings for filtering
    modalidade,
    sg_uf
FROM latest_by_project
GROUP BY mes_entrega, modalidade, sg_uf
ORDER BY mes_entrega;

-- Create indexes
CREATE INDEX idx_mv_dp_previsao_month ON mcmv_v2.mv_dados_prioritarios_previsao(month);
CREATE INDEX idx_mv_dp_previsao_modalidade ON mcmv_v2.mv_dados_prioritarios_previsao(modalidade);
CREATE INDEX idx_mv_dp_previsao_uf ON mcmv_v2.mv_dados_prioritarios_previsao(sg_uf);

-- ================================================
-- REFRESH FUNCTIONS
-- ================================================

-- Function to refresh all dados prioritarios materialized views
CREATE OR REPLACE FUNCTION mcmv_v2.refresh_dados_prioritarios_views()
RETURNS void AS $$
BEGIN
    -- Use CONCURRENTLY to avoid locking
    REFRESH MATERIALIZED VIEW CONCURRENTLY mcmv_v2.mv_dados_prioritarios_historico;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mcmv_v2.mv_dados_prioritarios_estado_atual;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mcmv_v2.mv_dados_prioritarios_previsao;
    
    -- Log the refresh
    RAISE NOTICE 'Dados Prioritários materialized views refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT ON mcmv_v2.mv_dados_prioritarios_historico TO PUBLIC;
GRANT SELECT ON mcmv_v2.mv_dados_prioritarios_estado_atual TO PUBLIC;
GRANT SELECT ON mcmv_v2.mv_dados_prioritarios_previsao TO PUBLIC;

-- Add comment for documentation
COMMENT ON MATERIALIZED VIEW mcmv_v2.mv_dados_prioritarios_historico IS 
'Pre-aggregated view for Dados Prioritários historical data. Reduces 66k+ records to ~500 aggregated rows for fast querying.';

COMMENT ON MATERIALIZED VIEW mcmv_v2.mv_dados_prioritarios_estado_atual IS 
'Latest snapshot of Dados Prioritários aggregated by program and situation.';

COMMENT ON MATERIALIZED VIEW mcmv_v2.mv_dados_prioritarios_previsao IS 
'Aggregated delivery forecast data by month for timeline visualization.';