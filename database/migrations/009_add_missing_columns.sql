-- Add missing columns to vw_empreendimentos_unificado that the enhanced dashboard expects

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
    ps.percentual_obra_realizado AS percentual_mcmv,
    ps.data_inicio_obra,
    ps.situacao_atual,
    ps.data_atualizacao_situacao,
    ps.etiquetas,
    ps.observacoes,
    ps.uh_estimadas,
    ps.uf AS uf_beneficiaria,
    -- Add calculated fields
    CASE
        WHEN ps.percentual_obra_realizado < 10
         AND ps.data_inicio_obra < CURRENT_DATE - INTERVAL '180 days'
        THEN TRUE ELSE FALSE
    END AS alto_risco,
    CASE 
        WHEN ps.percentual_obra_realizado >= 100 THEN TRUE 
        ELSE FALSE 
    END AS projeto_completado,
    -- Add the missing financial columns that the dashboard expects
    ps.valor_investimento AS valor_investimento_mcmv,
    0 AS valor_investimento_pac,  -- Since these are MCMV projects, PAC investment is 0
    ps.valor_investimento + COALESCE(ps.valor_repasse, 0) AS valor_investimento_total
FROM projeto_status ps
WHERE ps.tipo_programa = 'MCMV-HIS'
AND ps.programa IN ('FAR', 'FDS', 'RURAL');

COMMENT ON VIEW mcmv_pj.vw_empreendimentos_unificado IS 'View unificada com todas as colunas esperadas pelo dashboard enhanced';
