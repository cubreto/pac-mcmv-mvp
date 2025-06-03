-- Enhanced Views for MCMV-PAC Integration
-- Answering key ministry questions with available data

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS mcmv_pj;  -- Projetos/Empreendimentos
CREATE SCHEMA IF NOT EXISTS mcmv_pf;  -- Pessoas Físicas (future)
CREATE SCHEMA IF NOT EXISTS financeiro; -- Financial movements

-- 1. Unified view for all housing projects with estimated UH
CREATE OR REPLACE VIEW mcmv_pj.vw_empreendimentos_unificado AS
SELECT 
    ps.proposta AS nu_apf,
    ps.uf,
    ps.municipio_beneficiado,
    ps.programa,
    ps.tipo_programa,
    
    -- Financial data
    COALESCE(ps.valor_repasse, 0) AS valor_repasse_mcmv,
    COALESCE(ps.valor_investimento, 0) AS valor_investimento_mcmv,
    COALESCE(po.valor_repasse, 0) AS valor_repasse_pac,
    COALESCE(po.valor_investimento, 0) AS valor_investimento_pac,
    COALESCE(po.valor_empenhado, 0) AS valor_empenhado,
    COALESCE(po.valor_desbloqueado, 0) AS valor_desbloqueado,
    
    -- Execution percentages
    COALESCE(ps.percentual_obra_realizado, 0) AS percentual_mcmv,
    COALESCE(po.percentual_realizado_reuni, 0) AS percentual_pac,
    
    -- Status and delays
    ps.situacao_atual AS situacao_mcmv,
    po.situacao_atual AS situacao_pac,
    ps.data_inicio_obra,
    ps.data_atualizacao_situacao,
    po.vencimento_da_suspensiva,
    po.dias_sem_movimentacao,
    
    -- Calculate estimated housing units based on program averages
    -- Note: These are estimates based on sample data ratios
    CASE 
        WHEN ps.programa IN ('FAR', 'MCMV-FAR') THEN 168  -- 133440 total / 793 sample
        WHEN ps.programa IN ('FDS', 'MCMV-Entidades') THEN 226  -- 24606 total / 109 sample
        WHEN ps.programa IN ('Rural', 'MCMV-Rural', 'PNHR') THEN 70  -- 30729 total / 438 sample
        ELSE 100  -- Default estimate
    END AS uh_estimadas,
    
    -- Integration and risk flags
    CASE WHEN po.operacao IS NOT NULL THEN TRUE ELSE FALSE END AS has_pac,
    CASE WHEN po.vencimento_da_suspensiva < CURRENT_DATE THEN TRUE ELSE FALSE END AS suspensiva_vencida,
    CASE WHEN ps.percentual_obra_realizado < 10 AND 
              ps.data_inicio_obra < CURRENT_DATE - INTERVAL '180 days' 
         THEN TRUE ELSE FALSE END AS alto_risco
    
FROM projeto_status ps
LEFT JOIN pac_operations po ON ps.proposta = po.proposta;

-- 2. UH Gap Analysis by State and Program
CREATE OR REPLACE VIEW mcmv_pj.vw_brecha_uh_por_uf AS
SELECT 
    uf,
    programa,
    COUNT(*) AS total_projetos,
    SUM(uh_estimadas) AS uh_esperadas,
    SUM(uh_estimadas * percentual_mcmv / 100.0) AS uh_executadas,
    SUM(uh_estimadas * (1 - percentual_mcmv / 100.0)) AS brecha_uh,
    AVG(percentual_mcmv) AS percentual_medio,
    SUM(CASE WHEN has_pac THEN 1 ELSE 0 END) AS projetos_com_pac,
    SUM(CASE WHEN alto_risco THEN 1 ELSE 0 END) AS projetos_alto_risco
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa
ORDER BY uf, programa;

-- 3. National Summary
CREATE OR REPLACE VIEW mcmv_pj.vw_resumo_nacional AS
SELECT 
    COUNT(*) AS total_projetos,
    SUM(uh_estimadas) AS uh_esperadas_total,
    SUM(uh_estimadas * percentual_mcmv / 100.0) AS uh_executadas_total,
    SUM(uh_estimadas * (1 - percentual_mcmv / 100.0)) AS brecha_uh_nacional,
    AVG(percentual_mcmv) AS percentual_medio_nacional,
    SUM(valor_investimento_mcmv + valor_investimento_pac) AS investimento_total,
    SUM(valor_empenhado) AS empenhado_total,
    SUM(valor_desbloqueado) AS desbloqueado_total,
    SUM(CASE WHEN has_pac THEN 1 ELSE 0 END) AS projetos_integrados,
    SUM(CASE WHEN alto_risco THEN 1 ELSE 0 END) AS projetos_alto_risco,
    SUM(CASE WHEN suspensiva_vencida THEN 1 ELSE 0 END) AS suspensivas_vencidas
FROM mcmv_pj.vw_empreendimentos_unificado;

-- 4. Financial Flow Analysis
CREATE OR REPLACE VIEW financeiro.vw_fluxo_consolidado AS
SELECT 
    uf,
    programa,
    COUNT(*) AS num_projetos,
    SUM(valor_investimento_mcmv) AS investimento_mcmv,
    SUM(valor_investimento_pac) AS investimento_pac,
    SUM(valor_investimento_mcmv + valor_investimento_pac) AS investimento_total,
    SUM(valor_repasse_mcmv + valor_repasse_pac) AS repasse_total,
    SUM(valor_empenhado) AS empenhado,
    SUM(valor_desbloqueado) AS desbloqueado,
    -- Financial execution rate
    CASE 
        WHEN SUM(valor_investimento_mcmv + valor_investimento_pac) > 0 
        THEN SUM(valor_desbloqueado) * 100.0 / 
             SUM(valor_investimento_mcmv + valor_investimento_pac)
        ELSE 0 
    END AS taxa_execucao_financeira,
    -- Empenho rate
    CASE 
        WHEN SUM(valor_investimento_pac) > 0 
        THEN SUM(valor_empenhado) * 100.0 / SUM(valor_investimento_pac)
        ELSE 0 
    END AS taxa_empenho
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa
ORDER BY investimento_total DESC;

-- 5. Risk Analysis View
CREATE OR REPLACE VIEW mcmv_pj.vw_analise_risco AS
SELECT 
    uf,
    programa,
    COUNT(*) AS total_projetos,
    SUM(CASE WHEN percentual_mcmv < 10 THEN 1 ELSE 0 END) AS projetos_inicio,
    SUM(CASE WHEN percentual_mcmv BETWEEN 10 AND 30 THEN 1 ELSE 0 END) AS projetos_andamento_inicial,
    SUM(CASE WHEN percentual_mcmv BETWEEN 30 AND 70 THEN 1 ELSE 0 END) AS projetos_meio,
    SUM(CASE WHEN percentual_mcmv BETWEEN 70 AND 90 THEN 1 ELSE 0 END) AS projetos_finalizacao,
    SUM(CASE WHEN percentual_mcmv >= 90 THEN 1 ELSE 0 END) AS projetos_concluidos,
    SUM(CASE WHEN alto_risco THEN 1 ELSE 0 END) AS alto_risco,
    SUM(CASE WHEN suspensiva_vencida THEN 1 ELSE 0 END) AS suspensivas_vencidas,
    SUM(CASE WHEN dias_sem_movimentacao > 90 THEN 1 ELSE 0 END) AS parados_90_dias,
    AVG(dias_sem_movimentacao) AS media_dias_parado
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa;

-- 6. Execution Timeline View (for cohort analysis)
CREATE OR REPLACE VIEW mcmv_pj.vw_evolucao_temporal AS
SELECT 
    EXTRACT(YEAR FROM data_inicio_obra) AS ano_inicio,
    EXTRACT(MONTH FROM data_inicio_obra) AS mes_inicio,
    programa,
    COUNT(*) AS projetos_iniciados,
    AVG(percentual_mcmv) AS percentual_medio,
    SUM(uh_estimadas) AS uh_coorte,
    AVG(EXTRACT(EPOCH FROM (CURRENT_DATE - data_inicio_obra))/86400) AS dias_desde_inicio
FROM mcmv_pj.vw_empreendimentos_unificado
WHERE data_inicio_obra IS NOT NULL
GROUP BY ano_inicio, mes_inicio, programa
ORDER BY ano_inicio, mes_inicio;

-- 7. Integration Performance View
CREATE OR REPLACE VIEW mcmv_pj.vw_performance_integracao AS
SELECT 
    uf,
    COUNT(*) FILTER (WHERE has_pac) AS projetos_com_pac,
    COUNT(*) FILTER (WHERE NOT has_pac) AS projetos_sem_pac,
    AVG(percentual_mcmv) FILTER (WHERE has_pac) AS exec_media_com_pac,
    AVG(percentual_mcmv) FILTER (WHERE NOT has_pac) AS exec_media_sem_pac,
    SUM(valor_investimento_mcmv + valor_investimento_pac) FILTER (WHERE has_pac) AS invest_com_pac,
    SUM(valor_investimento_mcmv) FILTER (WHERE NOT has_pac) AS invest_sem_pac
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projeto_status_programa ON projeto_status(programa);
CREATE INDEX IF NOT EXISTS idx_projeto_status_uf ON projeto_status(uf);
CREATE INDEX IF NOT EXISTS idx_pac_operations_proposta ON pac_operations(proposta);

-- Grant permissions (adjust as needed)
GRANT USAGE ON SCHEMA mcmv_pj TO postgres;
GRANT USAGE ON SCHEMA financeiro TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA mcmv_pj TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA financeiro TO postgres;
