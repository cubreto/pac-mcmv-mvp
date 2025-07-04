/**
 * MCMV Dashboard v5 - RURAL Program Analysis Page
 * Deep dive into RURAL program with detailed KPIs, charts, and financial breakdown
 */

import { useKPIs } from '../api/hooks'
import { KPISkeleton } from '../components/LoadingSpinner'
import { useGlobalFilters } from '../contexts/FilterContext'
import { ProgramErrorBoundary } from '../components/ProgramErrorBoundary'
import { useMemo } from 'react'
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

// STATUS_COLORS from original component
const STATUS_COLORS = [
  '#009688', '#00796B', '#4DB6AC', '#26A69A', '#80CBC4', '#B2DFDB'
]

export default function RuralPage() {
  const { filters } = useGlobalFilters()

  const chartFilters = useMemo(() => {
    if (!filters) return {}
    return {
      regiao: filters.region,
      state: filters.state,
      municipality: filters.municipality
    }
  }, [filters?.region, filters?.state, filters?.municipality])

  const { data: kpis, isLoading: kpisLoading, error: kpisError } = useKPIs({
    programa: 'RURAL',
    ...chartFilters
  })

  // Use our working hook
  const { data: chartData, isLoading: chartLoading, error: chartError } = useRuralRegionStatusChart(chartFilters)

  return (
    <ProgramErrorBoundary programName="RURAL">
      <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-orange-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          🌾 RURAL - Análise Detalhada
        </h1>
        <p className="text-orange-100">
          Programa habitacional para produtores rurais com análise financeira e de execução
        </p>
        <div className="mt-4 flex items-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-orange-400 rounded-full mr-2"></div>
            <span>Programa RURAL</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
            <span>Dados em Tempo Real</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-8">
          {/* KPI Cards */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🏢 Indicadores RURAL
            </h2>
            
            {kpisLoading ? (
              <KPISkeleton />
            ) : kpisError ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">❌ Error loading KPIs</p>
              </div>
            ) : kpis ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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
                  title="Valor Contratado"
                  value={kpis.total_contratado ? `R$ ${(kpis.total_contratado / 1000000000).toFixed(1)}B` : 'R$ 0'}
                  subtitle="Valor contratado"
                  color="purple"
                />
                <KPICard
                  title="Valor Investido"
                  value={kpis.total_investimento ? `R$ ${(kpis.total_investimento / 1000000000).toFixed(1)}B` : 'R$ 0'}
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
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-gray-600">Nenhum dado de KPI disponível</p>
              </div>
            )}
          </div>

        {/* Charts Section - Back to exact v3.1 working config */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* UH por Situação - ONLY WORKING CHART */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              📊 UH por Situação
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
              📊 Distribuição por Status
            </h3>
            <StatusDistributionChart filters={chartFilters} />
          </div>
        </div>

        {/* Timeline Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📈 Timeline - Previsão de Entrega
          </h3>
          <TimelineChart filters={chartFilters} />
        </div>

        {/* Financial Table */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📋 Resumo Financeiro
          </h3>
          <FinancialTable filters={chartFilters} />
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
          {statusValues.map((status, index) => (
            <Bar 
              key={status}
              dataKey={status}
              stackId="uh"
              fill={STATUS_COLORS[index % STATUS_COLORS.length]}
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
          {statusValues.map((status, index) => (
            <Bar 
              key={status}
              dataKey={status}
              stackId="uh"
              fill={STATUS_COLORS[index % STATUS_COLORS.length]}
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