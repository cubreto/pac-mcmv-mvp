-- Migration: Add tipo and modalidadeProposta columns for RURAL filters
-- Date: 2025-07-31
-- Purpose: Support new RURAL filter requirements from BI Digiteam specification

-- Add tipo column
ALTER TABLE mcmv_v2.projetos 
ADD COLUMN IF NOT EXISTS tipo VARCHAR(50);

-- Add modalidadeProposta column  
ALTER TABLE mcmv_v2.projetos 
ADD COLUMN IF NOT EXISTS modalidade_proposta VARCHAR(50);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projetos_tipo 
ON mcmv_v2.projetos(tipo) 
WHERE programa = 'RURAL';

CREATE INDEX IF NOT EXISTS idx_projetos_modalidade_proposta 
ON mcmv_v2.projetos(modalidade_proposta) 
WHERE programa = 'RURAL';

-- Update existing RURAL records to have default tipo value
UPDATE mcmv_v2.projetos 
SET tipo = 'RURAL' 
WHERE programa = 'RURAL' AND tipo IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN mcmv_v2.projetos.tipo IS 'Tipo do programa RURAL: RURAL ou RURAL-CALAMIDADES';
COMMENT ON COLUMN mcmv_v2.projetos.modalidade_proposta IS 'Modalidade da proposta RURAL: Melhoria Habitacional ou Produção Habitacional';