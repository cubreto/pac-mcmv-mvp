-- Create ETL Quality Reports table for tracking data quality over time
CREATE TABLE IF NOT EXISTS mcmv_v2.etl_quality_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    total_issues INTEGER NOT NULL DEFAULT 0,
    quality_score NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    report_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Index for fast lookups
    CONSTRAINT unique_daily_report UNIQUE (report_date, table_name)
);

CREATE INDEX idx_quality_reports_date ON mcmv_v2.etl_quality_reports(report_date DESC);
CREATE INDEX idx_quality_reports_table ON mcmv_v2.etl_quality_reports(table_name);
CREATE INDEX idx_quality_reports_score ON mcmv_v2.etl_quality_reports(quality_score);

-- Create ETL Issues table for detailed issue tracking
CREATE TABLE IF NOT EXISTS mcmv_v2.etl_quality_issues (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES mcmv_v2.etl_quality_reports(id),
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    affected_records INTEGER,
    details JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quality_issues_report ON mcmv_v2.etl_quality_issues(report_id);
CREATE INDEX idx_quality_issues_type ON mcmv_v2.etl_quality_issues(issue_type);
CREATE INDEX idx_quality_issues_severity ON mcmv_v2.etl_quality_issues(severity);
CREATE INDEX idx_quality_issues_resolved ON mcmv_v2.etl_quality_issues(resolved);

-- Create view for latest quality status
CREATE OR REPLACE VIEW mcmv_v2.vw_latest_quality_status AS
WITH latest_reports AS (
    SELECT DISTINCT ON (table_name) 
        *
    FROM mcmv_v2.etl_quality_reports
    ORDER BY table_name, report_date DESC
)
SELECT 
    lr.table_name,
    lr.report_date,
    lr.total_issues,
    lr.quality_score,
    lr.report_data->>'statistics' as statistics,
    COUNT(DISTINCT qi.issue_type) as unique_issue_types,
    COUNT(qi.id) FILTER (WHERE qi.severity = 'high') as high_severity_issues,
    COUNT(qi.id) FILTER (WHERE qi.severity = 'medium') as medium_severity_issues,
    COUNT(qi.id) FILTER (WHERE qi.severity = 'low') as low_severity_issues,
    COUNT(qi.id) FILTER (WHERE NOT qi.resolved) as unresolved_issues
FROM latest_reports lr
LEFT JOIN mcmv_v2.etl_quality_issues qi ON lr.id = qi.report_id
GROUP BY lr.table_name, lr.report_date, lr.total_issues, lr.quality_score, lr.report_data;