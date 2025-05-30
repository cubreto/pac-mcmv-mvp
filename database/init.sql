-- PAC-MCMV Database Initialization
-- Updated for REUNI data structure

-- Create tables (will be created by migration script)
-- This file now just creates views for the dashboards

-- View for dashboard summary (Q2: Suspensiva Analysis)
CREATE OR REPLACE VIEW suspensiva_funnel AS
SELECT 
    situacao_analise_suspensiva,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM pac_operations
WHERE situacao_proposta = 'em execucao'
GROUP BY situacao_analise_suspensiva
ORDER BY total DESC;

-- View for licitação funnel (Q3: Bidding Analysis)
CREATE OR REPLACE VIEW licitacao_funnel AS
SELECT 
    CASE 
        WHEN situacao_analise_vrpl = 'VRPL Emitida' THEN '4. VRPL Emitida'
        WHEN data_publicacao_edital IS NOT NULL THEN '3. Edital Publicado'
        WHEN situacao_ail LIKE '%Autorização Encaminhada%' THEN '2. AIL Autorizada'
        ELSE '1. Aguardando AIL'
    END as etapa_licitacao,
    COUNT(*) as total
FROM pac_operations
GROUP BY etapa_licitacao
ORDER BY etapa_licitacao;

-- View for regional analysis (Q4: Regional Performance)
CREATE OR REPLACE VIEW regional_summary AS
SELECT 
    uf,
    COUNT(*) as total_operacoes,
    SUM(valor_repasse_centavos) / 100.0 as valor_total_repasse,
    AVG(percentual_realizado_reuni) as percentual_medio_execucao,
    COUNT(CASE WHEN percentual_realizado_reuni < 50 THEN 1 END) as operacoes_baixa_execucao
FROM pac_operations
GROUP BY uf
ORDER BY total_operacoes DESC;

-- View for overall dashboard metrics
CREATE OR REPLACE VIEW dashboard_metrics AS
SELECT 
    COUNT(*) as total_operacoes,
    COUNT(DISTINCT uf) as total_estados,
    COUNT(DISTINCT municipio_beneficiado) as total_municipios,
    SUM(valor_repasse_centavos) / 100.0 as valor_total_repasse,
    SUM(valor_investimento_centavos) / 100.0 as valor_total_investimento,
    AVG(percentual_realizado_reuni) as percentual_medio_execucao,
    COUNT(CASE WHEN situacao_analise_suspensiva = 'Suspensiva retirada' THEN 1 END) as suspensivas_retiradas,
    COUNT(CASE WHEN data_publicacao_edital IS NOT NULL THEN 1 END) as licitacoes_publicadas
FROM pac_operations;
