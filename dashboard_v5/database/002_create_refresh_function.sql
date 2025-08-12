-- Create function to refresh all materialized views in mcmv_v2 schema
-- This function refreshes materialized views concurrently to avoid locking

CREATE OR REPLACE FUNCTION mcmv_v2.refresh_all_materialized_views()
RETURNS TABLE (
    view_name TEXT,
    refresh_status TEXT,
    refresh_time INTERVAL
) AS $$
DECLARE
    mat_view RECORD;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    error_msg TEXT;
BEGIN
    -- Log start
    RAISE NOTICE 'Starting materialized view refresh at %', clock_timestamp();
    
    -- Loop through all materialized views in mcmv_v2 schema
    FOR mat_view IN 
        SELECT 
            schemaname,
            matviewname 
        FROM pg_matviews 
        WHERE schemaname = 'mcmv_v2' 
        ORDER BY matviewname
    LOOP
        start_time := clock_timestamp();
        
        BEGIN
            -- Try to refresh concurrently (requires unique index)
            EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I.%I', 
                          mat_view.schemaname, mat_view.matviewname);
            
            end_time := clock_timestamp();
            
            -- Return success for this view
            view_name := mat_view.schemaname || '.' || mat_view.matviewname;
            refresh_status := 'SUCCESS';
            refresh_time := end_time - start_time;
            
            RAISE NOTICE 'Refreshed % in %', view_name, refresh_time;
            
            RETURN NEXT;
            
        EXCEPTION 
            WHEN OTHERS THEN
                -- If concurrent refresh fails, try non-concurrent
                BEGIN
                    EXECUTE format('REFRESH MATERIALIZED VIEW %I.%I', 
                                  mat_view.schemaname, mat_view.matviewname);
                    
                    end_time := clock_timestamp();
                    
                    -- Return success with warning
                    view_name := mat_view.schemaname || '.' || mat_view.matviewname;
                    refresh_status := 'SUCCESS (non-concurrent)';
                    refresh_time := end_time - start_time;
                    
                    RAISE WARNING 'Refreshed % non-concurrently in %', view_name, refresh_time;
                    
                    RETURN NEXT;
                    
                EXCEPTION
                    WHEN OTHERS THEN
                        -- Log error and continue with other views
                        GET STACKED DIAGNOSTICS error_msg = MESSAGE_TEXT;
                        
                        end_time := clock_timestamp();
                        
                        view_name := mat_view.schemaname || '.' || mat_view.matviewname;
                        refresh_status := 'ERROR: ' || error_msg;
                        refresh_time := end_time - start_time;
                        
                        RAISE WARNING 'Failed to refresh %: %', view_name, error_msg;
                        
                        RETURN NEXT;
                END;
        END;
        
    END LOOP;
    
    -- If no materialized views found
    IF NOT FOUND THEN
        view_name := 'mcmv_v2.*';
        refresh_status := 'No materialized views found';
        refresh_time := interval '0 seconds';
        RETURN NEXT;
    END IF;
    
    RAISE NOTICE 'Completed materialized view refresh at %', clock_timestamp();
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission to the application user
GRANT EXECUTE ON FUNCTION mcmv_v2.refresh_all_materialized_views() TO postgres;

-- Create a comment to document the function
COMMENT ON FUNCTION mcmv_v2.refresh_all_materialized_views() IS 
'Refreshes all materialized views in the mcmv_v2 schema. 
Attempts concurrent refresh first (non-blocking), falls back to regular refresh if needed.
Returns a table showing the status and timing of each refresh operation.';