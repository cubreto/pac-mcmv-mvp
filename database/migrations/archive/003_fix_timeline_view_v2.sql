-- Fix the execution timeline view - simpler version
CREATE OR REPLACE VIEW mcmv_pj.vw_evolucao_temporal AS
SELECT 
    EXTRACT(YEAR FROM data_inicio_obra) AS ano_inicio,
    EXTRACT(MONTH FROM data_inicio_obra) AS mes_inicio,
    programa,
    COUNT(*) AS projetos_iniciados,
    AVG(percentual_mcmv) AS percentual_medio,
    SUM(uh_estimadas) AS uh_coorte,
    AVG(CURRENT_DATE - data_inicio_obra::date) AS dias_desde_inicio
FROM mcmv_pj.vw_empreendimentos_unificado
WHERE data_inicio_obra IS NOT NULL
GROUP BY ano_inicio, mes_inicio, programa
ORDER BY ano_inicio, mes_inicio;
