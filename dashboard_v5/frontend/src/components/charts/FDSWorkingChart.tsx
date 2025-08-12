/**
 * FDS Working Chart - Simple and Stable
 * Follows exact same pattern as FAR/RURAL WorkingChart to avoid React Error #310
 */

import { useMemo } from 'react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts'
import { useFDSRegionStatusChart } from '../../api/hooks'
import { getStatusColor } from '../../constants/statusColors'

interface FDSWorkingChartProps {
  filters?: {
    regiao?: string
    state?: string
    municipality?: string
    status?: string
  }
}

export default function FDSWorkingChart({ filters }: FDSWorkingChartProps) {
  // Hook called unconditionally at top
  const { data, isLoading, error } = useFDSRegionStatusChart(filters)

  // EXACT SAME transformation logic as FAR WorkingChart but stable
  const chartData = useMemo(() => {
    if (!data?.data?.length) return []
    
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
    [...new Set(data?.data
      ?.map((item: any) => item?.situacao_obra)
      .filter(Boolean)
    )] as string[], 
    [data]
  )

  // Early returns after all hooks are called
  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Carregando chart...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <p className="text-red-600">❌ Erro no gráfico: {error.message}</p>
      </div>
    )
  }

  if (!chartData.length) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Nenhum dado disponível para o gráfico</p>
      </div>
    )
  }

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