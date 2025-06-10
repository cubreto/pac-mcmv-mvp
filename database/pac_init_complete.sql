-- Complete PAC Database Schema - FIXED DATA TYPES
-- Replaces: pac_init.sql + pac_realtime_migration.sql + add_missing_columns.sql
-- All 78 columns + real-time features + performance optimization
-- FIXED: Data type mismatches based on actual Excel file content

-- ============================================================================
-- STEP 1: Drop existing tables (for clean rebuild)
-- ============================================================================

DROP TABLE IF EXISTS pac_data_changes CASCADE;
DROP TABLE IF EXISTS pac_data_quality_log CASCADE;
DROP TABLE IF EXISTS pac_data_metadata CASCADE;
DROP TABLE IF EXISTS pac_ogu_data CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS check_system_health();
DROP FUNCTION IF EXISTS get_latest_batch_info();
DROP FUNCTION IF EXISTS cleanup_old_tracking_data(INTEGER);
DROP FUNCTION IF EXISTS update_pac_modified_timestamp();

-- ============================================================================
-- STEP 2: Create real-time tracking tables
-- ============================================================================

-- Batch metadata tracking
CREATE TABLE pac_data_metadata (
    batch_id VARCHAR(50) PRIMARY KEY,
    load_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_records INTEGER NOT NULL,
    source_file_name VARCHAR(255),
    source_file_hash VARCHAR(64),
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    processing_duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'SUCCESS',
    new_operations_count INTEGER DEFAULT 0,
    updated_operations_count INTEGER DEFAULT 0,
    errors_detected INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data quality tracking
CREATE TABLE pac_data_quality_log (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) REFERENCES pac_data_metadata(batch_id),
    quality_check VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARNING')),
    details TEXT,
    value_found TEXT,
    expected_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Change tracking
CREATE TABLE pac_data_changes (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) REFERENCES pac_data_metadata(batch_id),
    operacao VARCHAR(100) NOT NULL,
    change_type VARCHAR(50) NOT NULL CHECK (change_type IN ('NEW', 'UPDATED', 'STATUS_CHANGE', 'DELAY_INCREASE', 'DELETED')),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    change_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    significance_score INTEGER DEFAULT 1 CHECK (significance_score BETWEEN 1 AND 10)
);

-- ============================================================================
-- STEP 3: Create complete main table with ALL 78 columns + tracking
-- DATA TYPES FIXED BASED ON ACTUAL EXCEL CONTENT
-- ============================================================================

CREATE TABLE pac_ogu_data (
    id SERIAL PRIMARY KEY,
    
    -- ========================================================================
    -- ORIGINAL 78 COLUMNS FROM EXCEL FILE - FIXED DATA TYPES
    -- ========================================================================
    
    -- Basic Operation Info (Columns 1-15)
    proposta VARCHAR(100),                              -- 1. Proposta
    operacao VARCHAR(100),                              -- 2. Operação
    dv VARCHAR(10),                                     -- 3. DV
    instrumento VARCHAR(100),                           -- 4. Instrumento
    recebedor TEXT,                                     -- 5. Recebedor
    ente_vinculacao TEXT,                              -- 6. Ente de vinculação
    uf VARCHAR(2),                                      -- 7. UF
    municipio_beneficiado TEXT,                         -- 8. Município Beneficiado
    gigov_regov VARCHAR(100),                          -- 9. GIGOV/REGOV
    gigov_vinculacao VARCHAR(100),                     -- 10. GIGOV de Vinculação
    repassador TEXT,                                    -- 11. Repassador
    programa TEXT,                                      -- 12. Programa
    objetivo TEXT,                                      -- 13. Objetivo
    latitude DECIMAL(10, 8),                           -- 14. Latitude
    longitude DECIMAL(11, 8),                          -- 15. Longitude
    
    -- Project Classification (Columns 16-20)
    tipo VARCHAR(100),                                  -- 16. Tipo
    tipologia VARCHAR(100),                            -- 17. Tipologia
    situacao_termo_compromisso TEXT,                   -- 18. Situação do Termo de Compromisso
    situacao_proposta TEXT,                            -- 19. Situação da Proposta
    regime_simplificado VARCHAR(50),                   -- 20. Regime Simplificado
    
    -- Financial Data (Columns 21-26)
    valor_repasse DECIMAL(15,2),                       -- 21. Valor Repasse
    valor_investimento DECIMAL(15,2),                  -- 22. Valor Investimento
    valor_empenhado DECIMAL(15,2),                     -- 23. Valor Empenhado
    valor_pago DECIMAL(15,2),                          -- 24. Valor Pago C.Convênio
    valor_desbloqueado DECIMAL(15,2),                  -- 25. Valor Desbloqueado
    acao_orcamentaria VARCHAR(100),                    -- 26. Ação Orçamentária
    
    -- Process Timeline (Columns 27-32)
    envio_caixa DATE,                                   -- 27. Envio para CAIXA
    pt_complementacao DATE,                             -- 28. PT em Complementação
    pt_analise DATE,                                    -- 29. PT em Análise
    pt_aprovado DATE,                                   -- 30. PT Aprovado
    emissao_empenho DATE,                               -- 31. Emissão Empenho
    tc_assinado DATE,                                   -- 32. TC Assinado
    
    -- Suspensiva Data (Columns 33-47) - FIXED DATA TYPES
    vencimento_da_suspensiva DATE,                      -- 33. Vencimento da Suspensiva
    classificacao_suspensiva TEXT,                      -- 34. Classificação Suspensiva
    suspensiva TEXT,                                     -- 35. Suspensiva
    data_cumprimento_suspensiva DATE,                   -- 36. Data Cumprimento Suspensiva
    ultimo_envio_suspensiva_prazo DATE,                 -- 37. Último Envio Suspensiva (dentro do prazo contratual)
    ultimo_envio_suspensiva DATE,                       -- 38. Último Envio Suspensiva
    ultima_evolucao_suspensiva DATE,                    -- 39. Última Evolução Suspensiva
    dias_sem_movimentacao INTEGER,                      -- 40. Dias sem movimentação
    prazo_suspensiva_contratual DATE,                   -- 41. FIXED: Prazo Suspensiva Contratual (DATE not INTEGER)
    limite_retirada_90dias DATE,                        -- 42. Limite para retirada da suspensiva (90 dias)
    limite_retirada_prorrogacao DATE,                   -- 43. Limite para retirada da suspensiva (prorrogação 30 dias)
    prazo_retirada_dias INTEGER,                        -- 44. Prazo para retirada da suspensiva (dias)
    data_retirada_suspensiva DATE,                      -- 45. Data Retirada Suspensiva
    qtd_complementacoes_suspensiva INTEGER,             -- 46. Qd.Complementações de Suspensiva
    situacao_da_analise_suspensiva TEXT,               -- 47. Situação da Análise Suspensiva
    
    -- AIL Process (Columns 48-52)
    situacao_ail TEXT,                                  -- 48. Situação da AIL
    data_solicitacao_ail DATE,                         -- 49. Data solicitação AIL ao Repassador
    data_recebimento_retorno_ail DATE,                 -- 50. Data recebimento retorno AIL pelo Repassador
    data_envio_ail_recebedor DATE,                     -- 51. Data envio da AIL ao Recebedor
    data_previsao_publicacao_edital DATE,              -- 52. Data Previsão Publicação Edital Licitação
    
    -- Licitação Process (Columns 53-61)
    data_publicacao_edital DATE,                       -- 53. Data Publicação Edital Licitação
    primeiro_envio_licitacao DATE,                     -- 54. Primeiro Envio da Licitação
    ultimo_envio_licitacao DATE,                       -- 55. Último Envio da Licitação
    situacao_da_analise_vrpl TEXT,                     -- 56. Situação da Análise VRPL
    dias_sem_movimentacao_vrpl INTEGER,                -- 57. Dias sem movimentação VRPL
    data_conclusao_analise_vrpl DATE,                  -- 58. Data Conclusão Análise VRPL
    data_aceite_vrpl DATE,                             -- 59. Data Aceite VRPL
    data_ultima_movimentacao_vrpl DATE,                -- 60. Data Última Movimentação VRPL
    data_homologacao_licitacao DATE,                   -- 61. Data Homologação Licitação
    
    -- Obras Process (Columns 62-74)
    data_previsao_ordem_servico DATE,                  -- 62. Data Previsão Ordem Serviço
    data_emissao_ordem_servico DATE,                   -- 63. Data Emissão Ordem Serviço
    data_previsao_inicio_obra DATE,                    -- 64. Data Previsão Início de Obra
    data_inicio_de_obra DATE,                          -- 65. Data Início de Obra (TGov)
    data_ultimo_bm_tgov DATE,                          -- 66. Data Último BM (TGOV)
    data_ultimo_bm_reuni DATE,                         -- 67. Data Último BM (REUNI)
    percentual_informado_reuni DECIMAL(5,2),          -- 68. Percentual informado (REUNI)
    percentual_informado_tgov DECIMAL(5,2),           -- 69. Percentual informado (TGov)
    percentual_realizado DECIMAL(5,2),                -- 70. Percentual realizado (REUNI)
    percentual_realizado_tgov DECIMAL(5,2),           -- 71. Percentual realizado (TGov)
    valor_ultimo_bm_tgov DECIMAL(15,2),               -- 72. Valor Informado no último BM (TGov)
    valor_ultimo_bm_reuni DECIMAL(15,2),              -- 73. Valor Informado no último BM (REUNI)
    execucao_por_etapas TEXT,                          -- 74. Execução por Etapas
    
    -- Metadata and Status (Columns 75-78)
    etiquetas TEXT,                                     -- 75. Etiquetas
    situacao_atual TEXT,                               -- 76. Situação Atual
    data_atualizacao_situacao DATE,                    -- 77. Data atualização da Situação Atual
    data_atualizacao DATE,                             -- 78. Data Atualização
    
    -- ========================================================================
    -- REAL-TIME TRACKING COLUMNS
    -- ========================================================================
    
    data_load_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data_batch_id VARCHAR(50) REFERENCES pac_data_metadata(batch_id),
    record_version INTEGER DEFAULT 1,
    record_hash VARCHAR(64),
    first_seen_batch VARCHAR(50),
    last_updated_batch VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Legacy timestamps (keep for compatibility)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- STEP 4: Create comprehensive indexes for performance
-- ============================================================================

-- Core operation indexes
CREATE INDEX IF NOT EXISTS idx_pac_operacao ON pac_ogu_data(operacao);
CREATE INDEX IF NOT EXISTS idx_pac_proposta ON pac_ogu_data(proposta);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pac_operacao_active ON pac_ogu_data(operacao) WHERE is_active = TRUE;

-- Geographic indexes
CREATE INDEX IF NOT EXISTS idx_pac_uf ON pac_ogu_data(uf);
CREATE INDEX IF NOT EXISTS idx_pac_municipio ON pac_ogu_data(municipio_beneficiado);
CREATE INDEX IF NOT EXISTS idx_pac_gigov_regov ON pac_ogu_data(gigov_regov);
CREATE INDEX IF NOT EXISTS idx_pac_repassador ON pac_ogu_data(repassador);

-- Financial indexes
CREATE INDEX IF NOT EXISTS idx_pac_valor_empenhado ON pac_ogu_data(valor_empenhado);
CREATE INDEX IF NOT EXISTS idx_pac_valor_pago ON pac_ogu_data(valor_pago);
CREATE INDEX IF NOT EXISTS idx_pac_valor_desbloqueado ON pac_ogu_data(valor_desbloqueado);

-- Process tracking indexes
CREATE INDEX IF NOT EXISTS idx_pac_programa ON pac_ogu_data(programa);
CREATE INDEX IF NOT EXISTS idx_pac_tipo ON pac_ogu_data(tipo);
CREATE INDEX IF NOT EXISTS idx_pac_situacao_termo ON pac_ogu_data(situacao_termo_compromisso);
CREATE INDEX IF NOT EXISTS idx_pac_situacao_proposta ON pac_ogu_data(situacao_proposta);

-- Suspensiva indexes
CREATE INDEX IF NOT EXISTS idx_pac_vencimento_suspensiva ON pac_ogu_data(vencimento_da_suspensiva);
CREATE INDEX IF NOT EXISTS idx_pac_data_cumprimento ON pac_ogu_data(data_cumprimento_suspensiva);
CREATE INDEX IF NOT EXISTS idx_pac_data_retirada ON pac_ogu_data(data_retirada_suspensiva);
CREATE INDEX IF NOT EXISTS idx_pac_dias_sem_movimentacao ON pac_ogu_data(dias_sem_movimentacao);
CREATE INDEX IF NOT EXISTS idx_pac_situacao_analise_suspensiva ON pac_ogu_data(situacao_da_analise_suspensiva);
CREATE INDEX IF NOT EXISTS idx_pac_prazo_suspensiva ON pac_ogu_data(prazo_suspensiva_contratual);

-- AIL/VRPL indexes
CREATE INDEX IF NOT EXISTS idx_pac_situacao_ail ON pac_ogu_data(situacao_ail);
CREATE INDEX IF NOT EXISTS idx_pac_data_solicitacao_ail ON pac_ogu_data(data_solicitacao_ail);
CREATE INDEX IF NOT EXISTS idx_pac_data_aceite_vrpl ON pac_ogu_data(data_aceite_vrpl);
CREATE INDEX IF NOT EXISTS idx_pac_situacao_vrpl ON pac_ogu_data(situacao_da_analise_vrpl);
CREATE INDEX IF NOT EXISTS idx_pac_dias_sem_movimentacao_vrpl ON pac_ogu_data(dias_sem_movimentacao_vrpl);

-- Obras indexes
CREATE INDEX IF NOT EXISTS idx_pac_data_inicio_obra ON pac_ogu_data(data_inicio_de_obra);
CREATE INDEX IF NOT EXISTS idx_pac_data_emissao_os ON pac_ogu_data(data_emissao_ordem_servico);
CREATE INDEX IF NOT EXISTS idx_pac_percentual_realizado ON pac_ogu_data(percentual_realizado);
CREATE INDEX IF NOT EXISTS idx_pac_tc_assinado ON pac_ogu_data(tc_assinado);

-- Status and metadata indexes
CREATE INDEX IF NOT EXISTS idx_pac_situacao_atual ON pac_ogu_data(situacao_atual);
CREATE INDEX IF NOT EXISTS idx_pac_etiquetas ON pac_ogu_data(etiquetas);
CREATE INDEX IF NOT EXISTS idx_pac_data_atualizacao ON pac_ogu_data(data_atualizacao);

-- Real-time performance indexes
CREATE INDEX IF NOT EXISTS idx_pac_data_load_timestamp ON pac_ogu_data(data_load_timestamp);
CREATE INDEX IF NOT EXISTS idx_pac_batch_id ON pac_ogu_data(data_batch_id);
CREATE INDEX IF NOT EXISTS idx_pac_record_version ON pac_ogu_data(record_version);
CREATE INDEX IF NOT EXISTS idx_pac_is_active ON pac_ogu_data(is_active);
CREATE INDEX IF NOT EXISTS idx_pac_last_updated ON pac_ogu_data(last_updated_batch);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_pac_active_batch ON pac_ogu_data(is_active, data_batch_id) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_pac_uf_municipio ON pac_ogu_data(uf, municipio_beneficiado);
CREATE INDEX IF NOT EXISTS idx_pac_repassador_situacao ON pac_ogu_data(repassador, situacao_atual);
CREATE INDEX IF NOT EXISTS idx_pac_dias_prioridade ON pac_ogu_data(dias_sem_movimentacao) WHERE dias_sem_movimentacao > 40;

-- Metadata table indexes
CREATE INDEX IF NOT EXISTS idx_metadata_timestamp ON pac_data_metadata(load_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metadata_status ON pac_data_metadata(status);
CREATE INDEX IF NOT EXISTS idx_quality_batch ON pac_data_quality_log(batch_id);
CREATE INDEX IF NOT EXISTS idx_changes_batch ON pac_data_changes(batch_id);
CREATE INDEX IF NOT EXISTS idx_changes_operacao ON pac_data_changes(operacao);
CREATE INDEX IF NOT EXISTS idx_changes_type ON pac_data_changes(change_type);
CREATE INDEX IF NOT EXISTS idx_changes_timestamp ON pac_data_changes(change_timestamp DESC);

-- ============================================================================
-- STEP 5: Create enhanced views with all new data
-- ============================================================================

-- Enhanced Suspensivas View with complete data
CREATE OR REPLACE VIEW vw_pac_suspensivas AS
SELECT 
    -- Core operation info
    p.id,
    p.proposta,
    p.operacao,
    p.uf,
    p.municipio_beneficiado,
    p.repassador,
    p.gigov_regov,
    p.programa,
    p.tipo,
    p.tipologia,
    
    -- Financial data
    p.valor_empenhado,
    p.valor_pago,
    p.valor_desbloqueado,
    p.valor_repasse,
    p.valor_investimento,
    
    -- Suspensiva core data
    p.vencimento_da_suspensiva,
    p.data_cumprimento_suspensiva,
    p.data_retirada_suspensiva,
    p.situacao_da_analise_suspensiva,
    p.dias_sem_movimentacao,
    p.situacao_atual,
    p.etiquetas,
    p.classificacao_suspensiva,
    p.suspensiva,
    
    -- Suspensiva detailed tracking
    p.ultimo_envio_suspensiva,
    p.ultima_evolucao_suspensiva,
    p.prazo_suspensiva_contratual,
    p.limite_retirada_90dias,
    p.prazo_retirada_dias,
    p.qtd_complementacoes_suspensiva,
    
    -- Process timeline
    p.envio_caixa,
    p.pt_aprovado,
    p.tc_assinado,
    p.emissao_empenho,
    
    -- Enhanced calculations
    CASE 
        WHEN p.vencimento_da_suspensiva IS NOT NULL 
        THEN CURRENT_DATE - p.vencimento_da_suspensiva 
        ELSE NULL 
    END as dias_vencimento,
    
    CASE 
        WHEN p.data_retirada_suspensiva IS NOT NULL THEN 'Retirada'
        WHEN p.data_cumprimento_suspensiva IS NOT NULL THEN 'Cumprida'
        WHEN p.vencimento_da_suspensiva < CURRENT_DATE THEN 'Vencida'
        ELSE 'Pendente'
    END as status_suspensiva,
    
    -- Enhanced priority classification
    CASE 
        WHEN p.dias_sem_movimentacao > 90 THEN 'CRÍTICO'
        WHEN p.dias_sem_movimentacao > 60 THEN 'URGENTE'  
        WHEN p.dias_sem_movimentacao > 40 THEN 'ATENÇÃO'
        ELSE 'NORMAL'
    END as nivel_prioridade,
    
    -- Real-time metadata
    p.data_load_timestamp,
    p.data_batch_id,
    p.record_version,
    p.last_updated_batch,
    m.load_timestamp as batch_timestamp,
    m.data_quality_score as batch_quality_score,
    
    -- Real-time indicators
    CASE 
        WHEN p.data_load_timestamp > CURRENT_TIMESTAMP - INTERVAL '4 hours' THEN TRUE
        ELSE FALSE
    END as is_recently_updated,
    
    CASE 
        WHEN p.data_load_timestamp > CURRENT_TIMESTAMP - INTERVAL '2 hours' THEN TRUE
        ELSE FALSE
    END as is_fresh_data,
    
    -- Change tracking indicator
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pac_data_changes c 
            WHERE c.operacao = p.operacao 
            AND c.change_timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ) THEN TRUE
        ELSE FALSE
    END as teve_mudanca_recente
    
FROM pac_ogu_data p
LEFT JOIN pac_data_metadata m ON p.data_batch_id = m.batch_id
WHERE p.is_active = TRUE 
  AND p.vencimento_da_suspensiva IS NOT NULL;

-- Enhanced VRPL View with complete workflow
CREATE OR REPLACE VIEW vw_pac_vrpl AS
SELECT 
    -- Core info
    p.id,
    p.operacao,
    p.proposta,
    p.uf,
    p.municipio_beneficiado,
    p.repassador,
    p.gigov_regov,
    p.programa,
    p.valor_empenhado,
    
    -- AIL Process
    p.situacao_ail,
    p.data_solicitacao_ail,
    p.data_recebimento_retorno_ail,
    p.data_envio_ail_recebedor,
    
    -- Licitação Process
    p.data_previsao_publicacao_edital,
    p.data_publicacao_edital,
    p.primeiro_envio_licitacao,
    p.ultimo_envio_licitacao,
    p.data_homologacao_licitacao,
    
    -- VRPL Process
    p.situacao_da_analise_vrpl,
    p.data_aceite_vrpl,
    p.dias_sem_movimentacao_vrpl,
    p.data_conclusao_analise_vrpl,
    p.data_ultima_movimentacao_vrpl,
    
    -- Calculated timing
    CASE 
        WHEN p.data_aceite_vrpl IS NOT NULL AND p.data_solicitacao_ail IS NOT NULL
        THEN p.data_aceite_vrpl - p.data_solicitacao_ail
        ELSE NULL
    END as dias_processamento_vrpl,
    
    CASE 
        WHEN p.data_publicacao_edital IS NOT NULL AND p.data_previsao_publicacao_edital IS NOT NULL
        THEN p.data_publicacao_edital - p.data_previsao_publicacao_edital
        ELSE NULL
    END as atraso_publicacao_edital,
    
    -- Real-time metadata
    p.data_load_timestamp,
    p.data_batch_id,
    p.record_version,
    
    -- Change indicators
    CASE 
        WHEN p.data_load_timestamp > CURRENT_TIMESTAMP - INTERVAL '4 hours' THEN TRUE
        ELSE FALSE
    END as is_recently_updated
    
FROM pac_ogu_data p
LEFT JOIN pac_data_metadata m ON p.data_batch_id = m.batch_id
WHERE p.is_active = TRUE 
  AND (p.data_solicitacao_ail IS NOT NULL OR p.situacao_da_analise_vrpl IS NOT NULL);

-- Enhanced Obras View with complete construction tracking
CREATE OR REPLACE VIEW vw_pac_obras AS
SELECT 
    -- Core info
    p.id,
    p.operacao,
    p.proposta,
    p.uf,
    p.municipio_beneficiado,
    p.repassador,
    p.gigov_regov,
    p.programa,
    p.tipo,
    p.tipologia,
    
    -- Financial execution
    p.valor_empenhado,
    p.valor_pago,
    p.valor_desbloqueado,
    p.valor_ultimo_bm_tgov,
    p.valor_ultimo_bm_reuni,
    
    -- Construction timeline
    p.data_previsao_ordem_servico,
    p.data_emissao_ordem_servico,
    p.data_previsao_inicio_obra,
    p.data_inicio_de_obra,
    p.data_ultimo_bm_tgov,
    p.data_ultimo_bm_reuni,
    
    -- Progress tracking
    p.percentual_informado_reuni,
    p.percentual_informado_tgov,
    p.percentual_realizado,
    p.percentual_realizado_tgov,
    p.execucao_por_etapas,
    
    -- Financial calculations
    CASE 
        WHEN p.valor_empenhado > 0 
        THEN ROUND((p.valor_pago / p.valor_empenhado * 100), 2)
        ELSE 0 
    END as percentual_pago,
    
    CASE 
        WHEN p.valor_empenhado > 0 
        THEN ROUND((p.valor_desbloqueado / p.valor_empenhado * 100), 2)
        ELSE 0 
    END as percentual_desbloqueado,
    
    -- Timeline calculations
    CASE 
        WHEN p.data_inicio_de_obra IS NOT NULL AND p.data_emissao_ordem_servico IS NOT NULL
        THEN p.data_inicio_de_obra - p.data_emissao_ordem_servico
        ELSE NULL
    END as dias_os_para_inicio,
    
    CASE 
        WHEN p.data_emissao_ordem_servico IS NOT NULL AND p.data_previsao_ordem_servico IS NOT NULL
        THEN p.data_emissao_ordem_servico - p.data_previsao_ordem_servico
        ELSE NULL
    END as atraso_emissao_os,
    
    -- Real-time metadata
    p.data_load_timestamp,
    p.data_batch_id,
    p.record_version,
    
    -- Change indicators
    CASE 
        WHEN p.data_load_timestamp > CURRENT_TIMESTAMP - INTERVAL '4 hours' THEN TRUE
        ELSE FALSE
    END as is_recently_updated
    
FROM pac_ogu_data p
WHERE p.is_active = TRUE 
  AND p.valor_empenhado IS NOT NULL 
  AND p.valor_empenhado > 0;

-- Enhanced Portfolio Summary with all metrics
CREATE OR REPLACE VIEW vw_pac_portfolio_summary AS
SELECT 
    -- Basic counts
    COUNT(*) as total_operacoes,
    COUNT(DISTINCT p.uf) as total_estados,
    COUNT(DISTINCT p.municipio_beneficiado) as total_municipios,
    COUNT(DISTINCT p.repassador) as total_ministerios,
    COUNT(DISTINCT p.programa) as total_programas,
    
    -- Financial summary
    SUM(p.valor_empenhado) as valor_total_empenhado,
    SUM(p.valor_pago) as valor_total_pago,
    SUM(p.valor_desbloqueado) as valor_total_desbloqueado,
    SUM(p.valor_repasse) as valor_total_repasse,
    SUM(p.valor_investimento) as valor_total_investimento,
    
    -- Process metrics
    AVG(p.dias_sem_movimentacao) as media_dias_sem_movimentacao,
    COUNT(CASE WHEN p.tc_assinado IS NOT NULL THEN 1 END) as tc_assinados,
    COUNT(CASE WHEN p.data_retirada_suspensiva IS NOT NULL THEN 1 END) as suspensivas_retiradas,
    COUNT(CASE WHEN p.data_aceite_vrpl IS NOT NULL THEN 1 END) as vrpl_aceitos,
    COUNT(CASE WHEN p.data_inicio_de_obra IS NOT NULL THEN 1 END) as obras_iniciadas,
    
    -- Priority distribution
    COUNT(CASE WHEN p.dias_sem_movimentacao > 90 THEN 1 END) as operacoes_criticas,
    COUNT(CASE WHEN p.dias_sem_movimentacao > 60 THEN 1 END) as operacoes_urgentes,
    COUNT(CASE WHEN p.dias_sem_movimentacao > 40 THEN 1 END) as operacoes_atencao,
    
    -- Real-time metrics
    MAX(m.load_timestamp) as ultima_atualizacao_dados,
    COUNT(CASE WHEN p.data_load_timestamp > CURRENT_TIMESTAMP - INTERVAL '4 hours' THEN 1 END) as operacoes_atualizadas_recentemente,
    COUNT(CASE WHEN p.data_load_timestamp > CURRENT_TIMESTAMP - INTERVAL '2 hours' THEN 1 END) as operacoes_muito_recentes,
    
    -- Data quality indicators
    AVG(COALESCE(m.data_quality_score, 1.0)) as qualidade_media_dados,
    COUNT(DISTINCT m.batch_id) as total_batches_carregados
    
FROM pac_ogu_data p
LEFT JOIN pac_data_metadata m ON p.data_batch_id = m.batch_id
WHERE p.is_active = TRUE;

-- System status monitoring
CREATE OR REPLACE VIEW vw_pac_system_status AS
SELECT 
    m.batch_id,
    m.load_timestamp,
    m.total_records,
    m.data_quality_score,
    m.processing_duration_seconds,
    m.status,
    m.new_operations_count,
    m.updated_operations_count,
    m.errors_detected,
    
    -- Time calculations
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - m.load_timestamp))/60 as minutes_since_update,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - m.load_timestamp))/3600 as hours_since_update,
    
    -- Status classifications
    CASE 
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - m.load_timestamp))/60 <= 130 THEN 'FRESH'
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - m.load_timestamp))/60 <= 180 THEN 'STALE'
        ELSE 'EXPIRED'
    END as data_freshness_status,
    
    CASE 
        WHEN m.data_quality_score >= 0.95 THEN 'EXCELLENT'
        WHEN m.data_quality_score >= 0.90 THEN 'GOOD'
        WHEN m.data_quality_score >= 0.80 THEN 'FAIR'
        ELSE 'POOR'
    END as data_quality_status,
    
    -- Next expected update
    m.load_timestamp + INTERVAL '2 hours' as proxima_atualizacao_esperada
    
FROM pac_data_metadata m
ORDER BY m.load_timestamp DESC
LIMIT 1;

-- Recent changes summary
CREATE OR REPLACE VIEW vw_pac_recent_changes AS
SELECT 
    c.batch_id,
    c.change_type,
    COUNT(*) as quantidade_mudancas,
    COUNT(DISTINCT c.operacao) as operacoes_afetadas,
    STRING_AGG(DISTINCT c.operacao, ', ' ORDER BY c.operacao) FILTER (WHERE c.operacao IS NOT NULL) as lista_operacoes_sample,
    MAX(c.change_timestamp) as ultima_mudanca,
    MIN(c.change_timestamp) as primeira_mudanca,
    AVG(c.significance_score) as score_significancia_medio,
    m.load_timestamp as timestamp_batch
    
FROM pac_data_changes c
LEFT JOIN pac_data_metadata m ON c.batch_id = m.batch_id
WHERE c.change_timestamp > CURRENT_TIMESTAMP - INTERVAL '6 hours'
GROUP BY c.batch_id, c.change_type, m.load_timestamp
ORDER BY ultima_mudanca DESC;

-- ============================================================================
-- STEP 6: Create utility functions
-- ============================================================================

-- Get latest batch information
CREATE OR REPLACE FUNCTION get_latest_batch_info()
RETURNS TABLE (
    batch_id VARCHAR(50),
    load_timestamp TIMESTAMP WITH TIME ZONE,
    total_records INTEGER,
    data_quality_score DECIMAL(3,2),
    minutes_old NUMERIC,
    status VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.batch_id,
        m.load_timestamp,
        m.total_records,
        m.data_quality_score,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - m.load_timestamp))/60 as minutes_old,
        m.status
    FROM pac_data_metadata m
    ORDER BY m.load_timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Check system health
CREATE OR REPLACE FUNCTION check_system_health()
RETURNS TABLE (
    overall_status TEXT,
    data_freshness TEXT,
    data_quality TEXT,
    last_update_minutes NUMERIC,
    quality_score DECIMAL(3,2),
    recommendations TEXT
) AS $$
DECLARE
    latest_info RECORD;
    recommendations_text TEXT := '';
BEGIN
    -- Get latest batch info
    SELECT * INTO latest_info FROM get_latest_batch_info();
    
    -- Build recommendations
    IF latest_info.minutes_old > 150 THEN
        recommendations_text := 'Data update overdue - check ETL process';
    ELSIF latest_info.data_quality_score < 0.90 THEN
        recommendations_text := 'Data quality below 90% - investigate source data';
    ELSIF latest_info.status != 'SUCCESS' THEN
        recommendations_text := 'Last ETL run failed - check error logs';
    ELSE
        recommendations_text := 'System operating normally';
    END IF;
    
    RETURN QUERY
    SELECT 
        CASE 
            WHEN latest_info.minutes_old <= 130 AND latest_info.data_quality_score >= 0.90 THEN 'HEALTHY'
            WHEN latest_info.minutes_old <= 180 AND latest_info.data_quality_score >= 0.80 THEN 'WARNING'
            ELSE 'CRITICAL'
        END::TEXT as overall_status,
        CASE 
            WHEN latest_info.minutes_old <= 130 THEN 'FRESH'
            WHEN latest_info.minutes_old <= 180 THEN 'STALE'
            ELSE 'EXPIRED'
        END::TEXT as data_freshness,
        CASE 
            WHEN latest_info.data_quality_score >= 0.95 THEN 'EXCELLENT'
            WHEN latest_info.data_quality_score >= 0.90 THEN 'GOOD'
            WHEN latest_info.data_quality_score >= 0.80 THEN 'FAIR'
            ELSE 'POOR'
        END::TEXT as data_quality,
        latest_info.minutes_old as last_update_minutes,
        latest_info.data_quality_score as quality_score,
        recommendations_text::TEXT as recommendations;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old tracking data
CREATE OR REPLACE FUNCTION cleanup_old_tracking_data(days_to_keep INTEGER DEFAULT 30)
RETURNS TABLE (
    metadata_deleted INTEGER,
    changes_deleted INTEGER,
    quality_logs_deleted INTEGER
) AS $$
DECLARE
    metadata_count INTEGER;
    changes_count INTEGER;
    quality_count INTEGER;
BEGIN
    -- Delete old metadata (cascades to related tables)
    WITH deleted_metadata AS (
        DELETE FROM pac_data_metadata 
        WHERE load_timestamp < CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL
        RETURNING batch_id
    )
    SELECT COUNT(*) INTO metadata_count FROM deleted_metadata;
    
    -- Delete old changes
    WITH deleted_changes AS (
        DELETE FROM pac_data_changes 
        WHERE change_timestamp < CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO changes_count FROM deleted_changes;
    
    -- Delete old quality logs
    WITH deleted_quality AS (
        DELETE FROM pac_data_quality_log 
        WHERE created_at < CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO quality_count FROM deleted_quality;
    
    RETURN QUERY
    SELECT metadata_count, changes_count, quality_count;
END;
$$ LANGUAGE plpgsql;

-- Enhanced trigger function
CREATE OR REPLACE FUNCTION update_pac_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    
    -- Update tracking fields if they exist
    IF TG_OP = 'UPDATE' THEN
        -- Keep original creation metadata
        NEW.first_seen_batch = OLD.first_seen_batch;
        NEW.data_load_timestamp = OLD.data_load_timestamp;
        
        -- Update version tracking
        NEW.record_version = COALESCE(OLD.record_version, 0) + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply enhanced trigger
CREATE TRIGGER update_pac_ogu_data_modtime
    BEFORE UPDATE ON pac_ogu_data
    FOR EACH ROW
    EXECUTE FUNCTION update_pac_modified_timestamp();

-- ============================================================================
-- STEP 7: Create migration summary view
-- ============================================================================

CREATE OR REPLACE VIEW vw_migration_summary AS
SELECT 
    'pac_ogu_data' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN data_batch_id IS NOT NULL THEN 1 END) as records_with_batch_tracking,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_records,
    MIN(data_load_timestamp) as earliest_load_time,
    MAX(data_load_timestamp) as latest_load_time
FROM pac_ogu_data

UNION ALL

SELECT 
    'pac_data_metadata' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as successful_batches,
    COUNT(CASE WHEN load_timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as recent_batches,
    MIN(load_timestamp) as earliest_batch,
    MAX(load_timestamp) as latest_batch
FROM pac_data_metadata

UNION ALL

SELECT 
    'pac_data_changes' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT operacao) as operations_with_changes,
    COUNT(CASE WHEN change_timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as recent_changes,
    MIN(change_timestamp) as earliest_change,
    MAX(change_timestamp) as latest_change
FROM pac_data_changes;

-- ============================================================================
-- FINAL VERIFICATION AND SUMMARY
-- ============================================================================

-- Create comprehensive column overview
SELECT 
    'Schema created successfully!' as status,
    COUNT(*) as total_columns,
    COUNT(CASE WHEN column_name LIKE 'data_%' THEN 1 END) as date_columns,
    COUNT(CASE WHEN data_type = 'numeric' THEN 1 END) as numeric_columns,
    COUNT(CASE WHEN data_type LIKE '%text%' OR data_type LIKE '%varchar%' THEN 1 END) as text_columns,
    COUNT(CASE WHEN column_name LIKE '%timestamp%' THEN 1 END) as timestamp_columns
FROM information_schema.columns 
WHERE table_name = 'pac_ogu_data';

-- Final success message
SELECT 
    '🎉 Complete PAC Database Schema Ready! 🎉' as status,
    '✅ All 78 Excel columns mapped with FIXED data types' as excel_columns,
    '✅ Real-time tracking enabled' as real_time,
    '✅ Performance optimized' as performance,
    '✅ Advanced views created' as views,
    '✅ Change detection ready' as change_detection,
    'Run your ETL to populate data!' as next_step;
