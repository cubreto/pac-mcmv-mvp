-- Migration: Create beneficiary and enhanced analytics views
-- Date: 2025-01-06
-- Description: Adds views for beneficiary tracking, contractor performance, timeline analysis, and social work

-- Create schema for PF (pessoa física) data if not exists
CREATE SCHEMA IF NOT EXISTS mcmv_pf;

-- First, we need to load the beneficiary data from RURAL.xlsx
-- This assumes the data has been loaded into tables via ETL

-- 1. Beneficiary Analytics View
CREATE OR REPLACE VIEW mcmv_pf.vw_beneficiarios_analytics AS
SELECT 
    "NU_APF",
    COUNT(*) as total_beneficiarios,
    COUNT(*) FILTER (WHERE "SG_SEXO" = 'F') as beneficiarias_mulheres,
    COUNT(*) FILTER (WHERE "SG_SEXO" = 'M') as beneficiarios_homens,
    ROUND(COUNT(*) FILTER (WHERE "SG_SEXO" = 'F')::numeric / NULLIF(COUNT(*), 0) * 100, 1) as percentual_mulheres,
    AVG("QT_SALARIO_MINIMO_RENDA_FAMILIAR_CONTRATACAO") as renda_media_sm,
    AVG("VR_COMPRA_VENDA") as valor_medio_imovel,
    AVG("VR_EVENTO") as valor_medio_pagamento,
    COUNT(*) FILTER (WHERE "VR_EVENTO" > 0) as beneficiarios_com_pagamento,
    SUM("VR_COMPRA_VENDA") as valor_total_imoveis
FROM mcmv_pf.beneficiarios_rural
GROUP BY "NU_APF";

-- 2. National beneficiary summary
CREATE OR REPLACE VIEW mcmv_pf.vw_beneficiarios_resumo_nacional AS
SELECT 
    COUNT(DISTINCT "NU_APF") as projetos_com_beneficiarios,
    COUNT(*) as total_beneficiarios,
    COUNT(*) FILTER (WHERE "SG_SEXO" = 'F') as total_mulheres,
    COUNT(*) FILTER (WHERE "SG_SEXO" = 'M') as total_homens,
    ROUND(COUNT(*) FILTER (WHERE "SG_SEXO" = 'F')::numeric / NULLIF(COUNT(*), 0) * 100, 1) as percentual_mulheres,
    AVG("QT_SALARIO_MINIMO_RENDA_FAMILIAR_CONTRATACAO") as renda_media_sm_nacional,
    AVG("VR_COMPRA_VENDA") as valor_medio_imovel_nacional,
    SUM("VR_COMPRA_VENDA") as valor_total_financiado,
    COUNT(*) FILTER (WHERE "VR_EVENTO" = 0) as inadimplentes
FROM mcmv_pf.beneficiarios_rural;

-- 3. Contractor Performance View
CREATE OR REPLACE VIEW mcmv_pj.vw_desempenho_construtoras AS
SELECT 
    COALESCE(ps.no_construtora, ps.no_eo) as entidade_executora,
    COALESCE(ps.cnpj_construtora, ps.cnpj_eo) as cnpj,
    ps.programa,
    COUNT(*) as total_projetos,
    AVG(ps.percentual_obra_realizado) as percentual_medio,
    SUM(COALESCE(ps.uh_estimadas, 0)) as total_uh,
    SUM(ps.uh_estimadas * ps.percentual_obra_realizado / 100.0) as uh_executadas,
    SUM(ps.valor_investimento) as investimento_total,
    COUNT(*) FILTER (WHERE ps.percentual_obra_realizado < 5) as projetos_paralisados,
    COUNT(*) FILTER (WHERE ps.percentual_obra_realizado >= 100) as projetos_concluidos,
    COUNT(*) FILTER (WHERE ps.percentual_obra_realizado = 0 
        AND ps.dt_contratacao < CURRENT_DATE - INTERVAL '180 days') as projetos_sem_inicio_6m,
    ROUND(AVG(EXTRACT(days FROM CURRENT_DATE - ps.dt_contratacao)), 0) as media_dias_desde_contratacao
FROM projeto_status ps
WHERE ps.tipo_programa = 'MCMV-HIS'
  AND (ps.no_construtora IS NOT NULL OR ps.no_eo IS NOT NULL)
GROUP BY 1, 2, 3
HAVING COUNT(*) > 0
ORDER BY total_projetos DESC;

-- 4. Timeline Analysis View
CREATE OR REPLACE VIEW mcmv_pj.vw_analise_prazos AS
WITH prazos AS (
    SELECT 
        programa,
        uf,
        nu_apf,
        dt_contratacao::date as data_contratacao,
        dt_inicio_obra::date as data_inicio,
        dt_previsao_conclusao_obra::date as data_previsao,
        CASE 
            WHEN dt_inicio_obra IS NOT NULL 
            THEN EXTRACT(days FROM dt_inicio_obra::date - dt_contratacao::date)
            ELSE NULL 
        END as dias_ate_inicio,
        EXTRACT(days FROM CURRENT_DATE - dt_contratacao::date) as dias_desde_contratacao,
        percentual_obra_realizado
    FROM projeto_status
    WHERE tipo_programa = 'MCMV-HIS'
      AND dt_contratacao IS NOT NULL
)
SELECT 
    programa,
    uf,
    COUNT(*) as total_projetos,
    ROUND(AVG(dias_ate_inicio), 0) as media_dias_ate_inicio,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dias_ate_inicio) as mediana_dias_ate_inicio,
    COUNT(*) FILTER (WHERE data_inicio IS NULL) as projetos_sem_inicio,
    COUNT(*) FILTER (WHERE data_inicio IS NULL AND dias_desde_contratacao > 180) as sem_inicio_6_meses,
    COUNT(*) FILTER (WHERE percentual_obra_realizado = 0 AND dias_desde_contratacao > 365) as paralisados_1_ano,
    ROUND(AVG(dias_desde_contratacao), 0) as media_dias_desde_contratacao,
    MIN(data_contratacao) as primeira_contratacao,
    MAX(data_contratacao) as ultima_contratacao
FROM prazos
GROUP BY programa, uf
ORDER BY programa, uf;

-- 5. Social Work View
CREATE OR REPLACE VIEW mcmv_pf.vw_trabalho_social AS
SELECT 
    ts."NU_APF",
    ps.programa,
    ps.uf,
    ps.no_empreendimento,
    ts."PC_PERCENTUAL_EXECUCAO_TS" as percentual_ts,
    ts."CO_SITUACAO_TRABALHO_SOCIAL" as situacao_ts,
    ts."DT_APROVACAO_PTS" as data_aprovacao,
    ts."DT_ASSINATURA_CONVENIO" as data_convenio,
    ts."DT_TERMINO_CONVENIO" as data_termino,
    ps.percentual_obra_realizado as percentual_obra,
    CASE 
        WHEN ts."PC_PERCENTUAL_EXECUCAO_TS" > ps.percentual_obra_realizado 
        THEN 'TS Adiantado'
        WHEN ts."PC_PERCENTUAL_EXECUCAO_TS" < ps.percentual_obra_realizado 
        THEN 'TS Atrasado'
        ELSE 'TS Alinhado'
    END as status_ts_obra,
    CASE
        WHEN ts."CO_SITUACAO_TRABALHO_SOCIAL" = 0 THEN 'Não Iniciado'
        WHEN ts."CO_SITUACAO_TRABALHO_SOCIAL" = 1 THEN 'Em Andamento'
        WHEN ts."CO_SITUACAO_TRABALHO_SOCIAL" = 2 THEN 'Paralisado'
        WHEN ts."CO_SITUACAO_TRABALHO_SOCIAL" = 3 THEN 'Concluído'
        ELSE 'Desconhecido'
    END as situacao_descricao
FROM mcmv_pf.trabalho_social ts
JOIN projeto_status ps ON ts."NU_APF" = ps.nu_apf
WHERE ps.tipo_programa = 'MCMV-HIS';

-- 6. Financial Execution View (enhanced)
CREATE OR REPLACE VIEW financeiro.vw_execucao_financeira AS
SELECT 
    ps.programa,
    ps.uf,
    COUNT(*) as total_projetos,
    SUM(ps.valor_investimento) as valor_comprometido,
    SUM(ps.valor_investimento * ps.percentual_obra_realizado / 100.0) as valor_executado_estimado,
    SUM(ps.valor_investimento * (1 - ps.percentual_obra_realizado / 100.0)) as valor_a_executar,
    ROUND(AVG(ps.percentual_obra_realizado), 2) as percentual_fisico_medio,
    ROUND(SUM(ps.valor_investimento * ps.percentual_obra_realizado / 100.0) / 
          NULLIF(SUM(ps.valor_investimento), 0) * 100, 2) as percentual_financeiro_executado,
    SUM(ps.uh_estimadas) as total_uh,
    ROUND(SUM(ps.valor_investimento) / NULLIF(SUM(ps.uh_estimadas), 0), 2) as custo_medio_por_uh
FROM projeto_status ps
WHERE ps.tipo_programa = 'MCMV-HIS'
  AND ps.programa IN ('FAR', 'FDS', 'RURAL')
GROUP BY ps.programa, ps.uf
ORDER BY ps.programa, ps.uf;

-- 7. Contractor Concentration Risk View
CREATE OR REPLACE VIEW mcmv_pj.vw_concentracao_construtoras AS
WITH contractor_stats AS (
    SELECT 
        COALESCE(no_construtora, no_eo) as entidade,
        COUNT(*) as num_projetos,
        SUM(uh_estimadas) as total_uh,
        SUM(valor_investimento) as total_investimento
    FROM projeto_status
    WHERE tipo_programa = 'MCMV-HIS'
      AND (no_construtora IS NOT NULL OR no_eo IS NOT NULL)
    GROUP BY 1
),
totals AS (
    SELECT 
        SUM(num_projetos) as total_projetos,
        SUM(total_uh) as total_uh_geral,
        SUM(total_investimento) as total_investimento_geral
    FROM contractor_stats
)
SELECT 
    cs.entidade,
    cs.num_projetos,
    cs.total_uh,
    cs.total_investimento,
    ROUND(cs.num_projetos::numeric / t.total_projetos * 100, 2) as percentual_projetos,
    ROUND(cs.total_uh::numeric / NULLIF(t.total_uh_geral, 0) * 100, 2) as percentual_uh,
    ROUND(cs.total_investimento / NULLIF(t.total_investimento_geral, 0) * 100, 2) as percentual_investimento,
    RANK() OVER (ORDER BY cs.num_projetos DESC) as ranking_projetos,
    RANK() OVER (ORDER BY cs.total_uh DESC) as ranking_uh,
    RANK() OVER (ORDER BY cs.total_investimento DESC) as ranking_investimento
FROM contractor_stats cs
CROSS JOIN totals t
ORDER BY cs.num_projetos DESC
LIMIT 100;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA mcmv_pf TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA mcmv_pj TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA financeiro TO postgres;

-- Add comments
COMMENT ON VIEW mcmv_pf.vw_beneficiarios_analytics IS 'Análise de beneficiários por projeto APF';
COMMENT ON VIEW mcmv_pf.vw_beneficiarios_resumo_nacional IS 'Resumo nacional dos beneficiários MCMV';
COMMENT ON VIEW mcmv_pj.vw_desempenho_construtoras IS 'Performance das construtoras e entidades organizadoras';
COMMENT ON VIEW mcmv_pj.vw_analise_prazos IS 'Análise de prazos e atrasos por programa e UF';
COMMENT ON VIEW mcmv_pf.vw_trabalho_social IS 'Acompanhamento do trabalho social vs obra física';
COMMENT ON VIEW financeiro.vw_execucao_financeira IS 'Execução financeira detalhada por programa e UF';
COMMENT ON VIEW mcmv_pj.vw_concentracao_construtoras IS 'Análise de concentração e risco por construtora';
