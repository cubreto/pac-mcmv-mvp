/**
 * MCMV Dashboard v5 - RURAL Program Analysis Page
 * Deep dive into RURAL program with detailed KPIs, charts, and financial breakdown
 */

import { useState, useMemo } from 'react'
import { useKPIs } from '../api/hooks'
import { KPISkeleton } from '../components/LoadingSpinner'
import { useGlobalFilters } from '../contexts/FilterContext'
import { ProgramErrorBoundary } from '../components/ProgramErrorBoundary'
import { formatCurrencyDashboard } from '../utils/formatters'
// Importing hooks to recreate our working test component
import { useRuralRegionStatusChart } from '../api/hooks'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts'
// Import Timeline chart - DISABLED: causes infinite re-render loops
// import { RuralTimelineChart } from '../components/charts/RuralCharts'
// Import new stable status chart
import StatusDistributionChart from '../components/charts/StatusDistributionChart'
// Import new stable timeline chart
import TimelineChart from '../components/charts/TimelineChart'
// Import new stable financial table
import FinancialTable from '../components/charts/FinancialTable'
// Import centralized status colors
import { getStatusColor } from '../constants/statusColors'
import GlobalFilters from '../components/GlobalFilters'
import RuralFilters from '../components/RuralFilters'

export default function RuralPage() {
  const [activeTab, setActiveTab] = useState('visao-geral')
  const [tipo, setTipo] = useState<string | undefined>()
  const [modalidadeProposta, setModalidadeProposta] = useState<string | undefined>()
  const { filters } = useGlobalFilters()
  
  const tabs = [
    { id: 'visao-geral', label: 'Visão Geral' },
    { id: 'analise-detalhada', label: 'Análise Detalhada' },
    { id: 'analise-financeira', label: 'Análise Financeira' },
  ]

  const chartFilters = useMemo(() => {
    if (!filters) return { tipo, modalidade_proposta: modalidadeProposta }
    return {
      regiao: filters.region,
      state: filters.state,
      municipality: filters.municipality,
      tipo,
      modalidade_proposta: modalidadeProposta
    }
  }, [filters?.region, filters?.state, filters?.municipality, tipo, modalidadeProposta])

  const { data: kpis, isLoading: kpisLoading, error: kpisError } = useKPIs({
    programa: 'RURAL',
    ...chartFilters
  })

  // Use our working hook
  const { data: chartData, isLoading: chartLoading, error: chartError } = useRuralRegionStatusChart(chartFilters)

  return (
    <ProgramErrorBoundary programName="RURAL">
      <div className="space-y-8">
      {/* Program Header */}
      <div className="bg-gradient-to-r from-orange-600 to-orange-800 rounded-lg shadow-lg p-6 text-white">
        <h1 className="text-2xl font-bold">
          RURAL - Programa Nacional de Habitação Rural
        </h1>
      </div>

      {/* Global Filters */}
      <GlobalFilters />
      
      {/* RURAL Specific Filters */}
      <RuralFilters 
        tipo={tipo}
        modalidadeProposta={modalidadeProposta}
        onTipoChange={setTipo}
        onModalidadeChange={setModalidadeProposta}
      />

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
                    ? 'border-orange-500 text-orange-600'
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
                    Indicadores RURAL
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
                  subtitle="Projetos RURAL"
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
                  value={kpis.investimento_medio_por_uh ? `R$ ${kpis.investimento_medio_por_uh.toLocaleString('pt-BR')}` : 'R$ 0'}
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
                {/* UH por Situação */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    UH por Situação
                  </h3>
                  {chartLoading ? (
                    <KPISkeleton />
                  ) : chartError ? (
                    <div className="h-64 flex items-center justify-center bg-red-50 rounded-lg">
                      <p className="text-red-600">❌ Chart Error: {chartError.message}</p>
                    </div>
                  ) : (
                    <WorkingChart data={chartData} />
                  )}
                </div>

                {/* Status Distribution Chart */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Distribuição por Status
                  </h3>
                  <StatusDistributionChart filters={chartFilters} />
                </div>
              </div>

              {/* Timeline Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Timeline - Previsão de Entrega dos Empreendimentos
                </h3>
                <TimelineChart filters={chartFilters} />
              </div>
            </div>
          )}

          {activeTab === 'analise-financeira' && (
            <div className="space-y-8">
              {/* Financial Table */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Resumo Financeiro
                </h3>
                <FinancialTable filters={chartFilters} />
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
    </ProgramErrorBoundary>
  )
}

// Our working chart component from v3.0 testing
function WorkingChart({ data }: { data: any }) {
  if (!data?.data?.length) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">No chart data available</p>
      </div>
    )
  }

  // EXACT SAME transformation logic as original but stable
  const chartData = useMemo(() => {
    const regionMap = new Map()
    
    data.data.forEach((item: any) => {
      const region = item?.regiao
      const situacao = item?.situacao_obra
      const totalUh = item?.total_uh
      
      if (!region || !situacao || totalUh == null) {
        return
      }
      
      if (!regionMap.has(region)) {
        regionMap.set(region, { regiao: region })
      }
      regionMap.get(region)[situacao] = Number(totalUh) || 0
    })
    
    return Array.from(regionMap.values())
  }, [data])

  const statusValues = useMemo(() => 
    [...new Set(data.data
      .map((item: any) => item?.situacao_obra)
      .filter(Boolean)
    )] as string[], 
    [data]
  )

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="80%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="regiao" 
            fontSize={12}
            stroke="#666"
          />
          <YAxis 
            fontSize={12}
            stroke="#666"
            tickFormatter={(value) => (value != null ? value.toLocaleString('pt-BR') : '0')}
          />
          <Tooltip 
            formatter={(value: any) => [value?.toLocaleString('pt-BR'), 'UH']}
            labelStyle={{ color: '#333' }}
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          <Legend />
          {statusValues.map((status) => (
            <Bar 
              key={status}
              dataKey={status}
              stackId="uh"
              fill={getStatusColor(status)}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// Removed unused MapTransformationTest component to fix TypeScript errors
/*
function MapTransformationTest({ data }: { data: any }) {
  if (!data?.data?.length) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">No chart data available</p>
      </div>
    )
  }

  // EXACT SAME transformation logic as original RuralRegionChart (lines 73-95)
  const chartData = useMemo(() => {
    const regionMap = new Map()
    
    data.data.forEach((item: any) => {
      const region = item?.regiao
      const situacao = item?.situacao_obra
      const totalUh = item?.total_uh
      
      if (!region || !situacao || totalUh == null) {
        return
      }
      
      if (!regionMap.has(region)) {
        regionMap.set(region, { regiao: region })
      }
      regionMap.get(region)[situacao] = Number(totalUh) || 0
    })
    
    return Array.from(regionMap.values())
  }, [data])

  // EXACT SAME statusValues logic as original (lines 97-103)
  const statusValues = useMemo(() => 
    [...new Set(data.data
      .map((item: any) => item?.situacao_obra)
      .filter(Boolean)
    )] as string[], 
    [data]
  )

  // Test: Use EXACT color mapping from original component
  return (
    <div className="h-64">
      <h4 className="font-semibold mb-2 px-4">📊 Original Colors Test v3.0</h4>
      <p className="text-xs text-gray-500 px-4 mb-2">
        Regions: {chartData.length}, Status Types: {statusValues.length}, Showing: EXACT ORIGINAL COLORS
      </p>
      <ResponsiveContainer width="100%" height="80%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="regiao" 
            fontSize={12}
            stroke="#666"
          />
          <YAxis 
            fontSize={12}
            stroke="#666"
            tickFormatter={(value) => (value != null ? value.toLocaleString('pt-BR') : '0')}
          />
          <Tooltip 
            formatter={(value: any) => [value?.toLocaleString('pt-BR'), 'UH']}
            labelStyle={{ color: '#333' }}
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          <Legend />
          {statusValues.map((status) => (
            <Bar 
              key={status}
              dataKey={status}
              stackId="uh"
              fill={getStatusColor(status)}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
*/

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
    <div className="bg-white rounded-lg shadow p-6 border-l-4 border-l-orange-500 hover:shadow-md transition-shadow">
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