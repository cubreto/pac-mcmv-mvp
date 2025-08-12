-- Create materialized view for Previsão de Entrega dashboard tab
-- This view provides the latest snapshot of empreendimentos with delivery forecast dates

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS mcmv_v2.vw_dados_prioritarios_prev_entrega;

-- Create the materialized view
CREATE MATERIALIZED VIEW mcmv_v2.vw_dados_prioritarios_prev_entrega AS
WITH latest AS (
    -- Get only the most recent snapshot (highest data_movimento)
    SELECT dp.*
    FROM mcmv_v2.dados_prioritarios dp
    JOIN (
        -- Get latest snapshot date once for performance
        SELECT MAX(data_movimento) AS max_mov
        FROM mcmv_v2.dados_prioritarios
    ) mx ON dp.data_movimento = mx.max_mov
)
SELECT
    apf,
    sg_uf,
    municipio,
    nome_empreendimento,
    modalidade,
    data_contratacao,
    data_previsao_entrega,
    -- Use uh_vigentes if available, otherwise calculate as contracted minus delivered
    COALESCE(uh_vigentes, GREATEST(0, uh_contratadas - COALESCE(uh_entregues, 0))) AS uh_a_entregar
FROM latest
WHERE data_previsao_entrega IS NOT NULL
ORDER BY data_previsao_entrega;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_prev_entrega_uf ON mcmv_v2.vw_dados_prioritarios_prev_entrega(sg_uf);
CREATE INDEX IF NOT EXISTS idx_prev_entrega_modalidade ON mcmv_v2.vw_dados_prioritarios_prev_entrega(modalidade);
CREATE INDEX IF NOT EXISTS idx_prev_entrega_data ON mcmv_v2.vw_dados_prioritarios_prev_entrega(data_previsao_entrega);

-- Grant permissions
GRANT SELECT ON mcmv_v2.vw_dados_prioritarios_prev_entrega TO PUBLIC;

-- Add refresh function to the existing refresh procedure
-- Note: This will be added to the nightly refresh job