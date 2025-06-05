-- Migration: Fix MCMV views to use real UH data
-- Date: 2025-01-06
-- Description: Updates views to use actual uh_estimadas column instead of hardcoded values

-- 1. Update the main unified view to use real UH values
CREATE OR REPLACE VIEW mcmv_pj.vw_empreendimentos_unificado AS
SELECT 
    ps.proposta AS nu_apf,
    ps.uf,
    ps.municipio_beneficiado,
    ps.programa,
    ps.tipo_programa,
    COALESCE(ps.valor_repasse, 0::double precision) AS valor_repasse_mcmv,
    COALESCE(ps.valor_investimento, 0::double precision) AS valor_investimento_mcmv,
    COALESCE(po.valor_repasse, 0::double precision) AS valor_repasse_pac,
    COALESCE(po.valor_investimento, 0::double precision) AS valor_investimento_pac,
    COALESCE(po.valor_empenhado, 0::double precision) AS valor_empenhado,
    COALESCE(po.valor_desbloqueado, 0::double precision) AS valor_desbloqueado,
    COALESCE(ps.percentual_obra_realizado, 0::double precision) AS percentual_mcmv,
    COALESCE(po.percentual_realizado_reuni, 0::double precision) AS percentual_pac,
    ps.situacao_atual AS situacao_mcmv,
    po.situacao_atual AS situacao_pac,
    ps.data_inicio_obra,
    ps.data_atualizacao_situacao,
    po.vencimento_da_suspensiva,
    CASE
        WHEN po.dias_sem_movimentacao IS NOT NULL THEN po.dias_sem_movimentacao::integer
        ELSE 0
    END AS dias_sem_movimentacao,
    COALESCE(ps.uh_estimadas, 0) AS uh_estimadas,  -- USE REAL VALUES!
    CASE
        WHEN po.operacao IS NOT NULL THEN true
        ELSE false
    END AS has_pac,
    CASE
        WHEN po.vencimento_da_suspensiva < CURRENT_DATE THEN true
        ELSE false
    END AS suspensiva_vencida,
    CASE
        WHEN ps.percentual_obra_realizado < 20::double precision 
         AND ps.data_atualizacao_situacao < (CURRENT_DATE - '180 days'::interval) THEN true
        ELSE false
    END AS alto_risco
FROM projeto_status ps
LEFT JOIN pac_operations po ON ps.proposta = po.operacao::text;

-- 2. Recreate dependent views (they depend on vw_empreendimentos_unificado)
-- Note: These don't need changes, but we recreate them to ensure consistency

-- National summary view
CREATE OR REPLACE VIEW mcmv_pj.vw_resumo_nacional AS
WITH stats AS (
    SELECT 
        COUNT(*) as total_projetos,
        SUM(uh_estimadas) as uh_esperadas_total,
        SUM(uh_estimadas * percentual_mcmv / 100.0) as uh_executadas_total,
        AVG(percentual_mcmv) as percentual_medio_nacional,
        SUM(valor_investimento_mcmv + valor_investimento_pac) as investimento_total,
        SUM(valor_empenhado) as empenhado_total,
        SUM(valor_desbloqueado) as desbloqueado_total,
        COUNT(*) FILTER (WHERE has_pac) as projetos_integrados,
        COUNT(*) FILTER (WHERE alto_risco) as projetos_alto_risco,
        COUNT(*) FILTER (WHERE suspensiva_vencida) as suspensivas_vencidas
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN ('FAR', 'FDS', 'RURAL', 'Minha Casa Minha Vida - Faixa 1', 
                       'Minha Casa Minha Vida - Faixa 2', 'Minha Casa Minha Vida - Faixa 3',
                       'Casa Verde e Amarela', 'Habitação Rural')
)
SELECT 
    *,
    uh_esperadas_total - uh_executadas_total as brecha_uh_nacional
FROM stats;

-- UH gap by state view
CREATE OR REPLACE VIEW mcmv_pj.vw_brecha_uh_por_uf AS
SELECT 
    uf,
    programa,
    SUM(uh_estimadas) as uh_esperadas,
    SUM(uh_estimadas * percentual_mcmv / 100.0) as uh_executadas,
    SUM(uh_estimadas * (1 - percentual_mcmv / 100.0)) as brecha_uh,
    AVG(percentual_mcmv) as percentual_medio
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa
ORDER BY uf, programa;

-- Financial flow view
CREATE OR REPLACE VIEW financeiro.vw_fluxo_consolidado AS
SELECT 
    uf,
    programa,
    SUM(valor_investimento_mcmv + valor_investimento_pac) as investimento_total,
    SUM(valor_empenhado) as empenhado,
    SUM(valor_desbloqueado) as desbloqueado,
    AVG(percentual_mcmv) as taxa_execucao_financeira
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA mcmv_pj TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA financeiro TO postgres;

-- Add comment to track migration
COMMENT ON VIEW mcmv_pj.vw_empreendimentos_unificado IS 'Updated 2025-01-06: Now uses real uh_estimadas from projeto_status table';
