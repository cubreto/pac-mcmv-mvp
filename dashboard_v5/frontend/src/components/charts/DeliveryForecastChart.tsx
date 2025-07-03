/**
 * MCMV Dashboard v5 - Delivery Forecast Chart
 * Time series visualization for delivery forecasts by program
 * Recreates v4 functionality with modern React + Recharts
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { DeliveryForecastDataPoint } from '../../api/client'

interface DeliveryForecastChartProps {
  data: DeliveryForecastDataPoint[]
  type: 'timeline' | 'cumulative'
}

const PROGRAM_COLORS = {
  'FAR': '#FF9F0A',  // Orange - matching v4
  'FDS': '#9733FF',  // Purple - matching v4  
  'RURAL': '#009688', // Teal - matching v4
  'default': '#9E9E9E'
}

const formatNumber = (value: number) => value.toLocaleString('pt-BR')

export function DeliveryForecastChart({ data, type }: DeliveryForecastChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Nenhum dado de previsão disponível
      </div>
    )
  }

  // Transform data for chart visualization
  const processedData = transformDataForChart(data, type)

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              <span className="font-medium">{entry.name}:</span> {formatNumber(entry.value)} UH
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
        📈 {type === 'timeline' ? 'Entregas por Mês' : 'Entregas Acumuladas'}
        <span className="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
          24 Meses
        </span>
      </h4>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={processedData} margin={{ top: 5, right: 30, left: 20, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="mes"
              tick={{ fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              tick={{ fontSize: 11 }}
              tickFormatter={formatNumber}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
            />
            {/* Dynamic lines for each program */}
            {getUniquePrograms(data).map((programa) => (
              <Line
                key={programa}
                type="monotone"
                dataKey={programa}
                stroke={PROGRAM_COLORS[programa as keyof typeof PROGRAM_COLORS] || PROGRAM_COLORS.default}
                strokeWidth={3}
                dot={{ strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, strokeWidth: 2 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// Helper function to transform data for chart
function transformDataForChart(data: DeliveryForecastDataPoint[], type: 'timeline' | 'cumulative') {
  // Group by month
  const monthlyData: Record<string, Record<string, number>> = {}
  
  data.forEach(item => {
    if (!monthlyData[item.ano_mes]) {
      monthlyData[item.ano_mes] = {}
    }
    monthlyData[item.ano_mes][item.programa] = item.numero_uhs
  })

  // Convert to array format and sort by month
  let chartData = Object.entries(monthlyData)
    .map(([mes, programData]) => ({
      mes: formatMonth(mes),
      ...programData
    }))
    .sort((a, b) => a.mes.localeCompare(b.mes))

  // If cumulative, calculate running totals
  if (type === 'cumulative') {
    const programs = getUniquePrograms(data)
    const cumulativeData: Record<string, number> = {}
    
    programs.forEach(programa => {
      cumulativeData[programa] = 0
    })

    chartData = chartData.map(monthData => {
      const result: any = { mes: monthData.mes }
      programs.forEach(programa => {
        cumulativeData[programa] += ((monthData as any)[programa] || 0)
        result[programa] = cumulativeData[programa]
      })
      return result
    })
  }

  return chartData
}

// Helper function to get unique programs
function getUniquePrograms(data: DeliveryForecastDataPoint[]): string[] {
  return Array.from(new Set(data.map(item => item.programa)))
}

// Helper function to format month for display
function formatMonth(anoMes: string): string {
  // Convert "2024-01" to "Jan/24"
  const [year, month] = anoMes.split('-')
  const monthNames = [
    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
  ]
  return `${monthNames[parseInt(month) - 1]}/${year.slice(-2)}`
}

export default DeliveryForecastChart