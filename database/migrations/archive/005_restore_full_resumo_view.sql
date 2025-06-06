-- 005_restore_full_resumo_view.sql
-- Recreates vw_resumo_nacional with all columns expected by dashboard.py
-- while still filtering to the eight MCMV programs.

DROP VIEW IF EXISTS mcmv_pj.vw_resumo_nacional;

CREATE VIEW mcmv_pj.vw_resumo_nacional AS
WITH stats AS (
  SELECT
      COUNT(*) AS total_projetos,
      SUM(uh_estimadas) AS uh_esperadas_total,
      SUM(uh_estimadas * percentual_mcmv / 100) AS uh_executadas_total,
      SUM(uh_estimadas * (1 - percentual_mcmv / 100)) AS brecha_uh_nacional,

      AVG(percentual_mcmv) AS percentual_medio_nacional,

      SUM(COALESCE(valor_investimento_mcmv,0) +
          COALESCE(valor_investimento_pac,0)) AS investimento_total,
      SUM(valor_empenhado)       AS empenhado_total,
      SUM(valor_desbloqueado)    AS desbloqueado_total,

      COUNT(*) FILTER (WHERE has_pac)              AS projetos_integrados,
      COUNT(*) FILTER (WHERE alto_risco)           AS projetos_alto_risco,
      COUNT(*) FILTER (WHERE suspensiva_vencida)   AS suspensivas_vencidas
  FROM mcmv_pj.vw_empreendimentos_unificado
  WHERE programa IN (
        'FAR','FDS','RURAL',
        'Minha Casa Minha Vida - Faixa 1',
        'Minha Casa Minha Vida - Faixa 2',
        'Minha Casa Minha Vida - Faixa 3',
        'Casa Verde e Amarela','Habitação Rural')
)
SELECT * FROM stats;
