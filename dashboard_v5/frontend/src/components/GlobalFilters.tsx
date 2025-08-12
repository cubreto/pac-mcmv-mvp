/**
 * MCMV Dashboard v5 - Global Filters Component
 * Single filter bar that controls all tabs (Dashboard, RURAL, FAR, FDS)
 */

import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useFilters, useFilterSummary } from '../api/hooks'
import { useGlobalFilters } from '../contexts/FilterContext'
import { apiClient } from '../api/client'

export default function GlobalFilters() {
  const { filters, updateFilter, clearAllFilters } = useGlobalFilters()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const location = useLocation()
  
  // Determine if we should show the Program filter
  // Show it ONLY on the Resumo page ('/'), hide on program-specific pages
  const showProgramFilter = location.pathname === '/'

  // API hooks for filter data
  const { data: regions, isLoading: regionsLoading } = useFilters.useRegions()
  const { data: states, isLoading: statesLoading } = useFilters.useStates(filters.region)
  const { data: municipalities, isLoading: municipalitiesLoading } = useFilters.useMunicipalities(
    filters.region,
    filters.state
  )
  const { data: programs, isLoading: programsLoading } = useFilters.usePrograms(
    filters.region,
    filters.state,
    filters.municipality
  )

  // Filter summary for showing impact
  const { data: summary, isLoading: summaryLoading } = useFilterSummary(filters)

  const hasActiveFilters = Object.keys(filters).length > 0

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      await apiClient.downloadAnalyticalReport(filters)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Erro ao baixar relatório. Verifique sua conexão e tente novamente.')
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 transition-all duration-300 ${isCollapsed ? 'py-4' : ''}`}>
      {/* Header */}
      <div className={`flex items-center justify-between ${isCollapsed ? 'mb-0' : 'mb-6'}`}>
        <div className="flex items-center space-x-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              🔍 Filtros Globais
            </h3>
            {!isCollapsed && (
              <p className="text-sm text-gray-600 mt-1">
                Filtros de localização e programa aplicados em Resumo, RURAL, FAR e FDS
              </p>
            )}
            {isCollapsed && hasActiveFilters && (
              <p className="text-sm text-gray-600 mt-1">
                {Object.keys(filters).length} filtro(s) ativo(s) - {summary?.data?.total_projects?.toLocaleString('pt-BR') || '...'} projetos
              </p>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Download Button */}
          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Baixar relação analítica em CSV"
          >
            {isDownloading ? (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
            )}
            <span>{isDownloading ? 'Baixando...' : 'Download'}</span>
          </button>
          
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="px-3 py-1.5 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
            >
              🗑️ Limpar Tudo
            </button>
          )}
          
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded-md transition-colors flex items-center space-x-1"
          >
            {isCollapsed ? (
              <>
                <span>Expandir</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </>
            ) : (
              <>
                <span>Recolher</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Filter Grid */}
      {!isCollapsed && (
        <div className={`grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 ${showProgramFilter ? 'lg:grid-cols-4' : 'lg:grid-cols-3'}`}>
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

        {/* Program Filter - Only show on Resumo page */}
        {showProgramFilter && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🏗️ Programa
            </label>
            <select
              value={filters.programa || ''}
              onChange={(e) => updateFilter('programa', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              disabled={programsLoading}
            >
              <option value="">Todos os Programas</option>
              {programs?.data?.map((program) => (
                <option key={program.code} value={program.code}>
                  {program.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
      )}

      {/* Filter Summary */}
      {!isCollapsed && hasActiveFilters && (
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
      {(regionsLoading || statesLoading || municipalitiesLoading || programsLoading) && (
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