-- =====================================================
-- MCMV Critical Data Quality Fixes
-- Date: 2025-07-19
-- Description: Fix critical data quality issues identified in investigation
-- =====================================================

-- Start transaction for safety
BEGIN;

-- =====================================================
-- 1. FIX UH FIELD MAPPING ISSUE
-- =====================================================
-- Problem: 99.8% of records have zero uh_contratadas but values in uh_original_contratadas

-- First, let's verify the issue
DO $$
BEGIN
    RAISE NOTICE 'Before UH fix - Records with zero uh_contratadas: %', 
        (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios WHERE uh_contratadas = 0);
    RAISE NOTICE 'Records with uh_original_contratadas > 0: %', 
        (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios WHERE uh_original_contratadas > 0);
END $$;

-- Update uh_contratadas from uh_original_contratadas where needed
UPDATE mcmv_v2.dados_prioritarios
SET uh_contratadas = uh_original_contratadas
WHERE uh_contratadas = 0 
  AND uh_original_contratadas > 0;

-- Verify the fix
DO $$
BEGIN
    RAISE NOTICE 'After UH fix - Records with zero uh_contratadas: %', 
        (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios WHERE uh_contratadas = 0);
END $$;

-- =====================================================
-- 2. FIX MODALIDADE MAPPING
-- =====================================================
-- Problem: 2,307 records have "Entidades" instead of "FDS"

-- Verify the issue
DO $$
BEGIN
    RAISE NOTICE 'Before modalidade fix - Records with "Entidades": %', 
        (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios WHERE modalidade = 'Entidades');
END $$;

-- Update modalidade from Entidades to FDS
UPDATE mcmv_v2.dados_prioritarios
SET modalidade = 'FDS'
WHERE modalidade = 'Entidades';

-- Verify the fix
DO $$
BEGIN
    RAISE NOTICE 'After modalidade fix - Records with "Entidades": %', 
        (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios WHERE modalidade = 'Entidades');
    RAISE NOTICE 'Records with "FDS": %', 
        (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios WHERE modalidade = 'FDS');
END $$;

-- =====================================================
-- 3. FIX CHARACTER ENCODING ISSUES
-- =====================================================
-- Problem: Municipality names with encoding issues (Ã, Ç, etc.)

-- Create a mapping table for common encoding fixes
CREATE TEMP TABLE encoding_fixes (
    wrong_char TEXT,
    correct_char TEXT
);

INSERT INTO encoding_fixes VALUES
    ('Ã§', 'ç'),
    ('Ã£', 'ã'),
    ('Ã¡', 'á'),
    ('Ã¢', 'â'),
    ('Ã©', 'é'),
    ('Ãª', 'ê'),
    ('Ã­', 'í'),
    ('Ã³', 'ó'),
    ('Ã´', 'ô'),
    ('Ãµ', 'õ'),
    ('Ãº', 'ú'),
    ('Ã‡', 'Ç'),
    ('Ãƒ', 'Ã'),
    ('Ã', 'Á'),
    ('Ã‚', 'Â'),
    ('Ã‰', 'É'),
    ('ÃŠ', 'Ê'),
    ('Ã"', 'Ó'),
    ('Ã"', 'Ô'),
    ('Ã•', 'Õ');

-- Fix municipality names
UPDATE mcmv_v2.dados_prioritarios AS dp
SET municipio = (
    SELECT regexp_replace(
        regexp_replace(
            regexp_replace(
                regexp_replace(
                    regexp_replace(dp.municipio, 'Ã§', 'ç', 'g'),
                    'Ã£', 'ã', 'g'),
                'Ã¡', 'á', 'g'),
            'Ã©', 'é', 'g'),
        'Ã³', 'ó', 'g')
)
WHERE municipio LIKE '%Ã%';

-- Also fix nome_empreendimento if needed
UPDATE mcmv_v2.dados_prioritarios AS dp
SET nome_empreendimento = (
    SELECT regexp_replace(
        regexp_replace(
            regexp_replace(
                regexp_replace(
                    regexp_replace(dp.nome_empreendimento, 'Ã§', 'ç', 'g'),
                    'Ã£', 'ã', 'g'),
                'Ã¡', 'á', 'g'),
            'Ã©', 'é', 'g'),
        'Ã³', 'ó', 'g')
)
WHERE nome_empreendimento LIKE '%Ã%';

-- =====================================================
-- 4. TRIM WHITESPACE ISSUES
-- =====================================================
-- Clean any trailing/leading spaces

UPDATE mcmv_v2.dados_prioritarios
SET municipio = TRIM(municipio)
WHERE LENGTH(municipio) != LENGTH(TRIM(municipio));

UPDATE mcmv_v2.dados_prioritarios
SET nome_empreendimento = TRIM(nome_empreendimento)
WHERE nome_empreendimento IS NOT NULL 
  AND LENGTH(nome_empreendimento) != LENGTH(TRIM(nome_empreendimento));

-- =====================================================
-- 5. CREATE DATA QUALITY VIEW
-- =====================================================
-- Create a view that always shows current data quality metrics

CREATE OR REPLACE VIEW mcmv_v2.vw_data_quality_metrics AS
WITH quality_checks AS (
    SELECT 
        -- UH Issues
        COUNT(*) as total_records,
        SUM(CASE WHEN uh_contratadas = 0 THEN 1 ELSE 0 END) as zero_uh_count,
        SUM(CASE WHEN uh_entregues > uh_contratadas THEN 1 ELSE 0 END) as delivered_exceeds_contracted,
        
        -- Modalidade Issues
        SUM(CASE WHEN modalidade NOT IN ('FAR', 'FDS', 'RURAL') THEN 1 ELSE 0 END) as invalid_modalidade,
        
        -- Encoding Issues
        SUM(CASE WHEN municipio LIKE '%Ã%' THEN 1 ELSE 0 END) as encoding_issues,
        
        -- Whitespace Issues
        SUM(CASE WHEN municipio != TRIM(municipio) THEN 1 ELSE 0 END) as whitespace_issues,
        
        -- Date Issues (we don't have delivery date in dados_prioritarios)
        0 as missing_delivery_date,
        
        -- Coordinate Issues
        SUM(CASE WHEN latitude IS NULL OR longitude IS NULL THEN 1 ELSE 0 END) as missing_coordinates,
        SUM(CASE WHEN latitude = 0 OR longitude = 0 THEN 1 ELSE 0 END) as zero_coordinates
    
    FROM mcmv_v2.dados_prioritarios
)
SELECT 
    total_records,
    ROUND(100.0 * zero_uh_count / NULLIF(total_records, 0), 2) as pct_zero_uh,
    ROUND(100.0 * delivered_exceeds_contracted / NULLIF(total_records, 0), 2) as pct_delivery_exceeds_contract,
    ROUND(100.0 * invalid_modalidade / NULLIF(total_records, 0), 2) as pct_invalid_modalidade,
    ROUND(100.0 * encoding_issues / NULLIF(total_records, 0), 2) as pct_encoding_issues,
    ROUND(100.0 * whitespace_issues / NULLIF(total_records, 0), 2) as pct_whitespace_issues,
    ROUND(100.0 * missing_delivery_date / NULLIF(total_records, 0), 2) as pct_missing_delivery_date,
    ROUND(100.0 * missing_coordinates / NULLIF(total_records, 0), 2) as pct_missing_coordinates,
    ROUND(100.0 * zero_coordinates / NULLIF(total_records, 0), 2) as pct_zero_coordinates,
    CURRENT_TIMESTAMP as checked_at
FROM quality_checks;

-- =====================================================
-- 6. CREATE VALIDATION FUNCTIONS
-- =====================================================

-- Function to validate dados_prioritarios data
CREATE OR REPLACE FUNCTION mcmv_v2.validate_dados_prioritarios()
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check 1: UH validation
    RETURN QUERY
    SELECT 
        'UH Contratadas Validation'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s records with zero UH contratadas', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE uh_contratadas = 0 AND uh_original_contratadas > 0;

    -- Check 2: Modalidade validation
    RETURN QUERY
    SELECT 
        'Modalidade Validation'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s records with invalid modalidade', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE modalidade NOT IN ('FAR', 'FDS', 'RURAL');

    -- Check 3: Encoding validation
    RETURN QUERY
    SELECT 
        'Character Encoding Validation'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'WARNING'::TEXT
        END,
        format('%s records with potential encoding issues', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE municipio LIKE '%Ã%' OR nome_empreendimento LIKE '%Ã%';

    -- Check 4: Whitespace validation
    RETURN QUERY
    SELECT 
        'Whitespace Validation'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'WARNING'::TEXT
        END,
        format('%s records with whitespace issues', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE municipio != TRIM(municipio);

    -- Check 5: Delivery logic validation
    RETURN QUERY
    SELECT 
        'Delivery Logic Validation'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'WARNING'::TEXT
        END,
        format('%s records where delivered > contracted', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE uh_entregues > uh_contratadas AND uh_contratadas > 0;

END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. RUN VALIDATION
-- =====================================================
SELECT * FROM mcmv_v2.validate_dados_prioritarios();

-- Show final summary
SELECT * FROM mcmv_v2.vw_data_quality_metrics;

-- If everything looks good, commit the transaction
-- COMMIT;

-- If there are issues, rollback
-- ROLLBACK;