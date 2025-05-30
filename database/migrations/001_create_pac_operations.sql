-- PAC Operations table based on REUNI Excel analysis
-- 4,899 records with 78 columns analyzed

CREATE TABLE IF NOT EXISTS pac_operations (
    -- Primary identifiers
    proposta VARCHAR(50) PRIMARY KEY,
    operacao NUMERIC(20,0),
    dv INTEGER,
    instrumento INTEGER,
    
    -- Entities
    recebedor TEXT NOT NULL,
    ente_vinculacao TEXT,
    uf CHAR(2) NOT NULL,
    municipio_beneficiado TEXT NOT NULL,
    gigov_regov TEXT,
    gigov_vinculacao TEXT,
    repassador TEXT,
    
    -- Program details
    programa TEXT,
    objetivo TEXT,
    
    -- Geographic coordinates
    latitude NUMERIC(10,6),
    longitude NUMERIC(10,6),
    
    -- Classification
    tipo VARCHAR(200),
    tipologia TEXT,
    
    -- Status fields
    situacao_termo_compromisso VARCHAR(200),
    situacao_proposta VARCHAR(100),
    regime_simplificado VARCHAR(10),
    
    -- Financial values (stored in centavos to avoid floating point issues)
    valor_repasse_centavos BIGINT NOT NULL DEFAULT 0,
    valor_investimento_centavos BIGINT NOT NULL DEFAULT 0,
    valor_empenhado_centavos BIGINT DEFAULT 0,
    valor_pago_convenio_centavos BIGINT DEFAULT 0,
    valor_desbloqueado_centavos BIGINT DEFAULT 0,
    
    -- Key dates - Contract phase
    envio_para_caixa DATE,
    pt_em_complementacao DATE,
    pt_em_analise DATE,
    pt_aprovado DATE,
    emissao_empenho DATE,
    tc_assinado DATE,
    
    -- Suspensiva phase
    vencimento_suspensiva DATE,
    classificacao_suspensiva TEXT,
    suspensiva TEXT,
    data_cumprimento_suspensiva DATE,
    ultimo_envio_suspensiva_prazo DATE,
    ultimo_envio_suspensiva DATE,
    ultima_evolucao_suspensiva DATE,
    dias_sem_movimentacao INTEGER,
    prazo_suspensiva_contratual DATE,
    limite_retirada_suspensiva_90 DATE,
    limite_retirada_suspensiva_prorrogacao DATE,
    prazo_retirada_suspensiva_dias INTEGER,
    data_retirada_suspensiva DATE,
    qd_complementacoes_suspensiva INTEGER DEFAULT 0,
    situacao_analise_suspensiva VARCHAR(100),
    
    -- Bidding (Licitação) phase
    situacao_ail VARCHAR(200),
    data_solicitacao_ail_repassador DATE,
    data_recebimento_retorno_ail DATE,
    data_envio_ail_recebedor DATE,
    data_previsao_publicacao_edital DATE,
    data_publicacao_edital DATE,
    primeiro_envio_licitacao DATE,
    ultimo_envio_licitacao DATE,
    situacao_analise_vrpl VARCHAR(100),
    dias_sem_movimentacao_vrpl INTEGER,
    data_conclusao_analise_vrpl DATE,
    data_aceite_vrpl DATE,
    data_ultima_movimentacao_vrpl DATE,
    data_homologacao_licitacao DATE,
    
    -- Execution phase
    data_previsao_ordem_servico DATE,
    data_emissao_ordem_servico DATE,
    data_previsao_inicio_obra DATE,
    data_inicio_obra_tgov DATE,
    data_ultimo_bm_tgov DATE,
    data_ultimo_bm_reuni DATE,
    percentual_informado_reuni NUMERIC(5,2),
    percentual_informado_tgov NUMERIC(5,2),
    percentual_realizado_reuni NUMERIC(5,2),
    percentual_realizado_tgov NUMERIC(5,2),
    valor_informado_ultimo_bm_tgov_centavos BIGINT,
    valor_informado_ultimo_bm_reuni_centavos BIGINT,
    execucao_por_etapas BOOLEAN DEFAULT FALSE,
    
    -- Text fields for NLP analysis
    etiquetas TEXT,
    situacao_atual TEXT, -- Key field for delay cause analysis
    
    -- Metadata
    data_atualizacao_situacao_atual TIMESTAMP,
    data_atualizacao TIMESTAMP NOT NULL,
    
    -- ETL tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_pac_uf ON pac_operations(uf);
CREATE INDEX idx_pac_municipio ON pac_operations(municipio_beneficiado);
CREATE INDEX idx_pac_situacao_proposta ON pac_operations(situacao_proposta);
CREATE INDEX idx_pac_situacao_analise_suspensiva ON pac_operations(situacao_analise_suspensiva);
CREATE INDEX idx_pac_situacao_ail ON pac_operations(situacao_ail);
CREATE INDEX idx_pac_valor_repasse ON pac_operations(valor_repasse_centavos);
CREATE INDEX idx_pac_data_atualizacao ON pac_operations(data_atualizacao);
CREATE INDEX idx_pac_percentual_realizado ON pac_operations(percentual_realizado_reuni);

-- Table for storing extracted delay causes (from NLP analysis)
CREATE TABLE IF NOT EXISTS delay_causes (
    id SERIAL PRIMARY KEY,
    proposta VARCHAR(50) REFERENCES pac_operations(proposta),
    causa_categoria VARCHAR(100),
    causa_texto TEXT,
    confianca_score NUMERIC(3,2),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for audit/history tracking
CREATE TABLE IF NOT EXISTS pac_status_history (
    id SERIAL PRIMARY KEY,
    proposta VARCHAR(50) REFERENCES pac_operations(proposta),
    campo_alterado VARCHAR(100),
    valor_anterior TEXT,
    valor_novo TEXT,
    data_alteracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
