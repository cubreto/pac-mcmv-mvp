/**
 * MCMV Dashboard v5 - Quality Trend Chart Component
 * Shows quality score trends over time
 */

import { Line } from 'recharts'
import {
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface TrendDataPoint {
  snapshot_date: string
  overall_score: number
  completeness_score: number
  accuracy_score: number
  consistency_score: number
  score_change?: number
}

interface QualityTrendChartProps {
  data: TrendDataPoint[]
  height?: number
}

export default function QualityTrendChart({ data, height = 400 }: QualityTrendChartProps) {
  // Transform data for the chart
  const chartData = data.map(point => ({
    date: format(new Date(point.snapshot_date), 'dd/MM', { locale: ptBR }),
    fullDate: format(new Date(point.snapshot_date), 'dd/MM/yyyy', { locale: ptBR }),
    overall: point.overall_score,
    completeness: point.completeness_score,
    accuracy: point.accuracy_score,
    consistency: point.consistency_score,
    change: point.score_change
  }))

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{data.fullDate}</p>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Geral:</span>
              <span className="font-medium ml-4">{data.overall.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Completude:</span>
              <span className="font-medium ml-4">{data.completeness.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Precisão:</span>
              <span className="font-medium ml-4">{data.accuracy.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Consistência:</span>
              <span className="font-medium ml-4">{data.consistency.toFixed(1)}%</span>
            </div>
            {data.change !== null && data.change !== undefined && (
              <div className="flex justify-between items-center pt-2 border-t border-gray-200">
                <span className="text-gray-600">Variação:</span>
                <span className={`font-medium ml-4 ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {data.change >= 0 ? '+' : ''}{data.change.toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Tendência de Qualidade</h3>
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis 
            dataKey="date" 
            stroke="#6B7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6B7280"
            style={{ fontSize: '12px' }}
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ fontSize: '14px' }}
            iconType="line"
          />
          
          <Line
            type="monotone"
            dataKey="overall"
            name="Score Geral"
            stroke="#3B82F6"
            strokeWidth={3}
            dot={{ fill: '#3B82F6', r: 4 }}
            activeDot={{ r: 6 }}
          />
          
          <Line
            type="monotone"
            dataKey="completeness"
            name="Completude"
            stroke="#10B981"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#10B981', r: 3 }}
          />
          
          <Line
            type="monotone"
            dataKey="accuracy"
            name="Precisão"
            stroke="#F59E0B"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#F59E0B', r: 3 }}
          />
          
          <Line
            type="monotone"
            dataKey="consistency"
            name="Consistência"
            stroke="#8B5CF6"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#8B5CF6', r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* Legend with current values */}
      {chartData.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Valores Atuais:</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Geral</span>
              </div>
              <p className="text-lg font-semibold">{chartData[chartData.length - 1].overall.toFixed(1)}%</p>
            </div>
            <div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Completude</span>
              </div>
              <p className="text-lg font-semibold">{chartData[chartData.length - 1].completeness.toFixed(1)}%</p>
            </div>
            <div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Precisão</span>
              </div>
              <p className="text-lg font-semibold">{chartData[chartData.length - 1].accuracy.toFixed(1)}%</p>
            </div>
            <div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-purple-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Consistência</span>
              </div>
              <p className="text-lg font-semibold">{chartData[chartData.length - 1].consistency.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}