/**
 * Timeline Chart - Simple and Stable
 * Follows WorkingChart pattern to avoid React Error #310
 */

import { useMemo } from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts'
import { useRuralTimelineChart } from '../../api/hooks'

interface TimelineChartProps {
  filters?: {
    regiao?: string
    state?: string
    municipality?: string
    status?: string
  }
}

// Timeline color
const TIMELINE_COLOR = '#009688'

export default function TimelineChart({ filters }: TimelineChartProps) {
  // Hook called unconditionally at top
  const { data, isLoading, error } = useRuralTimelineChart(filters)

  // Memoized chart data transformation
  const chartData = useMemo(() => {
    if (!data?.data?.length) return []
    
    return data.data.map((item: any) => {
      try {
        // Try to format the date/month properly
        const date = new Date(item.delivery_month || item.month || item.date)
        return {
          month: date.toLocaleDateString('pt-BR', { 
            year: 'numeric', 
            month: 'short' 
          }),
          total_uh: Number(item.total_uh) || 0,
          originalData: item
        }
      } catch (error) {
        return {
          month: item.delivery_month || item.month || 'Data Inválida',
          total_uh: Number(item.total_uh) || 0,
          originalData: item
        }
      }
    })
  }, [data])

  // Early returns after all hooks are called
  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Carregando timeline...</p>
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
        <p className="text-gray-500">Nenhum dado de previsão disponível</p>
      </div>
    )
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="80%">
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
            formatter={(value: any) => [value?.toLocaleString('pt-BR'), 'UH Previstas']}
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
            stroke={TIMELINE_COLOR}
            strokeWidth={3}
            dot={{ fill: TIMELINE_COLOR, strokeWidth: 2, r: 4 }}
            name="UH Previstas"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}