/**
 * MCMV Dashboard v5 - FAR Program Analysis Page
 * Deep dive into FAR program with detailed KPIs, charts, and financial breakdown
 */

import { useState, useMemo } from 'react'
import { useKPIs } from '../api/hooks'
import { KPISkeleton } from '../components/LoadingSpinner'
import { useGlobalFilters } from '../contexts/FilterContext'
import { ProgramErrorBoundary } from '../components/ProgramErrorBoundary'
// import { FARRegionChart } from '../components/charts/FARCharts'
import FARWorkingChart from '../components/charts/FARWorkingChart'
import FARStatusDistributionChart from '../components/charts/FARStatusDistributionChart'
import FARTimelineChart from '../components/charts/FARTimelineChart'
import FARFinancialTable from '../components/charts/FARFinancialTable'
import { formatCurrencyDashboard } from '../utils/formatters'
import GlobalFilters from '../components/GlobalFilters'

export default function FARPage() {
  const [activeTab, setActiveTab] = useState('visao-geral')
  const { filters } = useGlobalFilters()
  
  const tabs = [
    { id: 'visao-geral', label: 'Visão Geral' },
    { id: 'analise-detalhada', label: 'Análise Detalhada' },
    { id: 'analise-financeira', label: 'Análise Financeira' },
  ]

  // Memoize chart filters to prevent infinite re-renders
  const chartFilters = useMemo(() => ({
    regiao: filters.region,
    state: filters.state,
    municipality: filters.municipality
  }), [filters.region, filters.state, filters.municipality])

  // Get FAR-specific KPI data with global filters applied
  const { data: kpis, isLoading: kpisLoading, error: kpisError } = useKPIs({
    programa: 'FAR',
    ...chartFilters
  })

  return (
    <ProgramErrorBoundary programName="FAR">
      <div className="space-y-8">
      {/* Program Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg shadow-lg p-6 text-white">
        <h1 className="text-2xl font-bold">
          FAR - Fundo de Arrendamento Residencial
        </h1>
      </div>

      {/* Global Filters */}
      <GlobalFilters />

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'visao-geral' && (
            <div className="space-y-8">
              {/* KPI Cards */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Indicadores FAR
                  </h2>
                  {kpis?.data_atualizacao && (
                    <span className="text-sm text-gray-500">
                      Posição: {new Date(kpis.data_atualizacao).toLocaleDateString('pt-BR')}
                    </span>
                  )}
                </div>
          
          {kpisLoading ? (
            <KPISkeleton />
          ) : kpisError || !kpis || (kpis.total_projetos === 0 && kpis.total_uh_contratadas === 0) ? (
            <div className="text-center py-8 text-gray-500">
              <p className="text-lg">Nenhum dado disponível para os filtros selecionados</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <KPICard
                title="Total Projetos"
                value={kpis.total_projetos?.toLocaleString('pt-BR') || '0'}
                subtitle="Projetos FAR"
                color="blue"
              />
              <KPICard
                title="UH Contratadas"
                value={kpis.total_uh_contratadas?.toLocaleString('pt-BR') || '0'}
                subtitle="Unidades Habitacionais"
                color="green"
              />
              <KPICard
                title="Valor Investido"
                value={kpis.total_investimento ? formatCurrencyDashboard(kpis.total_investimento) : 'R$ 0'}
                subtitle="Total investido"
                color="orange"
              />
              <KPICard
                title="Investimento/UH"
                value={kpis.investimento_medio_por_uh ? `R$ ${kpis.investimento_medio_por_uh.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}` : 'R$ 0'}
                subtitle="Média por unidade"
                color="teal"
              />
            </div>
          )}
              </div>
            </div>
          )}

          {activeTab === 'analise-detalhada' && (
            <div className="space-y-8">
              {/* Charts Section */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* UH por Região e Situação */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    UH por Região e Situação
                  </h3>
                  {kpisLoading ? (
                    <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                      <p className="text-gray-500">Carregando...</p>
                    </div>
                  ) : (
                    <FARWorkingChart filters={chartFilters} />
                  )}
                </div>

                {/* Status Distribution Chart */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Distribuição por Status
                  </h3>
                  <FARStatusDistributionChart filters={chartFilters} />
                </div>
              </div>

              {/* Timeline Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Timeline - Previsão de Entrega dos Empreendimentos
                </h3>
                <FARTimelineChart filters={chartFilters} />
              </div>
            </div>
          )}

          {activeTab === 'analise-financeira' && (
            <div className="space-y-8">
              {/* Financial Table */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Tabela Financeira FAR
                </h3>
                <FARFinancialTable filters={chartFilters} />
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
    </ProgramErrorBoundary>
  )
}

interface KPICardProps {
  title: string
  value: string
  subtitle: string
  color: 'blue' | 'green' | 'purple' | 'orange' | 'teal'
}

function KPICard({ title, value, subtitle, color }: KPICardProps) {
  const colorClasses = {
    blue: 'bg-blue-500 text-blue-600 bg-blue-50',
    green: 'bg-green-500 text-green-600 bg-green-50',
    purple: 'bg-purple-500 text-purple-600 bg-purple-50',
    orange: 'bg-orange-500 text-orange-600 bg-orange-50',
    teal: 'bg-teal-500 text-teal-600 bg-teal-50',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 border-l-4 border-l-blue-500 hover:shadow-md transition-shadow">
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full ${colorClasses[color].split(' ')[0]} mr-3`}></div>
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-600">{title}</div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{subtitle}</div>
        </div>
      </div>
    </div>
  )
}