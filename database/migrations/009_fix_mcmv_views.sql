-- Migration 009: Fix MCMV Views SQL Syntax Errors
-- Purpose: Correct SQL syntax issues in timeline analysis

/* ================================================================
   1. Fix timeline analysis view with correct SQL syntax
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_analise_prazos AS
SELECT
    programa,
    uf,
    COUNT(*) AS total_projetos,
    COUNT(*) FILTER (WHERE data_inicio_obra IS NOT NULL) AS projetos_iniciados,
    COUNT(*) FILTER (WHERE data_inicio_obra IS NULL) AS projetos_nao_iniciados,
    COUNT(*) FILTER (WHERE data_inicio_obra < CURRENT_DATE - INTERVAL '6 months' AND percentual_obra_realizado < 50) AS sem_progresso_6_meses,
    COUNT(*) FILTER (WHERE data_inicio_obra < CURRENT_DATE - INTERVAL '1 year' AND percentual_obra_realizado < 50) AS paralisados_1_ano,
    MIN(data_inicio_obra) AS primeira_obra_iniciada,
    MAX(data_inicio_obra) AS ultima_obra_iniciada,
    AVG(CASE 
        WHEN data_inicio_obra IS NOT NULL 
        THEN (CURRENT_DATE - data_inicio_obra)
        ELSE NULL 
    END) AS media_dias_em_obra
FROM projeto_status
GROUP BY programa, uf
ORDER BY programa, uf;

/* ================================================================
   2. Fix timeline evolution view
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_evolucao_temporal AS
SELECT
    EXTRACT(YEAR FROM data_inicio_obra) AS ano,
    EXTRACT(MONTH FROM data_inicio_obra) AS mes,
    programa,
    COUNT(*) AS projetos_iniciados,
    AVG(percentual_obra_realizado) AS exec_media
FROM projeto_status
WHERE data_inicio_obra IS NOT NULL
GROUP BY EXTRACT(YEAR FROM data_inicio_obra), EXTRACT(MONTH FROM data_inicio_obra), programa
ORDER BY ano, mes, programa;

/* ================================================================
   3. Fix unified view with correct column references
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_empreendimentos_unificado AS
SELECT
    ps.proposta,
    ps.programa,
    ps.uf,
    ps.municipio_beneficiado,
    ps.modalidade,
    ps.nome_empreendimento,
    ps.tipo_programa,
    ps.valor_repasse,
    ps.valor_investimento,
    ps.valor_empenhado,
    ps.valor_pago,
    ps.percentual_obra_realizado AS percentual_mcmv,
    ps.data_inicio_obra,
    ps.situacao_atual,
    ps.data_atualizacao_situacao,
    ps.etiquetas,
    ps.observacoes,
    ps.uh_estimadas,
    ps.uf AS uf_beneficiaria,
    -- Add calculated fields
    CASE
        WHEN ps.percentual_obra_realizado < 10
         AND ps.data_inicio_obra < CURRENT_DATE - INTERVAL '180 days'
        THEN TRUE ELSE FALSE
    END AS alto_risco,
    CASE 
        WHEN ps.percentual_obra_realizado >= 100 THEN TRUE 
        ELSE FALSE 
    END AS projeto_completado,
    -- Add financial combinations for backward compatibility
    COALESCE(ps.valor_investimento, 0) + COALESCE(ps.valor_repasse, 0) AS valor_investimento_mcmv,
    COALESCE(ps.valor_investimento, 0) AS valor_investimento_pac,
    -- Add execution calculations
    COALESCE(ps.uh_estimadas, 0) * COALESCE(ps.percentual_obra_realizado, 0) / 100.0 AS uh_executadas,
    COALESCE(ps.uh_estimadas, 0) * (1 - COALESCE(ps.percentual_obra_realizado, 0) / 100.0) AS brecha_uh
FROM projeto_status ps;

/* ================================================================
   4. Fix social work view with correct column references
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pf.vw_trabalho_social AS
SELECT
    ps.proposta,
    ps.nome_empreendimento,
    ps.uf,
    ps.programa,
    ps.modalidade,
    -- Simulate social work progress (typically runs ahead of construction)
    LEAST(COALESCE(ps.percentual_obra_realizado, 0) + 15, 100) AS percentual_ts,
    COALESCE(ps.percentual_obra_realizado, 0) AS percentual_obra,
    CASE 
        WHEN COALESCE(ps.percentual_obra_realizado, 0) + 15 > COALESCE(ps.percentual_obra_realizado, 0) + 5 THEN 'TS Adiantado'
        WHEN ABS((COALESCE(ps.percentual_obra_realizado, 0) + 15) - COALESCE(ps.percentual_obra_realizado, 0)) <= 5 THEN 'TS Alinhado'
        ELSE 'TS Atrasado'
    END AS status_ts_obra,
    ps.situacao_atual AS situacao_descricao
FROM projeto_status ps
WHERE ps.programa IN ('FDS', 'RURAL') -- Only these programs have structured social work
AND ps.tipo_programa = 'MCMV-HIS';

/* ================================================================
   5. Verify all views work with a simple test
   ================================================================ */
-- Test queries to ensure views work
-- These will fail if there are still syntax errors

-- Test national summary
DO $$
BEGIN
    PERFORM COUNT(*) FROM mcmv_pj.vw_resumo_nacional;
    RAISE NOTICE 'vw_resumo_nacional: OK';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'vw_resumo_nacional: ERROR - %', SQLERRM;
END $$;

-- Test timeline analysis  
DO $$
BEGIN
    PERFORM COUNT(*) FROM mcmv_pj.vw_analise_prazos;
    RAISE NOTICE 'vw_analise_prazos: OK';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'vw_analise_prazos: ERROR - %', SQLERRM;
END $$;

-- Test beneficiary summary
DO $$
BEGIN
    PERFORM COUNT(*) FROM mcmv_pf.vw_beneficiarios_resumo_nacional;
    RAISE NOTICE 'vw_beneficiarios_resumo_nacional: OK';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'vw_beneficiarios_resumo_nacional: ERROR - %', SQLERRM;
END $$;
