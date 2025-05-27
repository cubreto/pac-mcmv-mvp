-- PAC-MCMV Unified Database Schema
-- Single table strategy for MVP simplicity

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Unified project status table
CREATE TABLE IF NOT EXISTS projeto_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic project info
    proposta VARCHAR(100),
    uf CHAR(2) NOT NULL,
    municipio_beneficiado VARCHAR(255),
    
    -- Program identification
    programa VARCHAR(255) NOT NULL,
    tipo_programa VARCHAR(20) CHECK (tipo_programa IN ('PAC', 'HABITACAO')),
    
    -- Financial data
    valor_repasse DECIMAL(15,2),
    valor_investimento DECIMAL(15,2),
    valor_empenhado DECIMAL(15,2),
    valor_pago DECIMAL(15,2),
    
    -- Progress tracking
    percentual_obra_realizado DECIMAL(5,2),
    data_inicio_obra DATE,
    
    -- Key field for analysis
    situacao_atual TEXT NOT NULL,
    data_atualizacao_situacao DATE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT valid_percentage CHECK (percentual_obra_realizado >= 0 AND percentual_obra_realizado <= 100)
);

-- Indexes for common queries
CREATE INDEX idx_projeto_uf ON projeto_status(uf);
CREATE INDEX idx_projeto_programa ON projeto_status(programa);
CREATE INDEX idx_projeto_tipo ON projeto_status(tipo_programa);
CREATE INDEX idx_situacao_text ON projeto_status USING gin(to_tsvector('portuguese', situacao_atual));

-- View for dashboard queries (optional optimization)
CREATE OR REPLACE VIEW dashboard_summary AS
SELECT 
    uf,
    tipo_programa,
    COUNT(*) as total_projetos,
    SUM(valor_repasse) as valor_total,
    AVG(percentual_obra_realizado) as progresso_medio,
    COUNT(CASE WHEN situacao_atual ~* 'atras|problem|pendente|paralis' THEN 1 END) as projetos_problema
FROM projeto_status 
GROUP BY uf, tipo_programa;

-- Update trigger for metadata
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projeto_status_modtime 
    BEFORE UPDATE ON projeto_status 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
