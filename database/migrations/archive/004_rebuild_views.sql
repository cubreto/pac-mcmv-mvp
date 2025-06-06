/* ================================================================
   0.  make sure the helper schemas exist
   ================================================================ */
CREATE SCHEMA IF NOT EXISTS mcmv_pj;
CREATE SCHEMA IF NOT EXISTS financeiro;

/* ================================================================
   1.  drop old material (if present)
   ================================================================ */
DROP VIEW IF EXISTS financeiro.vw_fluxo_consolidado           CASCADE;
DROP VIEW IF EXISTS mcmv_pj.vw_analise_risco                  CASCADE;
DROP VIEW IF EXISTS mcmv_pj.vw_brecha_uh_por_uf               CASCADE;
DROP VIEW IF EXISTS mcmv_pj.vw_evolucao_temporal              CASCADE;
DROP VIEW IF EXISTS mcmv_pj.vw_performance_integracao         CASCADE;
DROP VIEW IF EXISTS mcmv_pj.vw_resumo_nacional                CASCADE;
DROP VIEW IF EXISTS mcmv_pj.vw_empreendimentos_unificado      CASCADE;

/* ================================================================
   2.  tighten the table definition (indexes)
   ================================================================ */
-- remove any outdated ones
DROP INDEX IF EXISTS idx_projeto_status_programa;
DROP INDEX IF EXISTS idx_projeto_status_uf;

-- create fresh helper indexes
CREATE INDEX idx_projeto_status_programa   ON projeto_status(programa);
CREATE INDEX idx_projeto_status_uf         ON projeto_status(uf);
CREATE INDEX idx_projeto_status_modalidade ON projeto_status(modalidade);

/* ================================================================
   3.  unified MCMV view (the work-horse for every other view)
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
    ps.percentual_obra_realizado      AS percentual_mcmv,
    ps.data_inicio_obra,
    ps.situacao_atual,
    ps.data_atualizacao_situacao,
    ps.etiquetas,
    ps.observacoes,
    /* simple “risk” flag – tweak as you like */
    CASE
        WHEN ps.percentual_obra_realizado < 10
         AND ps.data_inicio_obra < CURRENT_DATE - INTERVAL '180 days'
        THEN TRUE ELSE FALSE
    END                                    AS alto_risco
FROM projeto_status ps;

/* ================================================================
   4.  national summary
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_resumo_nacional AS
SELECT
    COUNT(*)                                  AS total_projetos,
    SUM(valor_investimento)                   AS investimento_total,
    AVG(percentual_mcmv)                      AS percentual_medio_nacional,
    COUNT(*) FILTER (WHERE alto_risco)        AS projetos_alto_risco
FROM mcmv_pj.vw_empreendimentos_unificado;

/* ================================================================
   5.  gap / performance by UF
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_brecha_uh_por_uf AS
SELECT
    uf,
    programa,
    COUNT(*)                            AS qt_projetos,
    SUM(valor_investimento)             AS investimento_total,
    AVG(percentual_mcmv)                AS exec_media,
    COUNT(*) FILTER (WHERE alto_risco)  AS qt_alto_risco
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa
ORDER BY uf, programa;

/* ================================================================
   6.  simple financial consolidation (can be refined later)
   ================================================================ */
CREATE OR REPLACE VIEW financeiro.vw_fluxo_consolidado AS
SELECT
    uf,
    programa,
    SUM(valor_investimento)              AS investimento_total,
    SUM(valor_empenhado)                 AS empenhado_total,
    SUM(valor_pago)                      AS pago_total,
    CASE
        WHEN SUM(valor_empenhado) = 0 THEN 0
        ELSE ROUND(SUM(valor_pago)::numeric
                   / NULLIF(SUM(valor_empenhado),0) * 100, 1)
    END                                  AS perc_pago_vs_empenhado
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY uf, programa
ORDER BY uf, programa;

/* ================================================================
   7.  very light timeline (year-month)
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_evolucao_temporal AS
SELECT
    EXTRACT(YEAR  FROM data_inicio_obra)      AS ano,
    EXTRACT(MONTH FROM data_inicio_obra)      AS mes,
    programa,
    COUNT(*)                                  AS projetos_iniciados,
    AVG(percentual_mcmv)                      AS exec_media
FROM mcmv_pj.vw_empreendimentos_unificado
WHERE data_inicio_obra IS NOT NULL
GROUP BY 1,2,3
ORDER BY 1,2,3;

/* ================================================================
   8.  risk list (for dashboards’ “Análise de Risco” tab)
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_analise_risco AS
SELECT *
FROM   mcmv_pj.vw_empreendimentos_unificado
WHERE  alto_risco = TRUE;

/* ================================================================
   9.  integration performance stub (kept for old dashboards)
   ================================================================ */
CREATE OR REPLACE VIEW mcmv_pj.vw_performance_integracao AS
SELECT
    programa,
    COUNT(*)                             AS qt_projetos,
    AVG(percentual_mcmv)                 AS exec_media
FROM mcmv_pj.vw_empreendimentos_unificado
GROUP BY programa;

