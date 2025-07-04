/**
 * FDS Status Distribution Chart - Simple and Stable
 * Follows WorkingChart pattern to avoid React Error #310
 */

import { useMemo } from 'react'
import { ResponsiveContainer, PieChart, Pie, Tooltip, Legend } from 'recharts'
import { useFDSStatusDonutChart } from '../../api/hooks'

interface FDSStatusDistributionChartProps {
  filters?: {
    regiao?: string
    state?: string
    municipality?: string
    status?: string
  }
}

// Simple colors array
const STATUS_COLORS = ['#009688', '#00796B', '#4DB6AC', '#26A69A', '#80CBC4']

export default function FDSStatusDistributionChart({ filters }: FDSStatusDistributionChartProps) {
  // Hook called unconditionally at top
  const { data, isLoading, error } = useFDSStatusDonutChart(filters)

  // Memoized chart data transformation
  const chartData = useMemo(() => {
    if (!data?.data?.length) return []
    
    return data.data.map((item: any, index: number) => ({
      name: item.status || 'Sem Status',
      value: Number(item.total_uh) || 0,
      fill: STATUS_COLORS[index % STATUS_COLORS.length]
    }))
  }, [data])

  // Early returns after all hooks are called
  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Carregando distribuição...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <p className="text-red-600">❌ Erro: {error.message}</p>
      </div>
    )
  }

  if (!chartData.length) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Nenhum dado de status disponível</p>
      </div>
    )
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            outerRadius={80}
            dataKey="value"
            nameKey="name"
          />
          <Tooltip 
            formatter={(value: any) => [value?.toLocaleString('pt-BR'), 'UH']}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}