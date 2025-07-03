/**
 * MCMV Dashboard v5 - RURAL Chart Components
 * Specialized charts for RURAL program analysis
 */

import { useMemo, useState } from 'react'
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts'
import { 
  useRuralRegionStatusChart, 
  useRuralStatusDonutChart, 
  useRuralTimelineChart,
  useRuralFinancialTable 
} from '../../api/hooks'
import { ChartSkeleton } from '../LoadingSpinner'

// RURAL program colors
const RURAL_COLORS = {
  primary: '#009688',
  secondary: '#00796B',
  accent: '#4DB6AC',
  light: '#B2DFDB'
}

const STATUS_COLORS = [
  '#009688', '#00796B', '#4DB6AC', '#26A69A', '#80CBC4', '#B2DFDB'
]

interface RuralChartProps {
  filters?: {
    regiao?: string
    state?: string
    municipality?: string
    status?: string
  }
}

export function RuralRegionChart({ filters }: RuralChartProps) {
  const { data, isLoading, error } = useRuralRegionStatusChart(filters)

  if (isLoading) return <ChartSkeleton />
  
  if (error) {
    return (
      <div className="h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <p className="text-red-600">Erro ao carregar dados regionais</p>
      </div>
    )
  }

  if (!data?.data?.length) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Nenhum dado disponível</p>
      </div>
    )
  }

  // Transform data for stacked bar chart
  const chartData = useMemo(() => {
    const regionMap = new Map()
    
    data.data.forEach((item: any) => {
      const region = item.regiao
      if (!regionMap.has(region)) {
        regionMap.set(region, { regiao: region })
      }
      regionMap.get(region)[item.situacao_obra] = item.total_uh
    })
    
    return Array.from(regionMap.values())
  }, [data])

  // Get unique status values for legend
  const statusValues = [...new Set(data.data.map((item: any) => item.situacao_obra))] as string[]

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
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
            tickFormatter={(value) => value.toLocaleString('pt-BR')}
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

export function RuralStatusChart({ filters }: RuralChartProps) {
  const { data, isLoading, error } = useRuralStatusDonutChart(filters)

  if (isLoading) return <ChartSkeleton />
  
  if (error) {
    return (
      <div className="h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <p className="text-red-600">Erro ao carregar dados de situação</p>
      </div>
    )
  }

  if (!data?.data?.length) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Nenhum dado disponível</p>
      </div>
    )
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data.data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={100}
            paddingAngle={2}
            dataKey="total_uh"
            nameKey="status"
          >
            {data.data.map((_: any, index: number) => (
              <Cell 
                key={`cell-${index}`} 
                fill={STATUS_COLORS[index % STATUS_COLORS.length]} 
              />
            ))}
          </Pie>
          <Tooltip 
            formatter={(value: any) => [value?.toLocaleString('pt-BR'), 'UH']}
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RuralTimelineChart({ filters }: RuralChartProps) {
  const { data, isLoading, error } = useRuralTimelineChart(filters)

  if (isLoading) return <ChartSkeleton />
  
  if (error) {
    return (
      <div className="h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <p className="text-red-600">Erro ao carregar timeline</p>
      </div>
    )
  }

  if (!data?.data?.length) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Nenhum dado de previsão disponível</p>
      </div>
    )
  }

  // Transform data for timeline
  const chartData = useMemo(() => {
    if (!data?.data?.length) return []
    
    return data.data.map((item: any) => {
      try {
        const date = new Date(item.delivery_month)
        return {
          ...item,
          month: date.toLocaleDateString('pt-BR', { 
            year: 'numeric', 
            month: 'short' 
          })
        }
      } catch (error) {
        return {
          ...item,
          month: 'Data Inválida'
        }
      }
    })
  }, [data])

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="month" 
            fontSize={12}
            stroke="#666"
          />
          <YAxis 
            fontSize={12}
            stroke="#666"
            tickFormatter={(value) => value.toLocaleString('pt-BR')}
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
          <Line 
            type="monotone" 
            dataKey="total_uh" 
            stroke={RURAL_COLORS.primary}
            strokeWidth={3}
            dot={{ fill: RURAL_COLORS.primary, strokeWidth: 2, r: 4 }}
            name="UH Previstas"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RuralFinancialTable({ filters }: RuralChartProps) {
  const { data, isLoading, error } = useRuralFinancialTable(filters)
  const [showAll, setShowAll] = useState(false)
  const [expandedStates, setExpandedStates] = useState<Set<string>>(new Set())

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📋 Tabela Financeira por Município
        </h3>
        <div className="animate-pulse space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-8 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📋 Tabela Financeira por Município
        </h3>
        <div className="text-center py-8 text-red-600">
          Erro ao carregar dados financeiros
        </div>
      </div>
    )
  }

  if (!data?.data?.length) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📋 Tabela Financeira por Município
        </h3>
        <div className="text-center py-8 text-gray-500">
          Nenhum dado financeiro disponível
        </div>
      </div>
    )
  }

  // Group data by state
  const groupedData = useMemo(() => {
    const grouped = data.data.reduce((acc: any, row: any) => {
      if (!acc[row.uf]) {
        acc[row.uf] = {
          state: row.uf,
          municipalities: [],
          totals: {
            projects: 0,
            uh: 0,
            value: 0,
            investment: 0
          }
        }
      }
      acc[row.uf].municipalities.push(row)
      acc[row.uf].totals.projects += row.total_projetos || 0
      acc[row.uf].totals.uh += row.total_uh_contratadas || 0
      acc[row.uf].totals.value += row.total_valor_contratado || 0
      acc[row.uf].totals.investment += row.total_investimento || 0
      return acc
    }, {})

    return Object.values(grouped).sort((a: any, b: any) => b.totals.uh - a.totals.uh)
  }, [data])

  const displayData = showAll ? groupedData : groupedData.slice(0, 5)

  const toggleState = (stateCode: string) => {
    const newExpanded = new Set(expandedStates)
    if (newExpanded.has(stateCode)) {
      newExpanded.delete(stateCode)
    } else {
      newExpanded.add(stateCode)
    }
    setExpandedStates(newExpanded)
  }

  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          📋 Resumo Financeiro por Estado
        </h3>
        <div className="text-sm text-gray-500">
          {data.data.length} municípios • {groupedData.length} estados
        </div>
      </div>

      <div className="space-y-2">
        {displayData.map((stateGroup: any) => {
          const isExpanded = expandedStates.has(stateGroup.state)
          const avgInvestmentPerUH = stateGroup.totals.uh > 0 
            ? stateGroup.totals.investment / stateGroup.totals.uh 
            : 0

          return (
            <div key={stateGroup.state} className="border rounded-lg">
              {/* State Summary Row */}
              <div 
                className="px-4 py-3 bg-gray-50 hover:bg-gray-100 cursor-pointer flex items-center justify-between"
                onClick={() => toggleState(stateGroup.state)}
              >
                <div className="flex items-center space-x-4">
                  <div className="flex items-center">
                    <span className="text-lg mr-2">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                    <span className="font-semibold text-gray-900">
                      {stateGroup.state}
                    </span>
                    <span className="ml-2 text-sm text-gray-500">
                      ({stateGroup.municipalities.length} municípios)
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-6 text-sm">
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {stateGroup.totals.projects.toLocaleString('pt-BR')}
                    </div>
                    <div className="text-gray-500">Projetos</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {stateGroup.totals.uh.toLocaleString('pt-BR')}
                    </div>
                    <div className="text-gray-500">UH</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      R$ {(stateGroup.totals.investment / 1e6).toFixed(1)}M
                    </div>
                    <div className="text-gray-500">Investimento</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      R$ {avgInvestmentPerUH.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                    </div>
                    <div className="text-gray-500">Invest./UH</div>
                  </div>
                </div>
              </div>

              {/* Expanded Municipality Details */}
              {isExpanded && (
                <div className="border-t">
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead className="bg-gray-25">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Município
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Projetos
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            UH
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Investimento
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Invest./UH
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {stateGroup.municipalities
                          .sort((a: any, b: any) => (b.total_uh_contratadas || 0) - (a.total_uh_contratadas || 0))
                          .map((row: any, index: number) => (
                          <tr key={index} className="hover:bg-gray-25">
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {row.municipio}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {row.total_projetos?.toLocaleString('pt-BR')}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {row.total_uh_contratadas?.toLocaleString('pt-BR')}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              R$ {(row.total_investimento / 1e6)?.toFixed(1)}M
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              R$ {row.investimento_medio_uh?.toLocaleString('pt-BR')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Show More/Less Button */}
      {groupedData.length > 5 && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
          >
            {showAll ? 'Mostrar Menos' : `Mostrar Todos (${groupedData.length} estados)`}
          </button>
        </div>
      )}
    </div>
  )
}