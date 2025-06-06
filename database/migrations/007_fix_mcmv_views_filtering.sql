-- Fix views to properly filter MCMV-HIS data only

-- 1. Fix national summary to only include MCMV-HIS
CREATE OR REPLACE VIEW mcmv_pj.vw_resumo_nacional AS
SELECT
    COUNT(*) AS total_projetos,
    SUM(valor_investimento) AS investimento_total,
    AVG(percentual_obra_realizado) AS percentual_medio_nacional,
    COUNT(*) FILTER (WHERE percentual_obra_realizado < 10 AND data_inicio_obra < CURRENT_DATE - INTERVAL '180 days') AS projetos_alto_risco,
    SUM(uh_estimadas) AS uh_esperadas_total,
    SUM(uh_estimadas * percentual_obra_realizado / 100.0) AS uh_executadas_total,
    SUM(uh_estimadas * (1 - percentual_obra_realizado / 100.0)) AS brecha_uh_nacional,
    COUNT(*) FILTER (WHERE percentual_obra_realizado >= 100) AS projetos_completados,
    SUM(valor_empenhado) AS valor_empenhado_total,
    SUM(valor_pago) AS valor_pago_total,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            COUNT(*) FILTER (WHERE percentual_obra_realizado >= 100) * 100.0 / COUNT(*)
        ELSE 0 
    END AS taxa_conclusao,
    CASE 
        WHEN SUM(valor_empenhado) > 0 THEN 
            SUM(valor_pago) * 100.0 / SUM(valor_empenhado)
        ELSE 0 
    END AS taxa_pagamento
FROM projeto_status
WHERE tipo_programa = 'MCMV-HIS';

-- 2. Fix UH gap view to filter MCMV-HIS only
CREATE OR REPLACE VIEW mcmv_pj.vw_brecha_uh_por_uf AS
SELECT
    uf,
    programa,
    COUNT(*) AS qt_projetos,
    SUM(uh_estimadas) AS uh_esperadas,
    SUM(uh_estimadas * percentual_obra_realizado / 100.0) AS uh_executadas,
    SUM(uh_estimadas * (1 - percentual_obra_realizado / 100.0)) AS brecha_uh,
    AVG(percentual_obra_realizado) AS percentual_medio,
    SUM(valor_investimento) AS investimento_total,
    COUNT(*) FILTER (WHERE percentual_obra_realizado < 10 AND data_inicio_obra < CURRENT_DATE - INTERVAL '180 days') AS qt_alto_risco
FROM projeto_status
WHERE tipo_programa = 'MCMV-HIS'
GROUP BY uf, programa
ORDER BY uf, programa;

-- 3. Fix state performance view to filter MCMV-HIS only
CREATE OR REPLACE VIEW mcmv_pj.vw_desempenho_por_estado AS
SELECT 
    uf,
    COUNT(*) AS total_projetos,
    COUNT(DISTINCT programa) AS programas_ativos,
    SUM(uh_estimadas) AS total_uh,
    SUM(uh_estimadas * percentual_obra_realizado / 100.0) AS uh_executadas,
    ROUND(AVG(percentual_obra_realizado)::numeric, 2) AS percentual_medio,
    SUM(valor_investimento) AS investimento_total,
    COUNT(*) FILTER (WHERE percentual_obra_realizado < 5) AS projetos_paralisados,
    COUNT(*) FILTER (WHERE percentual_obra_realizado >= 100) AS projetos_concluidos
FROM projeto_status
WHERE tipo_programa = 'MCMV-HIS'
  AND uf IS NOT NULL
GROUP BY uf
ORDER BY percentual_medio DESC;

COMMENT ON VIEW mcmv_pj.vw_resumo_nacional IS 'Resumo nacional APENAS para projetos MCMV-HIS (exclui PAC)';
COMMENT ON VIEW mcmv_pj.vw_brecha_uh_por_uf IS 'Brecha de UH APENAS para projetos MCMV-HIS';
COMMENT ON VIEW mcmv_pj.vw_desempenho_por_estado IS 'Desempenho por estado APENAS para projetos MCMV-HIS';
