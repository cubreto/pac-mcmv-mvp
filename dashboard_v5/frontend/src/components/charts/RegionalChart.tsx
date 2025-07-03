/**
 * MCMV Dashboard v5 - Regional Analysis Chart
 * High-performance interactive visualizations with Recharts
 * Updated: 2025-07-02 05:40
 */

import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { RegionalData } from '../../api/client'

interface RegionalChartProps {
  data: RegionalData[]
  type: 'pie' | 'bar' | 'mixed'
}

const COLORS = {
  'Nordeste': '#FF9800',
  'Sudeste': '#2196F3', 
  'Norte': '#4CAF50',
  'Centro-Oeste': '#9C27B0',
  'Sul': '#FF5722',
  'default': '#9E9E9E'
}

const formatCurrency = (value: number) => {
  if (value >= 1e9) return `R$ ${(value / 1e9).toFixed(1)}bi`
  if (value >= 1e6) return `R$ ${(value / 1e6).toFixed(1)}M`
  return `R$ ${value.toLocaleString('pt-BR')}`
}

const formatNumber = (value: number) => value.toLocaleString('pt-BR')

export function RegionalChart({ data, type }: RegionalChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Nenhum dado disponível para a tabela regional
      </div>
    )
  }

  // Debug: log the data and type to see what's being received
  console.log('RegionalChart received:', { data, type, length: data.length })
  console.log('First data item:', data[0])

  // Ensure region names are properly formatted
  const formattedData = data.map(item => ({
    ...item,
    regiao: item.regiao || 'Região não identificada'
  }))

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-4 border rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.regiao}</p>
          <p className="text-blue-600">
            <span className="font-medium">Projetos:</span> {formatNumber(data.total_projetos)}
          </p>
          <p className="text-green-600">
            <span className="font-medium">UH Total:</span> {formatNumber(data.total_uh)}
          </p>
          <p className="text-purple-600">
            <span className="font-medium">Investimento:</span> {formatCurrency(data.total_investimento)}
          </p>
          <p className="text-orange-600">
            <span className="font-medium">% Execução:</span> {data.percentual_execucao_medio.toFixed(1)}%
          </p>
        </div>
      )
    }
    return null
  }

  if (type === 'pie') {
    return (
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={formattedData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ regiao, percent }) => `${regiao} ${(percent * 100).toFixed(1)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="total_uh"
              nameKey="regiao"
            >
              {formattedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[entry.regiao as keyof typeof COLORS] || COLORS.default} 
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (type === 'bar') {
    return (
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="regiao" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              tickFormatter={formatNumber}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="total_uh" 
              fill="#2196F3"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  // Mixed view with table and charts
  return (
    <div className="space-y-8">
      {/* Regional Summary Table - Make it prominent */}
      <div className="bg-blue-50 rounded-lg shadow-lg border-2 border-blue-200 p-6">
        <h3 className="text-xl font-bold text-blue-900 mb-6 border-b border-blue-300 pb-4">
          📊 Resumo Financeiro por Região ({formattedData.length} regiões)
        </h3>
        <div className="overflow-x-auto bg-white rounded-lg p-4">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Região
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Projetos
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  UH Contratadas
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contratado (R$)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trabalho Social (R$)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contrapartida (R$)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Investimento (R$)
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {formattedData.map((row, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div 
                        className="w-3 h-3 rounded-full mr-2"
                        style={{ backgroundColor: COLORS[row.regiao as keyof typeof COLORS] || COLORS.default }}
                      ></div>
                      <span className="text-sm font-medium text-gray-900">{row.regiao}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatNumber(row.total_projetos)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatNumber(row.total_uh)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(row.total_contratado)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(row.trabalho_social || 0)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(row.contrapartida || 0)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(row.total_investimento)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Projects by Region - Pie Chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="text-lg font-medium text-gray-900 mb-4">
            📊 Projetos por Região
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={formattedData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="total_projetos"
                  nameKey="regiao"
                >
                  {formattedData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={COLORS[entry.regiao as keyof typeof COLORS] || COLORS.default} 
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [formatNumber(value as number), 'Projetos']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Investment by Region - Bar Chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="text-lg font-medium text-gray-900 mb-4">
            💰 Investimento por Região
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="regiao" 
                  tick={{ fontSize: 10 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  tick={{ fontSize: 10 }}
                  tickFormatter={formatCurrency}
                />
                <Tooltip 
                  formatter={(value) => [formatCurrency(value as number), 'Investimento']}
                />
                <Bar 
                  dataKey="total_investimento" 
                  radius={[4, 4, 0, 0]}
                >
                  {formattedData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={COLORS[entry.regiao as keyof typeof COLORS] || COLORS.default} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Execution Status by Region */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-6">
          🚧 Status de Execução por Região
        </h4>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={formattedData} 
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="regiao" 
                tick={{ fontSize: 11 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                tick={{ fontSize: 11 }}
                tickFormatter={formatNumber}
                label={{ value: 'Unidades Habitacionais', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => {
                  const labels: Record<string, string> = {
                    'concluidas': 'Concluídas',
                    'em_execucao': 'Em Execução', 
                    'nao_iniciadas': 'Não Iniciadas'
                  }
                  return [formatNumber(value as number), labels[name as string] || name]
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                formatter={(value) => {
                  const labels: Record<string, string> = {
                    'concluidas': '✅ Concluídas',
                    'em_execucao': '🏗️ Em Execução', 
                    'nao_iniciadas': '⏳ Não Iniciadas'
                  }
                  return labels[value] || value
                }}
              />
              <Bar 
                dataKey="concluidas" 
                stackId="execution"
                fill="#4CAF50"
                name="concluidas"
                radius={[0, 0, 0, 0]}
              />
              <Bar 
                dataKey="em_execucao" 
                stackId="execution"
                fill="#FF9800"
                name="em_execucao"
                radius={[0, 0, 0, 0]}
              />
              <Bar 
                dataKey="nao_iniciadas" 
                stackId="execution"
                fill="#757575"
                name="nao_iniciadas"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default RegionalChart