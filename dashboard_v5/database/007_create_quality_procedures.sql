-- =====================================================
-- MCMV Data Quality Stored Procedures and Functions
-- Date: 2025-07-19
-- Description: Create monitoring and validation procedures
-- =====================================================

-- =====================================================
-- 1. DATA QUALITY MONITORING FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION mcmv_v2.monitor_data_quality()
RETURNS TABLE (
    metric_name TEXT,
    metric_value NUMERIC,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check 1: Zero UH Contratadas
    RETURN QUERY
    SELECT 
        'Zero UH Contratadas'::TEXT,
        COUNT(*)::NUMERIC,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s records with zero UH contratadas but positive original values', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE uh_contratadas = 0 AND uh_original_contratadas > 0;

    -- Check 2: Invalid Modalidade
    RETURN QUERY
    SELECT 
        'Invalid Modalidade'::TEXT,
        COUNT(*)::NUMERIC,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s records with modalidade not in (FAR, FDS, RURAL)', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE modalidade NOT IN ('FAR', 'FDS', 'RURAL');

    -- Check 3: Delivery Exceeds Contracted
    RETURN QUERY
    SELECT 
        'Delivery Logic Error'::TEXT,
        COUNT(*)::NUMERIC,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            WHEN COUNT(*) < 100 THEN 'WARNING'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s records where delivered units exceed contracted units', COUNT(*))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE uh_entregues > uh_contratadas AND uh_contratadas > 0;

    -- Check 4: Missing Coordinates
    RETURN QUERY
    SELECT 
        'Missing Coordinates'::TEXT,
        ROUND(100.0 * COUNT(*)::NUMERIC / NULLIF((SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios), 0), 2),
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            WHEN COUNT(*) < (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios) * 0.5 THEN 'WARNING'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s percent of records missing coordinates', 
            ROUND(100.0 * COUNT(*)::NUMERIC / NULLIF((SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios), 0), 1))::TEXT
    FROM mcmv_v2.dados_prioritarios
    WHERE latitude IS NULL OR longitude IS NULL;

    -- Check 5: Date Inconsistencies
    RETURN QUERY
    WITH date_issues AS (
        SELECT COUNT(*) as count
        FROM mcmv_v2.projetos
        WHERE dt_inicio_obra < dt_contratacao
    )
    SELECT 
        'Date Logic Errors'::TEXT,
        count::NUMERIC,
        CASE 
            WHEN count = 0 THEN 'PASS'::TEXT
            WHEN count < 10 THEN 'WARNING'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s projects with start date before contract date', count)::TEXT
    FROM date_issues;

    -- Check 6: Financial Anomalies
    RETURN QUERY
    WITH financial_issues AS (
        SELECT COUNT(*) as count
        FROM mcmv_v2.projetos
        WHERE vr_total_investimento > vr_total_operacao
    )
    SELECT 
        'Financial Anomalies'::TEXT,
        count::NUMERIC,
        CASE 
            WHEN count = 0 THEN 'PASS'::TEXT
            WHEN count < 100 THEN 'WARNING'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s projects where investment exceeds total operation value', count)::TEXT
    FROM financial_issues;

    -- Check 7: Progress Percentage
    RETURN QUERY
    SELECT 
        'Invalid Progress Values'::TEXT,
        COUNT(*)::NUMERIC,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('%s projects with progress < 0 or > 100', COUNT(*))::TEXT
    FROM mcmv_v2.projetos
    WHERE pc_obra_realizada < 0 OR pc_obra_realizada > 100;

END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. DATA QUALITY SUMMARY VIEW
-- =====================================================
CREATE OR REPLACE VIEW mcmv_v2.vw_quality_summary AS
WITH quality_metrics AS (
    SELECT * FROM mcmv_v2.monitor_data_quality()
),
summary AS (
    SELECT 
        COUNT(*) FILTER (WHERE status = 'PASS') as passed,
        COUNT(*) FILTER (WHERE status = 'WARNING') as warnings,
        COUNT(*) FILTER (WHERE status = 'FAIL') as failed,
        COUNT(*) as total_checks
    FROM quality_metrics
)
SELECT 
    s.*,
    ROUND(100.0 * s.passed / NULLIF(s.total_checks, 0), 2) as pass_rate,
    CASE 
        WHEN s.failed = 0 AND s.warnings = 0 THEN 'EXCELLENT'
        WHEN s.failed = 0 THEN 'GOOD'
        WHEN s.failed <= 2 THEN 'NEEDS ATTENTION'
        ELSE 'CRITICAL'
    END as overall_status,
    CURRENT_TIMESTAMP as evaluated_at
FROM summary s;

-- =====================================================
-- 3. AUTOMATED FIX PROCEDURE
-- =====================================================
CREATE OR REPLACE FUNCTION mcmv_v2.auto_fix_common_issues()
RETURNS TABLE (
    issue_type TEXT,
    records_fixed INTEGER,
    status TEXT
) AS $$
DECLARE
    v_uh_fixed INTEGER;
    v_modalidade_fixed INTEGER;
    v_whitespace_fixed INTEGER;
BEGIN
    -- Fix UH mapping
    UPDATE mcmv_v2.dados_prioritarios
    SET uh_contratadas = uh_original_contratadas
    WHERE uh_contratadas = 0 AND uh_original_contratadas > 0;
    GET DIAGNOSTICS v_uh_fixed = ROW_COUNT;
    
    RETURN QUERY
    SELECT 'UH Field Mapping'::TEXT, v_uh_fixed, 
           CASE WHEN v_uh_fixed > 0 THEN 'FIXED' ELSE 'OK' END::TEXT;

    -- Fix modalidade
    UPDATE mcmv_v2.dados_prioritarios
    SET modalidade = 'FDS'
    WHERE modalidade = 'Entidades';
    GET DIAGNOSTICS v_modalidade_fixed = ROW_COUNT;
    
    RETURN QUERY
    SELECT 'Modalidade Mapping'::TEXT, v_modalidade_fixed,
           CASE WHEN v_modalidade_fixed > 0 THEN 'FIXED' ELSE 'OK' END::TEXT;

    -- Fix whitespace
    UPDATE mcmv_v2.dados_prioritarios
    SET municipio = TRIM(municipio)
    WHERE LENGTH(municipio) != LENGTH(TRIM(municipio));
    GET DIAGNOSTICS v_whitespace_fixed = ROW_COUNT;
    
    RETURN QUERY
    SELECT 'Whitespace Issues'::TEXT, v_whitespace_fixed,
           CASE WHEN v_whitespace_fixed > 0 THEN 'FIXED' ELSE 'OK' END::TEXT;

END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. QUALITY ALERT TRIGGERS
-- =====================================================
CREATE OR REPLACE FUNCTION mcmv_v2.check_quality_alerts()
RETURNS TABLE (
    alert_level TEXT,
    alert_message TEXT,
    metric_value NUMERIC
) AS $$
BEGIN
    -- Alert for high percentage of zero UH
    RETURN QUERY
    WITH zero_uh AS (
        SELECT 
            COUNT(*) FILTER (WHERE uh_contratadas = 0) as zero_count,
            COUNT(*) as total_count
        FROM mcmv_v2.dados_prioritarios
    )
    SELECT 
        'CRITICAL'::TEXT,
        'High percentage of zero UH contratadas'::TEXT,
        ROUND(100.0 * zero_count / NULLIF(total_count, 0), 2)
    FROM zero_uh
    WHERE zero_count > total_count * 0.1;

    -- Alert for invalid modalidade
    RETURN QUERY
    WITH invalid_mod AS (
        SELECT COUNT(*) as count
        FROM mcmv_v2.dados_prioritarios
        WHERE modalidade NOT IN ('FAR', 'FDS', 'RURAL')
    )
    SELECT 
        'HIGH'::TEXT,
        'Invalid modalidade values detected'::TEXT,
        count::NUMERIC
    FROM invalid_mod
    WHERE count > 0;

    -- Alert for delivery logic errors
    RETURN QUERY
    WITH delivery_errors AS (
        SELECT COUNT(*) as count
        FROM mcmv_v2.dados_prioritarios
        WHERE uh_entregues > uh_contratadas AND uh_contratadas > 0
    )
    SELECT 
        'MEDIUM'::TEXT,
        'Delivery exceeds contracted units'::TEXT,
        count::NUMERIC
    FROM delivery_errors
    WHERE count > 100;

END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. QUALITY REPORT GENERATION
-- =====================================================
CREATE OR REPLACE FUNCTION mcmv_v2.generate_quality_report()
RETURNS JSON AS $$
DECLARE
    v_report JSON;
BEGIN
    WITH report_data AS (
        SELECT 
            -- Summary statistics
            (SELECT COUNT(*) FROM mcmv_v2.dados_prioritarios) as total_dados_prioritarios,
            (SELECT COUNT(*) FROM mcmv_v2.projetos) as total_projetos,
            
            -- Quality metrics
            (SELECT array_to_json(array_agg(row_to_json(m))) 
             FROM mcmv_v2.monitor_data_quality() m) as quality_metrics,
            
            -- Alerts
            (SELECT array_to_json(array_agg(row_to_json(a))) 
             FROM mcmv_v2.check_quality_alerts() a) as active_alerts,
            
            -- Modalidade distribution
            (SELECT json_object_agg(modalidade, count) 
             FROM (
                 SELECT modalidade, COUNT(*) as count 
                 FROM mcmv_v2.dados_prioritarios 
                 GROUP BY modalidade
             ) t) as modalidade_distribution,
            
            -- Data freshness
            (SELECT MAX(data_movimento) FROM mcmv_v2.dados_prioritarios) as latest_data,
            
            -- Report metadata
            CURRENT_TIMESTAMP as report_generated_at
    )
    SELECT row_to_json(report_data) INTO v_report FROM report_data;
    
    RETURN v_report;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. CREATE QUALITY HISTORY TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS mcmv_v2.quality_history (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    quality_metrics JSON NOT NULL,
    alerts JSON,
    summary_stats JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_daily_report UNIQUE (report_date)
);

-- =====================================================
-- 7. AUTOMATED DAILY QUALITY CHECK FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION mcmv_v2.daily_quality_check()
RETURNS VOID AS $$
DECLARE
    v_report JSON;
BEGIN
    -- Generate quality report
    v_report := mcmv_v2.generate_quality_report();
    
    -- Store in history
    INSERT INTO mcmv_v2.quality_history (quality_metrics, alerts, summary_stats)
    VALUES (
        v_report->'quality_metrics',
        v_report->'active_alerts',
        v_report->>'summary_stats'
    )
    ON CONFLICT (report_date) 
    DO UPDATE SET 
        quality_metrics = EXCLUDED.quality_metrics,
        alerts = EXCLUDED.alerts,
        summary_stats = EXCLUDED.summary_stats,
        created_at = CURRENT_TIMESTAMP;
    
    -- Log result
    RAISE NOTICE 'Daily quality check completed at %', CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. GRANT PERMISSIONS
-- =====================================================
GRANT EXECUTE ON FUNCTION mcmv_v2.monitor_data_quality() TO PUBLIC;
GRANT EXECUTE ON FUNCTION mcmv_v2.auto_fix_common_issues() TO PUBLIC;
GRANT EXECUTE ON FUNCTION mcmv_v2.check_quality_alerts() TO PUBLIC;
GRANT EXECUTE ON FUNCTION mcmv_v2.generate_quality_report() TO PUBLIC;
GRANT EXECUTE ON FUNCTION mcmv_v2.daily_quality_check() TO PUBLIC;
GRANT SELECT ON mcmv_v2.vw_quality_summary TO PUBLIC;
GRANT SELECT ON mcmv_v2.quality_history TO PUBLIC;

-- =====================================================
-- 9. RUN INITIAL QUALITY CHECK
-- =====================================================
SELECT * FROM mcmv_v2.monitor_data_quality() ORDER BY status DESC, metric_name;