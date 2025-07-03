/**
 * MCMV Dashboard v5 - API Client
 * Type-safe API client with smart caching and error handling
 */

import { QueryClient } from '@tanstack/react-query';

// API Configuration
const API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8001/api/v5';
const API_TIMEOUT = 10000; // 10 seconds

// Response Types
export interface KPIData {
  total_projetos: number;
  total_uh_contratadas: number;
  total_contratado: number;
  total_investimento: number;
  investimento_medio_por_uh: number;
  percentual_execucao_medio: number;
  uh_em_execucao: number;
  uh_nao_iniciadas: number;
  uh_concluidas: number;
  projetos_alto_risco: number;
  data_atualizacao?: string;
  metadata: Record<string, any>;
}

export interface RegionalData {
  regiao: string;
  total_projetos: number;
  total_uh: number;
  total_contratado: number;
  total_investimento: number;
  trabalho_social?: number;
  contrapartida?: number;
  percentual_execucao_medio?: number;
  em_execucao?: number;
  nao_iniciadas?: number;
  concluidas?: number;
  color?: string;
}

export interface RegionalSummary {
  data: RegionalData[];
  metadata: Record<string, any>;
}

export interface DeliveryForecastDataPoint {
  ano_mes: string;
  programa: string;
  numero_uhs: number;
  numero_projetos: number;
}

export interface DeliveryForecastSummary {
  total_months: number;
  total_uh_forecast: number;
  peak_month: string;
  programs_included: string[];
}

export interface DeliveryForecastResponse {
  data: DeliveryForecastDataPoint[];
  summary: DeliveryForecastSummary;
  metadata: Record<string, any>;
}

export interface TemporalDataPoint {
  mes_contratacao: string;
  programa: string;
  regiao?: string;
  projetos_contratados: number;
  uh_contratadas_mes: number;
  investimento_mes: number;
  projetos_acumulados: number;
  uh_acumuladas: number;
  media_movel_3meses: number;
}

export interface TemporalTrends {
  data: TemporalDataPoint[];
  metadata: Record<string, any>;
}

export interface DataQualityProgram {
  programa: string;
  total_records: number;
  missing_dt_contratacao: number;
  missing_dt_inicio_obra: number;
  missing_pc_obra: number;
  missing_empreendimento: number;
  invalid_percentual_obra: number;
  invalid_uh_contratadas: number;
  invalid_investimento: number;
  inicio_antes_contratacao: number;
  progresso_sem_inicio: number;
  data_quality_score: number;
  ultima_verificacao: string;
}

export interface DataQuality {
  programs: DataQualityProgram[];
  overall_score: number;
  minimum_acceptable_score: number;
  metadata: Record<string, any>;
}

export interface Configuration {
  programs: Record<string, any>;
  status_definitions: Record<string, any>;
  regions: Record<string, any>;
  charts: Record<string, any>;
  kpis: Record<string, any>;
  api_version: string;
  performance: Record<string, any>;
}

// Filter types
export interface FilterRegion {
  name: string;
  states: string[];
  project_count: number;
  total_uh: number;
}

export interface FilterState {
  code: string;
  region: string;
  project_count: number;
  total_uh: number;
}

export interface FilterMunicipality {
  name: string;
  state: string;
  project_count: number;
  total_uh: number;
}

export interface FilterStatus {
  code: string;
  label: string;
  description: string;
  project_count: number;
  total_uh: number;
}

export interface FilterProgram {
  code: string;
  name: string;
  project_count: number;
  total_uh: number;
  total_investment: number;
}

export interface FilterSummary {
  total_projects: number;
  total_uh: number;
  total_investment: number;
  avg_progress: number;
  states_count: number;
  municipalities_count: number;
  programs_count: number;
}

export interface FilterResponse<T> {
  data: T[];
  metadata: Record<string, any>;
}

export interface FilterSummaryResponse {
  data: FilterSummary;
  filters: Record<string, string>;
  metadata: Record<string, any>;
}

// API Client Class
class APIClient {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL: string = API_BASE_URL, timeout: number = API_TIMEOUT) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error ${response.status}: ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`Request timeout after ${this.timeout}ms`);
        }
        throw error;
      }
      
      throw new Error('Unknown API error');
    }
  }

  // KPI Endpoints
  async getKPIs(filters: {
    programa?: string;
    regiao?: string;
    status?: string;
    state?: string;
    municipality?: string;
  } = {}): Promise<KPIData> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });

    const queryString = params.toString();
    const endpoint = `/kpis${queryString ? `?${queryString}` : ''}`;

    return this.request<KPIData>(endpoint);
  }

  // Regional Summary
  async getRegionalSummary(programa?: string): Promise<RegionalSummary> {
    const params = new URLSearchParams();
    if (programa) params.append('programa', programa);

    const queryString = params.toString();
    const endpoint = `/regional${queryString ? `?${queryString}` : ''}`;

    return this.request<RegionalSummary>(endpoint);
  }

  // Program Summary
  async getProgramSummary(filters: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
    programa?: string;
  } = {}): Promise<RegionalSummary> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });

    const queryString = params.toString();
    const endpoint = `/programs${queryString ? `?${queryString}` : ''}`;

    return this.request<RegionalSummary>(endpoint);
  }

  // Temporal Trends
  async getTemporalTrends(filters: {
    programa?: string;
    regiao?: string;
    months?: number;
  } = {}): Promise<TemporalTrends> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, value.toString());
    });

    const queryString = params.toString();
    const endpoint = `/temporal${queryString ? `?${queryString}` : ''}`;

    return this.request<TemporalTrends>(endpoint);
  }

  // Delivery Forecast
  async getDeliveryForecast(programa?: string): Promise<DeliveryForecastResponse> {
    const params = new URLSearchParams();
    if (programa) params.append('programa', programa);

    const queryString = params.toString();
    const endpoint = `/delivery-forecast${queryString ? `?${queryString}` : ''}`;

    return this.request<DeliveryForecastResponse>(endpoint);
  }

  // Data Quality
  async getDataQuality(): Promise<DataQuality> {
    return this.request<DataQuality>('/data-quality');
  }

  // Configuration
  async getConfiguration(): Promise<Configuration> {
    return this.request<Configuration>('/config');
  }

  // ================================================
  // RURAL-SPECIFIC ENDPOINTS
  // ================================================

  async getRuralRegionStatusChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/rural/charts/region-status${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getRuralStatusDonutChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/rural/charts/status-donut${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getRuralTimelineChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/rural/charts/timeline${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getRuralFinancialTable(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/rural/financial-table${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  // ================================================
  // FAR-SPECIFIC ENDPOINTS
  // ================================================

  async getFARRegionStatusChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/far/charts/region-status${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getFARStatusDonutChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/far/charts/status-donut${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getFARTimelineChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/far/charts/timeline${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getFARFinancialTable(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/far/financial-table${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  // ================================================
  // FDS-SPECIFIC ENDPOINTS
  // ================================================

  async getFDSRegionStatusChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/fds/charts/region-status${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getFDSStatusDonutChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/fds/charts/status-donut${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getFDSTimelineChart(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/fds/charts/timeline${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getFDSFinancialTable(filters?: {
    regiao?: string;
    state?: string;
    municipality?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.regiao) params.append('regiao', filters.regiao);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.municipality) params.append('municipality', filters.municipality);
    if (filters?.status) params.append('status', filters.status);
    
    const queryString = params.toString();
    const url = `/fds/financial-table${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  // ================================================
  // DADOS PRIORITÁRIOS ENDPOINTS
  // ================================================

  async getDadosPrioritarios(filters?: {
    ano_contratacao?: number;
    mes_movimento?: number;
    ano_movimento?: number;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.ano_contratacao) params.append('ano_contratacao', filters.ano_contratacao.toString());
    if (filters?.mes_movimento) params.append('mes_movimento', filters.mes_movimento.toString());
    if (filters?.ano_movimento) params.append('ano_movimento', filters.ano_movimento.toString());
    
    const queryString = params.toString();
    const url = `/dados-prioritarios${queryString ? `?${queryString}` : ''}`;
    return this.request<any>(url);
  }

  async getDadosPrioritariosFilters(): Promise<any> {
    return this.request<any>('/dados-prioritarios/filters');
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; version: string }> {
    // Call health endpoint at root level, not under base_path
    const url = `${this.baseURL.replace('/api/v5', '')}/health`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Health check failed');
    return await response.json();
  }

  // Filter Endpoints
  async getRegions(): Promise<FilterResponse<FilterRegion>> {
    return this.request<FilterResponse<FilterRegion>>('/filters/regions');
  }

  async getStates(region?: string): Promise<FilterResponse<FilterState>> {
    const params = new URLSearchParams();
    if (region) params.append('region', region);

    const queryString = params.toString();
    const endpoint = `/filters/states${queryString ? `?${queryString}` : ''}`;

    return this.request<FilterResponse<FilterState>>(endpoint);
  }

  async getMunicipalities(
    region?: string,
    state?: string
  ): Promise<FilterResponse<FilterMunicipality>> {
    const params = new URLSearchParams();
    if (region) params.append('region', region);
    if (state) params.append('state', state);

    const queryString = params.toString();
    const endpoint = `/filters/municipalities${queryString ? `?${queryString}` : ''}`;

    return this.request<FilterResponse<FilterMunicipality>>(endpoint);
  }

  async getStatusOptions(): Promise<FilterResponse<FilterStatus>> {
    return this.request<FilterResponse<FilterStatus>>('/filters/status');
  }

  async getPrograms(
    region?: string,
    state?: string,
    municipality?: string
  ): Promise<FilterResponse<FilterProgram>> {
    const params = new URLSearchParams();
    if (region) params.append('region', region);
    if (state) params.append('state', state);
    if (municipality) params.append('municipality', municipality);

    const queryString = params.toString();
    const endpoint = `/filters/programs${queryString ? `?${queryString}` : ''}`;

    return this.request<FilterResponse<FilterProgram>>(endpoint);
  }

  async getFilterSummary(filters: {
    region?: string;
    state?: string;
    municipality?: string;
    status?: string;
    programa?: string;
  } = {}): Promise<FilterSummaryResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });

    const queryString = params.toString();
    const endpoint = `/filters/summary${queryString ? `?${queryString}` : ''}`;

    return this.request<FilterSummaryResponse>(endpoint);
  }
}

// Singleton API client instance
export const apiClient = new APIClient();

// React Query Configuration
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (renamed from cacheTime in v5)
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && error.message.includes('4')) {
          return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
      refetchOnMount: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Query Keys Factory
const baseKeys = ['mcmv'] as const

export const queryKeys = {
  all: baseKeys,
  kpis: (filters?: Record<string, string>) => 
    [...baseKeys, 'kpis', filters] as const,
  regional: (programa?: string) => 
    [...baseKeys, 'regional', programa] as const,
  temporal: (filters?: Record<string, any>) => 
    [...baseKeys, 'temporal', filters] as const,
  deliveryForecast: (programa?: string) => 
    [...baseKeys, 'delivery-forecast', programa] as const,
  dataQuality: () => [...baseKeys, 'data-quality'] as const,
  config: () => [...baseKeys, 'config'] as const,
  health: () => [...baseKeys, 'health'] as const,
  
  // Filter query keys
  filters: {
    all: [...baseKeys, 'filters'] as const,
    regions: () => [...baseKeys, 'filters', 'regions'] as const,
    states: (region?: string) => 
      [...baseKeys, 'filters', 'states', region] as const,
    municipalities: (region?: string, state?: string) => 
      [...baseKeys, 'filters', 'municipalities', region, state] as const,
    status: () => [...baseKeys, 'filters', 'status'] as const,
    programs: (region?: string, state?: string, municipality?: string) => 
      [...baseKeys, 'filters', 'programs', region, state, municipality] as const,
    summary: (filters?: Record<string, string>) => 
      [...baseKeys, 'filters', 'summary', filters] as const,
  },
};

// Custom Hooks for API calls
export { 
  useKPIs, 
  useRegionalSummary, 
  useTemporalTrends, 
  useDataQuality, 
  useConfiguration,
  useFilters,
  useFilterSummary
} from './hooks';