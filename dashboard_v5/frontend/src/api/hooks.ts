/**
 * MCMV Dashboard v5 - React Query Hooks
 * Custom hooks for API data fetching with smart caching
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { 
  apiClient, 
  queryKeys, 
  KPIData, 
  RegionalSummary, 
  TemporalTrends, 
  DataQuality, 
  Configuration,
  DeliveryForecastResponse,
  FilterRegion,
  FilterState,
  FilterMunicipality,
  FilterStatus,
  FilterProgram,
  FilterResponse,
  FilterSummaryResponse
} from './client';

// KPI Hooks
export function useKPIs(
  filters: {
    programa?: string;
    regiao?: string;
    status?: string;
    state?: string;
    municipality?: string;
  } = {},
  options?: UseQueryOptions<KPIData>
) {
  return useQuery({
    queryKey: queryKeys.kpis(filters),
    queryFn: () => apiClient.getKPIs(filters),
    staleTime: 30 * 60 * 1000, // 30 minutes for KPIs (stable data)
    ...options,
  });
}

// Regional Summary Hook
export function useRegionalSummary(
  programa?: string,
  options?: UseQueryOptions<RegionalSummary>
) {
  return useQuery({
    queryKey: queryKeys.regional(programa),
    queryFn: () => apiClient.getRegionalSummary(programa),
    staleTime: 30 * 60 * 1000, // 30 minutes for regional data
    ...options,
  });
}

// Program Summary Hook
export function useProgramSummary(
  filters: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
    programa?: string;
  } = {},
  options?: UseQueryOptions<RegionalSummary>
) {
  return useQuery({
    queryKey: ['mcmv', 'program-summary', filters],
    queryFn: () => apiClient.getProgramSummary(filters),
    staleTime: 30 * 60 * 1000, // 30 minutes for program data
    ...options,
  });
}

// Temporal Trends Hook
export function useTemporalTrends(
  filters: {
    programa?: string;
    regiao?: string;
    months?: number;
  } = {},
  options?: UseQueryOptions<TemporalTrends>
) {
  return useQuery({
    queryKey: queryKeys.temporal(filters),
    queryFn: () => apiClient.getTemporalTrends(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes for temporal data
    ...options,
  });
}

// Delivery Forecast Hook
export function useDeliveryForecast(
  programa?: string,
  options?: UseQueryOptions<DeliveryForecastResponse>
) {
  return useQuery({
    queryKey: queryKeys.deliveryForecast(programa),
    queryFn: () => apiClient.getDeliveryForecast(programa),
    staleTime: 30 * 60 * 1000, // 30 minutes for forecast data
    ...options,
  });
}

// Data Quality Hook
export function useDataQuality(
  options?: UseQueryOptions<DataQuality>
) {
  return useQuery({
    queryKey: queryKeys.dataQuality(),
    queryFn: () => apiClient.getDataQuality(),
    staleTime: 60 * 60 * 1000, // 1 hour for data quality (changes slowly)
    ...options,
  });
}

// ================================================
// RURAL-SPECIFIC HOOKS
// ================================================

export function useRuralRegionStatusChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['rural', 'charts', 'region-status', filters],
    queryFn: () => apiClient.getRuralRegionStatusChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2, // Reduce retry attempts to prevent hanging
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useRuralStatusDonutChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['rural', 'charts', 'status-donut', filters],
    queryFn: () => apiClient.getRuralStatusDonutChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useRuralTimelineChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['rural', 'charts', 'timeline', filters],
    queryFn: () => apiClient.getRuralTimelineChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useRuralFinancialTable(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['rural', 'financial-table', filters],
    queryFn: () => apiClient.getRuralFinancialTable(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes for financial data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

// ================================================
// FAR-SPECIFIC HOOKS
// ================================================

export function useFARRegionStatusChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['far', 'charts', 'region-status', filters],
    queryFn: () => apiClient.getFARRegionStatusChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useFARStatusDonutChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['far', 'charts', 'status-donut', filters],
    queryFn: () => apiClient.getFARStatusDonutChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useFARTimelineChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['far', 'charts', 'timeline', filters],
    queryFn: () => apiClient.getFARTimelineChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useFARFinancialTable(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['far', 'financial-table', filters],
    queryFn: () => apiClient.getFARFinancialTable(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes for financial data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

// ================================================
// FDS-SPECIFIC HOOKS
// ================================================

export function useFDSRegionStatusChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['fds', 'charts', 'region-status', filters],
    queryFn: () => apiClient.getFDSRegionStatusChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useFDSStatusDonutChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['fds', 'charts', 'status-donut', filters],
    queryFn: () => apiClient.getFDSStatusDonutChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useFDSTimelineChart(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['fds', 'charts', 'timeline', filters],
    queryFn: () => apiClient.getFDSTimelineChart(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for chart data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

export function useFDSFinancialTable(
  filters?: { regiao?: string; state?: string; municipality?: string; status?: string },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['fds', 'financial-table', filters],
    queryFn: () => apiClient.getFDSFinancialTable(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes for financial data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    ...options,
  });
}

// Configuration Hook (cached aggressively)
export function useConfiguration(
  options?: UseQueryOptions<Configuration>
) {
  return useQuery({
    queryKey: queryKeys.config(),
    queryFn: () => apiClient.getConfiguration(),
    staleTime: 60 * 60 * 1000, // 1 hour for configuration
    gcTime: 24 * 60 * 60 * 1000, // 24 hours cache time (renamed from cacheTime in v5)
    ...options,
  });
}

// Health Check Hook
export function useHealthCheck(
  options?: UseQueryOptions<{ status: string; version: string }>
) {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => apiClient.healthCheck(),
    staleTime: 1 * 60 * 1000, // 1 minute for health checks
    refetchInterval: 2 * 60 * 1000, // Auto-refetch every 2 minutes
    ...options,
  });
}

// Combined hook for dashboard data (preloads everything)
export function useDashboardData(
  filters: {
    programa?: string;
    regiao?: string;
    status?: string;
  } = {}
) {
  const kpis = useKPIs(filters);
  const regional = useRegionalSummary(filters.programa);
  const temporal = useTemporalTrends({
    programa: filters.programa, 
    regiao: filters.regiao, 
    months: 24
  });
  const config = useConfiguration();

  return {
    kpis,
    regional,
    temporal,
    config,
    isLoading: kpis.isLoading || regional.isLoading || temporal.isLoading || config.isLoading,
    isError: kpis.isError || regional.isError || temporal.isError || config.isError,
    error: kpis.error || regional.error || temporal.error || config.error,
  };
}

// Program-specific hooks for instant tab switching
export function useRuralData(regiao?: string) {
  return useDashboardData({ programa: 'RURAL', regiao });
}

export function useFARData(regiao?: string) {
  return useDashboardData({ programa: 'FAR', regiao });
}

export function useFDSData(regiao?: string) {
  return useDashboardData({ programa: 'FDS', regiao });
}

// ================================================
// DADOS PRIORITÁRIOS HOOKS
// ================================================

export function useDadosPrioritarios(
  filters?: {
    ano_contratacao?: number;
    mes_movimento?: number;
    ano_movimento?: number;
  },
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['dados-prioritarios', filters],
    queryFn: () => apiClient.getDadosPrioritarios(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes for historical data
    ...options,
  });
}

export function useDadosPrioritariosFilters(
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: ['dados-prioritarios', 'filters'],
    queryFn: () => apiClient.getDadosPrioritariosFilters(),
    staleTime: 60 * 60 * 1000, // 1 hour for filter options
    ...options,
  });
}

// ================================================
// FILTER HOOKS
// ================================================

// Regions Hook
export function useRegions(
  options?: UseQueryOptions<FilterResponse<FilterRegion>>
) {
  return useQuery({
    queryKey: queryKeys.filters.regions(),
    queryFn: () => apiClient.getRegions(),
    staleTime: 60 * 60 * 1000, // 1 hour for regions (static data)
    ...options,
  });
}

// States Hook
export function useStates(
  region?: string,
  options?: UseQueryOptions<FilterResponse<FilterState>>
) {
  return useQuery({
    queryKey: queryKeys.filters.states(region),
    queryFn: () => apiClient.getStates(region),
    staleTime: 60 * 60 * 1000, // 1 hour for states (static data)
    enabled: true, // Always enabled - region filter applied server-side
    ...options,
  });
}

// Municipalities Hook
export function useMunicipalities(
  region?: string,
  state?: string,
  options?: UseQueryOptions<FilterResponse<FilterMunicipality>>
) {
  return useQuery({
    queryKey: queryKeys.filters.municipalities(region, state),
    queryFn: () => apiClient.getMunicipalities(region, state),
    staleTime: 30 * 60 * 1000, // 30 minutes for municipalities
    enabled: true, // Always enabled - filters applied server-side
    ...options,
  });
}

// Status Options Hook
export function useStatusOptions(
  options?: UseQueryOptions<FilterResponse<FilterStatus>>
) {
  return useQuery({
    queryKey: queryKeys.filters.status(),
    queryFn: () => apiClient.getStatusOptions(),
    staleTime: 60 * 60 * 1000, // 1 hour for status options (static data)
    ...options,
  });
}

// Programs Hook
export function usePrograms(
  region?: string,
  state?: string,
  municipality?: string,
  options?: UseQueryOptions<FilterResponse<FilterProgram>>
) {
  return useQuery({
    queryKey: queryKeys.filters.programs(region, state, municipality),
    queryFn: () => apiClient.getPrograms(region, state, municipality),
    staleTime: 30 * 60 * 1000, // 30 minutes for programs
    enabled: true, // Always enabled - filters applied server-side
    ...options,
  });
}

// Filter Summary Hook
export function useFilterSummary(
  filters: {
    region?: string;
    state?: string;
    municipality?: string;
    status?: string;
    programa?: string;
  } = {},
  options?: UseQueryOptions<FilterSummaryResponse>
) {
  // Only fetch if there are actual filters applied
  const hasFilters = Object.values(filters).some(value => value !== undefined && value !== '');
  
  return useQuery({
    queryKey: queryKeys.filters.summary(filters),
    queryFn: () => apiClient.getFilterSummary(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes for filter summary (changes frequently)
    enabled: hasFilters,
    ...options,
  });
}

// Grouped filter hooks for easy consumption
export const useFilters = {
  useRegions,
  useStates,
  useMunicipalities,
  useStatusOptions,
  usePrograms,
};