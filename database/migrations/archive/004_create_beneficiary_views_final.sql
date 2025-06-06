-- Migration: Create beneficiary and enhanced analytics views (FINAL)
-- Date: 2025-01-06
-- Description: Adds views for beneficiary tracking and analytics - fixed date calculations

-- Create schema for PF (pessoa física) data if not exists
CREATE SCHEMA IF NOT EXISTS mcmv_pf;

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

-- 3. Project Performance View (simplified without contractor data)
CREATE OR REPLACE VIEW mcmv_pj.vw_desempenho_projetos AS
SELECT 
    ps.programa,
    ps.uf,
    COUNT(*) as total_projetos,
    AVG(ps.percentual_obra_realizado) as percentual_medio,
    SUM(COALESCE(ps.uh_estimadas, 0)) as total_uh,
    SUM(ps.uh_estimadas * ps.percentual_obra_realizado / 100.0) as uh_executadas,
    SUM(ps.valor_investimento) as investimento_total,
    COUNT(*) FILTER (WHERE ps.percentual_obra_realizado < 5) as projetos_paralisados,
    COUNT(*) FILTER (WHERE ps.percentual_obra_realizado >= 100) as projetos_concluidos,
    COUNT(*) FILTER (WHERE ps.percentual_obra_realizado = 0 
        AND ps.data_inicio_obra < CURRENT_DATE - INTERVAL '180 days') as projetos_sem_progresso_6m,
    ROUND(AVG(CASE 
        WHEN ps.data_inicio_obra IS NOT NULL 
        THEN DATE_PART('day', CURRENT_DATE - ps.data_inicio_obra::date)
        ELSE NULL 
    END)::numeric, 0) as media_dias_em_obra
FROM projeto_status ps
WHERE ps.tipo_programa = 'MCMV-HIS'
GROUP BY ps.programa, ps.uf
ORDER BY ps.programa, ps.uf;

-- 4. Timeline Analysis View (fixed date calculations)
CREATE OR REPLACE VIEW mcmv_pj.vw_analise_prazos AS
WITH prazos AS (
    SELECT 
        programa,
        uf,
        proposta,
        data_inicio_obra::date as data_inicio,
        DATE_PART('day', CURRENT_DATE - data_inicio_obra::date) as dias_desde_inicio,
        percentual_obra_realizado
    FROM projeto_status
    WHERE tipo_programa = 'MCMV-HIS'
      AND data_inicio_obra IS NOT NULL
)
SELECT 
    programa,
    uf,
    COUNT(*) as total_projetos_iniciados,
    ROUND(AVG(dias_desde_inicio)::numeric, 0) as media_dias_desde_inicio,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dias_desde_inicio) as mediana_dias_desde_inicio,
    COUNT(*) FILTER (WHERE percentual_obra_realizado = 0) as projetos_sem_progresso,
    COUNT(*) FILTER (WHERE percentual_obra_realizado = 0 AND dias_desde_inicio > 180) as sem_progresso_6_meses,
    COUNT(*) FILTER (WHERE percentual_obra_realizado = 0 AND dias_desde_inicio > 365) as paralisados_1_ano,
    MIN(data_inicio) as primeira_obra_iniciada,
    MAX(data_inicio) as ultima_obra_iniciada
FROM prazos
GROUP BY programa, uf
ORDER BY programa, uf;

-- 5. Social Work View (fixed join)
CREATE OR REPLACE VIEW mcmv_pf.vw_trabalho_social AS
SELECT 
    ts."NU_APF",
    ts.programa,
    ps.uf,
    ps.nome_empreendimento,
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
JOIN projeto_status ps ON ts."NU_APF"::text = ps.proposta
WHERE ps.tipo_programa = 'MCMV-HIS';

-- 6. Financial Execution View (fixed ROUND function)
CREATE OR REPLACE VIEW financeiro.vw_execucao_financeira AS
SELECT 
    ps.programa,
    ps.uf,
    COUNT(*) as total_projetos,
    SUM(ps.valor_investimento) as valor_comprometido,
    SUM(ps.valor_investimento * ps.percentual_obra_realizado / 100.0) as valor_executado_estimado,
    SUM(ps.valor_investimento * (1 - ps.percentual_obra_realizado / 100.0)) as valor_a_executar,
    ROUND(AVG(ps.percentual_obra_realizado)::numeric, 2) as percentual_fisico_medio,
    ROUND((SUM(ps.valor_investimento * ps.percentual_obra_realizado / 100.0) / 
          NULLIF(SUM(ps.valor_investimento), 0) * 100)::numeric, 2) as percentual_financeiro_executado,
    SUM(ps.uh_estimadas) as total_uh,
    ROUND((SUM(ps.valor_investimento) / NULLIF(SUM(ps.uh_estimadas), 0))::numeric, 2) as custo_medio_por_uh
FROM projeto_status ps
WHERE ps.tipo_programa = 'MCMV-HIS'
  AND ps.programa IN ('FAR', 'FDS', 'RURAL')
GROUP BY ps.programa, ps.uf
ORDER BY ps.programa, ps.uf;

-- 7. Program Summary View
CREATE OR REPLACE VIEW mcmv_pj.vw_resumo_programa AS
SELECT 
    programa,
    COUNT(*) as total_projetos,
    SUM(uh_estimadas) as total_uh_planejadas,
    SUM(uh_estimadas * percentual_obra_realizado / 100.0) as total_uh_executadas,
    ROUND(AVG(percentual_obra_realizado)::numeric, 2) as percentual_medio_execucao,
    SUM(valor_investimento) as investimento_total,
    COUNT(*) FILTER (WHERE percentual_obra_realizado = 0) as projetos_nao_iniciados,
    COUNT(*) FILTER (WHERE percentual_obra_realizado > 0 AND percentual_obra_realizado < 100) as projetos_em_andamento,
    COUNT(*) FILTER (WHERE percentual_obra_realizado >= 100) as projetos_concluidos,
    COUNT(DISTINCT uf) as estados_atendidos
FROM projeto_status
WHERE tipo_programa = 'MCMV-HIS'
  AND programa IN ('FAR', 'FDS', 'RURAL')
GROUP BY programa
ORDER BY total_projetos DESC;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA mcmv_pf TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA mcmv_pj TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA financeiro TO postgres;

-- Add comments
COMMENT ON VIEW mcmv_pf.vw_beneficiarios_analytics IS 'Análise de beneficiários por projeto APF';
COMMENT ON VIEW mcmv_pf.vw_beneficiarios_resumo_nacional IS 'Resumo nacional dos beneficiários MCMV';
COMMENT ON VIEW mcmv_pj.vw_desempenho_projetos IS 'Performance dos projetos por programa e UF';
COMMENT ON VIEW mcmv_pj.vw_analise_prazos IS 'Análise de prazos e atrasos por programa e UF';
COMMENT ON VIEW mcmv_pf.vw_trabalho_social IS 'Acompanhamento do trabalho social vs obra física';
COMMENT ON VIEW financeiro.vw_execucao_financeira IS 'Execução financeira detalhada por programa e UF';
COMMENT ON VIEW mcmv_pj.vw_resumo_programa IS 'Resumo geral por programa';
