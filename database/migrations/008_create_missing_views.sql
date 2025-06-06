-- Create the missing views that the enhanced dashboard expects

-- 1. Create the unified enterprises view (key view that dashboard needs)
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
    END AS projeto_completado
FROM projeto_status ps
WHERE ps.tipo_programa = 'MCMV-HIS'
AND ps.programa IN ('FAR', 'FDS', 'RURAL');

-- 2. Create financial flow view if missing
CREATE OR REPLACE VIEW financeiro.vw_fluxo_consolidado AS
SELECT
    uf,
    programa,
    SUM(valor_investimento) AS investimento_total,
    SUM(valor_empenhado) AS empenhado,
    SUM(valor_pago) AS desbloqueado,
    CASE
        WHEN SUM(valor_empenhado) = 0 THEN 0
        ELSE SUM(valor_pago) * 100.0 / NULLIF(SUM(valor_empenhado), 0)
    END AS taxa_execucao_financeira
FROM projeto_status
WHERE tipo_programa = 'MCMV-HIS'
AND programa IN ('FAR', 'FDS', 'RURAL')
GROUP BY uf, programa
ORDER BY uf, programa;

-- 3. Update the UH gap view to use the unified view
CREATE OR REPLACE VIEW mcmv_pj.vw_brecha_uh_por_uf AS
SELECT
    uf,
    programa,
    COUNT(*) AS qt_projetos,
    SUM(uh_estimadas) AS uh_esperadas,
    SUM(uh_estimadas * percentual_mcmv / 100.0) AS uh_executadas,
    SUM(uh_estimadas * (1 - percentual_mcmv / 100.0)) AS brecha_uh,
    AVG(percentual_mcmv) AS percentual_medio,
    SUM(valor_investimento) AS investimento_total,
    COUNT(*) FILTER (WHERE alto_risco) AS qt_alto_risco
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa
ORDER BY uf, programa;

-- 4. Update national summary to use unified view
CREATE OR REPLACE VIEW mcmv_pj.vw_resumo_nacional AS
SELECT
    COUNT(*) AS total_projetos,
    SUM(valor_investimento) AS investimento_total,
    AVG(percentual_mcmv) AS percentual_medio_nacional,
    COUNT(*) FILTER (WHERE alto_risco) AS projetos_alto_risco,
    SUM(uh_estimadas) AS uh_esperadas_total,
    SUM(uh_estimadas * percentual_mcmv / 100.0) AS uh_executadas_total,
    SUM(uh_estimadas * (1 - percentual_mcmv / 100.0)) AS brecha_uh_nacional,
    COUNT(*) FILTER (WHERE projeto_completado) AS projetos_completados,
    SUM(valor_empenhado) AS valor_empenhado_total,
    SUM(valor_pago) AS valor_pago_total,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            COUNT(*) FILTER (WHERE projeto_completado) * 100.0 / COUNT(*)
        ELSE 0 
    END AS taxa_conclusao,
    CASE 
        WHEN SUM(valor_empenhado) > 0 THEN 
            SUM(valor_pago) * 100.0 / SUM(valor_empenhado)
        ELSE 0 
    END AS taxa_pagamento
FROM mcmv_pj.vw_empreendimentos_unificado;

-- 5. Update state performance to use unified view
CREATE OR REPLACE VIEW mcmv_pj.vw_desempenho_por_estado AS
SELECT 
    uf,
    COUNT(*) AS total_projetos,
    COUNT(DISTINCT programa) AS programas_ativos,
    SUM(uh_estimadas) AS total_uh,
    SUM(uh_estimadas * percentual_mcmv / 100.0) AS uh_executadas,
    ROUND(AVG(percentual_mcmv)::numeric, 2) AS percentual_medio,
    SUM(valor_investimento) AS investimento_total,
    COUNT(*) FILTER (WHERE percentual_mcmv < 5) AS projetos_paralisados,
    COUNT(*) FILTER (WHERE projeto_completado) AS projetos_concluidos
FROM mcmv_pj.vw_empreendimentos_unificado
WHERE uf IS NOT NULL
GROUP BY uf
ORDER BY percentual_medio DESC;

-- 6. Update program summary to use unified view
CREATE OR REPLACE VIEW mcmv_pj.vw_resumo_programa AS
SELECT 
    programa,
    COUNT(*) as total_projetos,
    SUM(uh_estimadas) as total_uh_planejadas,
    SUM(uh_estimadas * percentual_mcmv / 100.0) as total_uh_executadas,
    ROUND(AVG(percentual_mcmv)::numeric, 2) as percentual_medio_execucao,
    SUM(valor_investimento) as investimento_total,
    COUNT(*) FILTER (WHERE percentual_mcmv = 0) as projetos_nao_iniciados,
    COUNT(*) FILTER (WHERE percentual_mcmv > 0 AND percentual_mcmv < 100) as projetos_em_andamento,
    COUNT(*) FILTER (WHERE projeto_completado) as projetos_concluidos,
    COUNT(DISTINCT uf) as estados_atendidos
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY programa
ORDER BY total_projetos DESC;

-- Add comments
COMMENT ON VIEW mcmv_pj.vw_empreendimentos_unificado IS 'View unificada de empreendimentos MCMV para o dashboard enhanced';
COMMENT ON VIEW financeiro.vw_fluxo_consolidado IS 'Fluxo financeiro consolidado por UF e programa';
