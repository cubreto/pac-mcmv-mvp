-- Create data quality history tracking tables
-- This enables trend analysis and monitoring over time

-- Create table for program quality history
CREATE TABLE IF NOT EXISTS mcmv_v2.data_quality_history (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    programa VARCHAR(20) NOT NULL,
    total_records INTEGER NOT NULL,
    completeness_score NUMERIC(5,2) NOT NULL,
    accuracy_score NUMERIC(5,2) NOT NULL,
    consistency_score NUMERIC(5,2) NOT NULL,
    overall_score NUMERIC(5,2) NOT NULL,
    -- Detailed metrics
    missing_contract_date INTEGER DEFAULT 0,
    missing_start_date INTEGER DEFAULT 0,
    missing_end_date INTEGER DEFAULT 0,
    missing_name INTEGER DEFAULT 0,
    missing_municipality INTEGER DEFAULT 0,
    missing_entity INTEGER DEFAULT 0,
    invalid_progress INTEGER DEFAULT 0,
    invalid_uh INTEGER DEFAULT 0,
    invalid_investment INTEGER DEFAULT 0,
    start_before_contract INTEGER DEFAULT 0,
    progress_without_start INTEGER DEFAULT 0,
    -- Summary statistics
    avg_progress NUMERIC(5,2),
    total_investment NUMERIC(20,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(snapshot_date, programa)
);

-- Create index for efficient queries
CREATE INDEX idx_quality_history_date_program 
ON mcmv_v2.data_quality_history(snapshot_date DESC, programa);

-- Create table for dados prioritarios quality history
CREATE TABLE IF NOT EXISTS mcmv_v2.dados_prioritarios_quality_history (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    modalidade VARCHAR(50) NOT NULL,
    total_records INTEGER NOT NULL,
    completeness_score NUMERIC(5,2) NOT NULL,
    accuracy_score NUMERIC(5,2) NOT NULL,
    consistency_score NUMERIC(5,2) NOT NULL,
    overall_score NUMERIC(5,2) NOT NULL,
    -- Detailed metrics
    missing_contract_date INTEGER DEFAULT 0,
    missing_delivery_date INTEGER DEFAULT 0,
    missing_name INTEGER DEFAULT 0,
    missing_municipality INTEGER DEFAULT 0,
    missing_ibge INTEGER DEFAULT 0,
    missing_coordinates INTEGER DEFAULT 0,
    missing_agent INTEGER DEFAULT 0,
    invalid_progress INTEGER DEFAULT 0,
    invalid_uh INTEGER DEFAULT 0,
    invalid_value INTEGER DEFAULT 0,
    -- Summary statistics
    avg_execution NUMERIC(5,2),
    total_contracted NUMERIC(20,2),
    total_disbursed NUMERIC(20,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(snapshot_date, modalidade)
);

-- Create index for efficient queries
CREATE INDEX idx_dados_quality_history_date_modalidade 
ON mcmv_v2.dados_prioritarios_quality_history(snapshot_date DESC, modalidade);

-- Create table for quality alerts configuration
CREATE TABLE IF NOT EXISTS mcmv_v2.quality_alerts_config (
    id SERIAL PRIMARY KEY,
    alert_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'threshold', 'trend', 'anomaly'
    target_metric VARCHAR(100) NOT NULL,
    target_program VARCHAR(20),
    threshold_value NUMERIC(5,2),
    comparison_operator VARCHAR(10), -- '<', '>', '<=', '>=', '='
    trend_period_days INTEGER,
    trend_threshold_percent NUMERIC(5,2),
    is_active BOOLEAN DEFAULT true,
    notification_emails TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create table for quality alert history
CREATE TABLE IF NOT EXISTS mcmv_v2.quality_alerts_history (
    id SERIAL PRIMARY KEY,
    alert_config_id INTEGER REFERENCES mcmv_v2.quality_alerts_config(id),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metric_value NUMERIC(10,2),
    alert_message TEXT,
    notification_sent BOOLEAN DEFAULT false,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE
);

-- Create function to capture quality snapshot
CREATE OR REPLACE FUNCTION mcmv_v2.capture_quality_snapshot()
RETURNS TABLE (
    programs_captured INTEGER,
    dados_captured INTEGER,
    snapshot_date DATE
) AS $$
DECLARE
    prog_count INTEGER := 0;
    dados_count INTEGER := 0;
    snap_date DATE := CURRENT_DATE;
BEGIN
    -- Capture program quality metrics
    INSERT INTO mcmv_v2.data_quality_history (
        snapshot_date, programa, total_records, 
        completeness_score, accuracy_score, consistency_score, overall_score,
        missing_contract_date, missing_start_date, missing_end_date,
        missing_name, missing_municipality, missing_entity,
        invalid_progress, invalid_uh, invalid_investment,
        start_before_contract, progress_without_start,
        avg_progress, total_investment
    )
    SELECT 
        snap_date,
        programa,
        COUNT(*) as total_records,
        -- Completeness Score
        ROUND((100.0 * (1 - (
            COUNT(CASE WHEN dt_contratacao IS NULL THEN 1 END)::float + 
            COUNT(CASE WHEN dt_inicio_obra IS NULL THEN 1 END) + 
            COUNT(CASE WHEN dt_previsao_conclusao_obra IS NULL THEN 1 END) + 
            COUNT(CASE WHEN no_empreendimento IS NULL OR no_empreendimento = '' THEN 1 END) + 
            COUNT(CASE WHEN no_municipio IS NULL OR no_municipio = '' THEN 1 END) + 
            COUNT(CASE WHEN entidade_responsavel IS NULL OR entidade_responsavel = '' THEN 1 END)
        ) / (COUNT(*) * 6)))::numeric, 2),
        -- Accuracy Score
        ROUND((100.0 * (1 - (
            COUNT(CASE WHEN pc_obra_realizada < 0 OR pc_obra_realizada > 100 THEN 1 END)::float + 
            COUNT(CASE WHEN uh_contratadas <= 0 THEN 1 END) + 
            COUNT(CASE WHEN vr_total_investimento <= 0 THEN 1 END)
        ) / (COUNT(*) * 3)))::numeric, 2),
        -- Consistency Score
        ROUND((100.0 * (1 - (
            COUNT(CASE WHEN dt_inicio_obra < dt_contratacao THEN 1 END)::float + 
            COUNT(CASE WHEN pc_obra_realizada > 0 AND dt_inicio_obra IS NULL THEN 1 END) + 
            COUNT(CASE WHEN vr_total_operacao > 0 AND vr_total_investimento = 0 THEN 1 END) + 
            COUNT(CASE WHEN vr_total_contrapartidas > vr_total_operacao THEN 1 END)
        ) / (COUNT(*) * 4)))::numeric, 2),
        -- Overall Score (weighted average)
        ROUND((
            (100.0 * (1 - (COUNT(CASE WHEN dt_contratacao IS NULL THEN 1 END)::float + COUNT(CASE WHEN dt_inicio_obra IS NULL THEN 1 END) + COUNT(CASE WHEN dt_previsao_conclusao_obra IS NULL THEN 1 END) + COUNT(CASE WHEN no_empreendimento IS NULL OR no_empreendimento = '' THEN 1 END) + COUNT(CASE WHEN no_municipio IS NULL OR no_municipio = '' THEN 1 END) + COUNT(CASE WHEN entidade_responsavel IS NULL OR entidade_responsavel = '' THEN 1 END)) / (COUNT(*) * 6)) * 0.4) +
            (100.0 * (1 - (COUNT(CASE WHEN pc_obra_realizada < 0 OR pc_obra_realizada > 100 THEN 1 END)::float + COUNT(CASE WHEN uh_contratadas <= 0 THEN 1 END) + COUNT(CASE WHEN vr_total_investimento <= 0 THEN 1 END)) / (COUNT(*) * 3)) * 0.3) +
            (100.0 * (1 - (COUNT(CASE WHEN dt_inicio_obra < dt_contratacao THEN 1 END)::float + COUNT(CASE WHEN pc_obra_realizada > 0 AND dt_inicio_obra IS NULL THEN 1 END) + COUNT(CASE WHEN vr_total_operacao > 0 AND vr_total_investimento = 0 THEN 1 END) + COUNT(CASE WHEN vr_total_contrapartidas > vr_total_operacao THEN 1 END)) / (COUNT(*) * 4)) * 0.3)
        )::numeric, 2),
        -- Detailed issue counts
        COUNT(CASE WHEN dt_contratacao IS NULL THEN 1 END),
        COUNT(CASE WHEN dt_inicio_obra IS NULL THEN 1 END),
        COUNT(CASE WHEN dt_previsao_conclusao_obra IS NULL THEN 1 END),
        COUNT(CASE WHEN no_empreendimento IS NULL OR no_empreendimento = '' THEN 1 END),
        COUNT(CASE WHEN no_municipio IS NULL OR no_municipio = '' THEN 1 END),
        COUNT(CASE WHEN entidade_responsavel IS NULL OR entidade_responsavel = '' THEN 1 END),
        COUNT(CASE WHEN pc_obra_realizada < 0 OR pc_obra_realizada > 100 THEN 1 END),
        COUNT(CASE WHEN uh_contratadas <= 0 THEN 1 END),
        COUNT(CASE WHEN vr_total_investimento <= 0 THEN 1 END),
        COUNT(CASE WHEN dt_inicio_obra < dt_contratacao THEN 1 END),
        COUNT(CASE WHEN pc_obra_realizada > 0 AND dt_inicio_obra IS NULL THEN 1 END),
        -- Summary stats
        AVG(pc_obra_realizada),
        SUM(vr_total_investimento)
    FROM mcmv_v2.projetos
    WHERE programa IN ('FAR', 'FDS', 'RURAL')
    GROUP BY programa
    ON CONFLICT (snapshot_date, programa) DO UPDATE
    SET 
        total_records = EXCLUDED.total_records,
        completeness_score = EXCLUDED.completeness_score,
        accuracy_score = EXCLUDED.accuracy_score,
        consistency_score = EXCLUDED.consistency_score,
        overall_score = EXCLUDED.overall_score,
        missing_contract_date = EXCLUDED.missing_contract_date,
        missing_start_date = EXCLUDED.missing_start_date,
        missing_end_date = EXCLUDED.missing_end_date,
        missing_name = EXCLUDED.missing_name,
        missing_municipality = EXCLUDED.missing_municipality,
        missing_entity = EXCLUDED.missing_entity,
        invalid_progress = EXCLUDED.invalid_progress,
        invalid_uh = EXCLUDED.invalid_uh,
        invalid_investment = EXCLUDED.invalid_investment,
        start_before_contract = EXCLUDED.start_before_contract,
        progress_without_start = EXCLUDED.progress_without_start,
        avg_progress = EXCLUDED.avg_progress,
        total_investment = EXCLUDED.total_investment,
        created_at = NOW();
    
    GET DIAGNOSTICS prog_count = ROW_COUNT;
    
    -- Return results
    programs_captured := prog_count;
    dados_captured := 0; -- Simplified for now
    snapshot_date := snap_date;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Create function to check alerts
CREATE OR REPLACE FUNCTION mcmv_v2.check_quality_alerts()
RETURNS TABLE (
    alerts_triggered INTEGER,
    alerts_checked INTEGER
) AS $$
DECLARE
    alert RECORD;
    current_value NUMERIC;
    should_trigger BOOLEAN;
    alert_msg TEXT;
    triggered_count INTEGER := 0;
    checked_count INTEGER := 0;
BEGIN
    -- Check each active alert
    FOR alert IN 
        SELECT * FROM mcmv_v2.quality_alerts_config 
        WHERE is_active = true
    LOOP
        checked_count := checked_count + 1;
        should_trigger := false;
        
        -- Check threshold alerts
        IF alert.alert_type = 'threshold' THEN
            -- Get current metric value
            EXECUTE format(
                'SELECT %I FROM mcmv_v2.data_quality_history 
                 WHERE programa = $1 AND snapshot_date = CURRENT_DATE',
                alert.target_metric
            ) INTO current_value USING alert.target_program;
            
            -- Check threshold
            IF alert.comparison_operator = '<' AND current_value < alert.threshold_value THEN
                should_trigger := true;
            ELSIF alert.comparison_operator = '>' AND current_value > alert.threshold_value THEN
                should_trigger := true;
            ELSIF alert.comparison_operator = '<=' AND current_value <= alert.threshold_value THEN
                should_trigger := true;
            ELSIF alert.comparison_operator = '>=' AND current_value >= alert.threshold_value THEN
                should_trigger := true;
            END IF;
            
            IF should_trigger THEN
                alert_msg := format('Alert: %s for %s is %s (%s %s %s)',
                    alert.target_metric, alert.target_program, current_value,
                    current_value, alert.comparison_operator, alert.threshold_value);
                    
                INSERT INTO mcmv_v2.quality_alerts_history (
                    alert_config_id, metric_value, alert_message
                ) VALUES (
                    alert.id, current_value, alert_msg
                );
                
                triggered_count := triggered_count + 1;
            END IF;
        END IF;
    END LOOP;
    
    alerts_triggered := triggered_count;
    alerts_checked := checked_count;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Add sample alert configurations
INSERT INTO mcmv_v2.quality_alerts_config (
    alert_name, alert_type, target_metric, target_program, 
    threshold_value, comparison_operator
) VALUES 
    ('FAR Low Completeness', 'threshold', 'completeness_score', 'FAR', 70, '<'),
    ('FDS Low Overall Quality', 'threshold', 'overall_score', 'FDS', 75, '<'),
    ('RURAL Low Accuracy', 'threshold', 'accuracy_score', 'RURAL', 80, '<')
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT EXECUTE ON FUNCTION mcmv_v2.capture_quality_snapshot() TO postgres;
GRANT EXECUTE ON FUNCTION mcmv_v2.check_quality_alerts() TO postgres;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mcmv_v2 TO postgres;

COMMENT ON TABLE mcmv_v2.data_quality_history IS 
'Historical tracking of data quality metrics for trend analysis and monitoring';

COMMENT ON TABLE mcmv_v2.quality_alerts_config IS 
'Configuration for automated data quality alerts and thresholds';

COMMENT ON FUNCTION mcmv_v2.capture_quality_snapshot() IS 
'Captures daily snapshot of data quality metrics for all programs';

COMMENT ON FUNCTION mcmv_v2.check_quality_alerts() IS 
'Checks configured alerts against current quality metrics and triggers notifications';