/**
 * MCMV Dashboard v5 - Program-Specific Filters Component
 * Cascading filters for program pages (excludes program selector since each page is program-specific)
 */

import { useState, useEffect } from 'react'
import { useFilters, useFilterSummary } from '../api/hooks'

export interface ProgramFilterState {
  region?: string
  state?: string
  municipality?: string
  status?: string
}

interface ProgramFiltersProps {
  onFiltersChange: (filters: ProgramFilterState) => void
  initialFilters?: ProgramFilterState
  className?: string
  program: string // The specific program (RURAL, FAR, FDS)
}

export default function ProgramFilters({
  onFiltersChange,
  initialFilters = {},
  className = '',
  program
}: ProgramFiltersProps) {
  const [filters, setFilters] = useState<ProgramFilterState>(initialFilters)

  // API hooks for filter data
  const { data: regions, isLoading: regionsLoading } = useFilters.useRegions()
  const { data: states, isLoading: statesLoading } = useFilters.useStates(filters.region)
  const { data: municipalities, isLoading: municipalitiesLoading } = useFilters.useMunicipalities(
    filters.region,
    filters.state
  )
  const { data: statusOptions, isLoading: statusLoading } = useFilters.useStatusOptions()

  // Filter summary for showing impact (include program filter for API call)
  const { data: summary, isLoading: summaryLoading } = useFilterSummary({
    ...filters,
    programa: program
  })

  // Update parent when filters change
  useEffect(() => {
    onFiltersChange(filters)
  }, [filters, onFiltersChange])

  const updateFilter = (key: keyof ProgramFilterState, value: string | undefined) => {
    setFilters(prev => {
      const newFilters = { ...prev, [key]: value || undefined }
      
      // Clear dependent filters when parent changes
      if (key === 'region') {
        delete newFilters.state
        delete newFilters.municipality
      } else if (key === 'state') {
        delete newFilters.municipality
      }
      
      // Remove undefined values
      Object.keys(newFilters).forEach(k => {
        if (newFilters[k as keyof ProgramFilterState] === undefined) {
          delete newFilters[k as keyof ProgramFilterState]
        }
      })
      
      return newFilters
    })
  }

  const clearAllFilters = () => {
    setFilters({})
  }

  const hasActiveFilters = Object.keys(filters).length > 0

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            🔍 Filtros Avançados
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Use os filtros em cascata para refinar sua análise
          </p>
        </div>
        
        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="px-3 py-1.5 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
          >
            🗑️ Limpar Tudo
          </button>
        )}
      </div>

      {/* Filter Grid - 4 columns since we exclude program filter */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Region Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🌎 Região
          </label>
          <select
            value={filters.region || ''}
            onChange={(e) => updateFilter('region', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            disabled={regionsLoading}
          >
            <option value="">Todas as Regiões</option>
            {regions?.data?.map((region) => (
              <option key={region.name} value={region.name}>
                {region.name}
              </option>
            ))}
          </select>
        </div>

        {/* State Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📍 Estado (UF)
          </label>
          <select
            value={filters.state || ''}
            onChange={(e) => updateFilter('state', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            disabled={statesLoading || !states?.data?.length}
          >
            <option value="">Todos os Estados</option>
            {states?.data?.map((state) => (
              <option key={state.code} value={state.code}>
                {state.code}
              </option>
            ))}
          </select>
        </div>

        {/* Municipality Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🏙️ Município
          </label>
          <select
            value={filters.municipality || ''}
            onChange={(e) => updateFilter('municipality', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            disabled={municipalitiesLoading || !municipalities?.data?.length}
          >
            <option value="">Todos os Municípios</option>
            {municipalities?.data?.map((municipality, index) => (
              <option key={`${municipality.name}-${index}`} value={municipality.name}>
                {municipality.name}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🚧 Situação da Obra
          </label>
          <select
            value={filters.status || ''}
            onChange={(e) => updateFilter('status', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            disabled={statusLoading}
          >
            <option value="">Todas as Situações</option>
            {statusOptions?.data?.map((status) => (
              <option key={status.code} value={status.code}>
                {status.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Filter Summary */}
      {hasActiveFilters && (
        <div className="border-t border-gray-200 pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-gray-600">
                  {Object.keys(filters).length} filtro(s) ativo(s)
                </span>
              </div>
              
              {summary?.data && !summaryLoading && (
                <>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-gray-600">
                      {summary.data.total_projects?.toLocaleString('pt-BR')} projetos encontrados
                    </span>
                  </div>
                  
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                    <span className="text-gray-600">
                      {summary.data.total_uh?.toLocaleString('pt-BR')} UH
                    </span>
                  </div>
                </>
              )}
            </div>
            
            {summaryLoading && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className="animate-spin w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full"></div>
                <span>Calculando...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading States */}
      {(regionsLoading || statesLoading || municipalitiesLoading || statusLoading) && (
        <div className="absolute inset-0 bg-white bg-opacity-50 flex items-center justify-center rounded-lg">
          <div className="flex items-center space-x-2 text-gray-600">
            <div className="animate-spin w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full"></div>
            <span>Carregando filtros...</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ProgramFilterState type is already exported above with the interface declaration