/**
 * MCMV Dashboard v5 - Dados Prioritários Page
 * Historical data analysis with 3-tab view
 */

import { useState } from 'react'
import { 
  useDadosPrioritarios, 
  useDadosPrioritariosFilters, 
  useDadosPrioritariosPrevisaoEntrega,
  useDadosPrioritariosEstadoAtual 
} from '../api/hooks'
import TodosOsDadosTab from '../components/TodosOsDadosTab'
import EstadoAtualTab from '../components/EstadoAtualTab'
import PrevisaoEntregaTab from '../components/PrevisaoEntregaTab'

interface DadosPrioritariosFilters {
  ano_contratacao?: number
  mes_movimento?: number
  ano_movimento?: number
  situacao_empreendimento?: string
  uf?: string
}

export default function DadosPrioritariosPage() {
  const [activeTab, setActiveTab] = useState('todos-os-dados')
  const [filters, setFilters] = useState<DadosPrioritariosFilters>({})
  
  // Reset month/year filters when switching to Estado Atual or Previsão de Entrega tabs
  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId)
    if (tabId === 'estado-atual' || tabId === 'previsao-entrega') {
      // Clear month/year filters that don't apply to these tabs
      setFilters(prev => {
        const { mes_movimento, ano_movimento, ...rest } = prev
        return rest
      })
    }
  }

  // Get dados prioritarios data with filters
  const { data, isLoading, error, isFetching } = useDadosPrioritarios(filters)
  const { data: filterOptions, isLoading: filtersLoading } = useDadosPrioritariosFilters()
  const { data: previsaoData, isLoading: previsaoLoading } = useDadosPrioritariosPrevisaoEntrega(filters)
  
  // Get estado atual data (May 2025 only) - only UF filter applies
  const { data: estadoAtualData, isLoading: estadoAtualLoading, error: estadoAtualError } = useDadosPrioritariosEstadoAtual({ 
    uf: filters.uf 
  })

  const updateFilter = (key: keyof DadosPrioritariosFilters, value: number | string | undefined) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Dados Prioritários
        </h1>
        <p className="text-lg text-gray-600 mt-2">
          Análise detalhada dos empreendimentos com dados históricos mensais
        </p>
      </div>

      {/* Info Cards - Show only for Estado Atual tab */}
      {activeTab === 'estado-atual' && (() => {
        const summaryData = activeTab === 'estado-atual' ? estadoAtualData?.summary : data?.summary;
        if (!summaryData) return null;
        
        return (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4 border-l-4 border-blue-500 shadow-sm">
              <p className="text-sm text-gray-600">Total de Projetos</p>
              <p className="text-2xl font-bold text-gray-900">{summaryData.total_projetos?.toLocaleString('pt-BR')}</p>
              <p className="text-xs text-gray-500 mt-1">
                {activeTab === 'estado-atual' ? 'Snapshot: Maio/2025' : 'Dados: Jan/2025 - Mai/2025'}
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border-l-4 border-green-500 shadow-sm">
              <p className="text-sm text-gray-600">UH Contratadas</p>
              <p className="text-2xl font-bold text-gray-900">{summaryData.total_uh_contratadas?.toLocaleString('pt-BR')}</p>
            </div>
            <div className="bg-white rounded-lg p-4 border-l-4 border-purple-500 shadow-sm">
              <p className="text-sm text-gray-600">Taxa de Entrega</p>
              <p className="text-2xl font-bold text-gray-900">{summaryData.overall_percentual_entregues}%</p>
            </div>
          </div>
        );
      })()}

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'todos-os-dados', name: 'Dados Históricos' },
              { id: 'estado-atual', name: 'Estado Atual' },
              { id: 'previsao-entrega', name: 'Previsão de Entrega' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">
              Filtros Específicos
            </h3>
            {filtersLoading && (
              <div className="flex items-center text-sm text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500 mr-2"></div>
                Carregando filtros...
              </div>
            )}
          </div>

          <div className={`grid grid-cols-1 md:grid-cols-2 ${activeTab === 'estado-atual' ? 'lg:grid-cols-3' : activeTab === 'previsao-entrega' ? 'lg:grid-cols-3' : 'lg:grid-cols-5'} gap-4`}>
            {/* Ano de Contratação - Hidden for Previsão de Entrega */}
            {activeTab !== 'previsao-entrega' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ano de Contratação
              </label>
              <select
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filters.ano_contratacao || ''}
                onChange={(e) => updateFilter('ano_contratacao', e.target.value ? parseInt(e.target.value) : undefined)}
              >
                <option value="">Todos</option>
                {filterOptions?.anos_contratacao?.map((year: number) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            )}

            {/* Ano de Movimento - Hidden for Estado Atual and Previsão de Entrega */}
            {activeTab !== 'estado-atual' && activeTab !== 'previsao-entrega' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ano de Movimento
                </label>
                <select
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={filters.ano_movimento || ''}
                  onChange={(e) => updateFilter('ano_movimento', e.target.value ? parseInt(e.target.value) : undefined)}
                >
                  <option value="">Todos</option>
                  {filterOptions?.movimento_dates && Object.keys(filterOptions.movimento_dates)
                    .map(year => parseInt(year))
                    .sort((a, b) => b - a)
                    .map((year: number) => (
                      <option key={year} value={year}>{year}</option>
                    ))
                  }
                </select>
              </div>
            )}

            {/* Mês de Movimento - Hidden for Estado Atual and Previsão de Entrega */}
            {activeTab !== 'estado-atual' && activeTab !== 'previsao-entrega' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mês de Movimento
                </label>
                <select
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={filters.mes_movimento || ''}
                  onChange={(e) => updateFilter('mes_movimento', e.target.value ? parseInt(e.target.value) : undefined)}
                  disabled={!filters.ano_movimento}
                >
                  <option value="">Todos</option>
                  {filters.ano_movimento && filterOptions?.movimento_dates?.[filters.ano_movimento]?.map((month: number) => {
                    const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    return (
                      <option key={month} value={month}>{monthNames[month - 1]}</option>
                    )
                  })}
                </select>
              </div>
            )}

            {/* Situação - Hidden for Previsão de Entrega */}
            {activeTab !== 'previsao-entrega' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Situação
              </label>
              <select
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filters.situacao_empreendimento || ''}
                onChange={(e) => updateFilter('situacao_empreendimento', e.target.value || undefined)}
              >
                <option value="">Todas</option>
                {filterOptions?.situacoes_empreendimento?.map((situacao: string) => (
                  <option key={situacao} value={situacao}>{situacao}</option>
                ))}
              </select>
            </div>
            )}

            {/* UF */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                UF
              </label>
              <select
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filters.uf || ''}
                onChange={(e) => updateFilter('uf', e.target.value || undefined)}
              >
                <option value="">Todas</option>
                {filterOptions?.ufs?.map((uf: string) => (
                  <option key={uf} value={uf}>{uf}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Active Filters Summary */}
          {Object.keys(filters).filter(k => filters[k as keyof DadosPrioritariosFilters]).length > 0 && (
            <div className="mt-4 flex items-center justify-between bg-blue-50 rounded-lg px-4 py-2">
              <span className="text-sm text-blue-700">
                {Object.keys(filters).filter(k => filters[k as keyof DadosPrioritariosFilters]).length} filtros ativos
              </span>
              <button
                onClick={() => setFilters({})}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Limpar filtros
              </button>
            </div>
          )}
        </div>

      {/* Tab Content */}
      {activeTab === 'todos-os-dados' && (
        <TodosOsDadosTab 
          data={data} 
          isLoading={isLoading} 
          error={error} 
          isFetching={isFetching} 
        />
      )}
      
      {activeTab === 'estado-atual' && (
        <EstadoAtualTab 
          data={estadoAtualData} 
          isLoading={estadoAtualLoading} 
          error={estadoAtualError} 
          isFetching={false} 
        />
      )}
      
      {activeTab === 'previsao-entrega' && (
        <PrevisaoEntregaTab 
          data={previsaoData} 
          isLoading={previsaoLoading} 
        />
      )}
    </div>
  )
}