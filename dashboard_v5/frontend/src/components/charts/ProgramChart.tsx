/**
 * MCMV Dashboard v5 - Program Analysis Chart
 * Interactive program breakdown with animated visualizations
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Line, Area, AreaChart } from 'recharts'

interface ProgramData {
  programa?: string
  regiao?: string
  total_projetos: number
  total_uh: number
  total_contratado?: number
  trabalho_social?: number
  contrapartida?: number
  total_investimento: number
  percentual_execucao_medio?: number
  em_execucao?: number
  nao_iniciadas?: number
  concluidas?: number
}

interface ProgramChartProps {
  data: ProgramData[]
  type: 'overview' | 'execution' | 'investment'
}

const PROGRAM_COLORS = {
  'FAR': '#2196F3',  // Blue - Fundo de Arrendamento Residencial
  'FDS': '#4CAF50',  // Green - Fundo de Desenvolvimento Social  
  'RURAL': '#FF9800', // Orange - Programa Nacional de Habitação Rural
  'default': '#9E9E9E'
}

const PROGRAM_ICONS = {
  'FAR': '🏗️',
  'FDS': '🏘️', 
  'RURAL': '🌾'
}

const formatCurrency = (value: number) => {
  if (value >= 1e9) return `R$ ${(value / 1e9).toFixed(1)}bi`
  if (value >= 1e6) return `R$ ${(value / 1e6).toFixed(1)}M`
  return `R$ ${value.toLocaleString('pt-BR')}`
}

const formatNumber = (value: number) => value.toLocaleString('pt-BR')

export function ProgramChart({ data, type }: ProgramChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Nenhum dado disponível
      </div>
    )
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-4 border rounded-lg shadow-lg max-w-xs">
          <div className="flex items-center mb-2">
            <span className="text-xl mr-2">{PROGRAM_ICONS[data.programa as keyof typeof PROGRAM_ICONS]}</span>
            <p className="font-semibold text-gray-900">{data.programa}</p>
          </div>
          <div className="space-y-1 text-sm">
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
        </div>
      )
    }
    return null
  }

  if (type === 'overview') {
    return (
      <div className="space-y-8">
        {/* Program Summary Table */}
        <div className="bg-blue-50 rounded-lg shadow-lg border-2 border-blue-200 p-6">
          <h3 className="text-xl font-bold text-blue-900 mb-6 border-b border-blue-300 pb-4">
            📊 Resumo Financeiro por Programa ({data.length} programas)
          </h3>
          <div className="overflow-x-auto bg-white rounded-lg p-4">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Programa
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
                {data.map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-xl mr-2">{PROGRAM_ICONS[(row.programa || row.regiao) as keyof typeof PROGRAM_ICONS]}</span>
                        <div 
                          className="w-3 h-3 rounded-full mr-2"
                          style={{ backgroundColor: PROGRAM_COLORS[(row.programa || row.regiao) as keyof typeof PROGRAM_COLORS] || PROGRAM_COLORS.default }}
                        ></div>
                        <span className="text-sm font-medium text-gray-900">{row.programa || row.regiao}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(row.total_projetos)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(row.total_uh)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency((row as any).total_contratado || 0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency((row as any).trabalho_social || 0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency((row as any).contrapartida || 0)}
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
        {/* Program Distribution - Enhanced Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            📊 Distribuição por Programa
            <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              Por UH
            </span>
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ programa, regiao, percent }) => `${programa || regiao} ${(percent * 100).toFixed(1)}%`}
                  outerRadius={80}
                  innerRadius={30}
                  paddingAngle={3}
                  dataKey="total_uh"
                >
                  {data.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={PROGRAM_COLORS[(entry.programa || entry.regiao) as keyof typeof PROGRAM_COLORS] || PROGRAM_COLORS.default}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Program Legend with Stats */}
          <div className="mt-4 space-y-2">
            {data.map((program) => (
              <div key={program.programa} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: PROGRAM_COLORS[program.programa as keyof typeof PROGRAM_COLORS] }}
                  ></div>
                  <span className="text-sm font-medium">{PROGRAM_ICONS[program.programa as keyof typeof PROGRAM_ICONS]} {program.programa}</span>
                </div>
                <span className="text-sm text-gray-600">{formatNumber(program.total_uh)} UH</span>
              </div>
            ))}
          </div>
        </div>

        {/* Investment Comparison - Enhanced Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            💰 Investimento por Programa
            <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
              Em Bilhões
            </span>
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis 
                  dataKey="programa" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${PROGRAM_ICONS[value as keyof typeof PROGRAM_ICONS]} ${value}`}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar 
                  dataKey="total_investimento" 
                  radius={[6, 6, 0, 0]}
                  strokeWidth={2}
                  stroke="#fff"
                >
                  {data.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={PROGRAM_COLORS[(entry.programa || entry.regiao) as keyof typeof PROGRAM_COLORS] || PROGRAM_COLORS.default}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      </div>
    )
  }

  if (type === 'execution') {
    // Transform data for execution status visualization
    const executionData = data.map(program => ({
      programa: program.programa || program.regiao,
      'Em Execução': program.em_execucao || 0,
      'Não Iniciadas': program.nao_iniciadas || 0,
      'Concluídas': program.concluidas || 0,
      total: program.total_uh
    }))

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          🚧 Status de Execução por Programa
          <span className="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
            Unidades Habitacionais
          </span>
        </h4>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={executionData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey="programa" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${PROGRAM_ICONS[value as keyof typeof PROGRAM_ICONS]} ${value}`}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={formatNumber}
              />
              <Tooltip 
                formatter={(value, name) => [formatNumber(value as number), name]}
                labelFormatter={(label) => `${PROGRAM_ICONS[label as keyof typeof PROGRAM_ICONS]} ${label}`}
              />
              <Bar dataKey="Concluídas" stackId="a" fill="#4CAF50" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Em Execução" stackId="a" fill="#FF9800" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Não Iniciadas" stackId="a" fill="#F44336" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Execution Summary Cards */}
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-700">
              {formatNumber(executionData.reduce((sum, p) => sum + p['Concluídas'], 0))}
            </div>
            <div className="text-sm text-green-600">Concluídas</div>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-orange-700">
              {formatNumber(executionData.reduce((sum, p) => sum + p['Em Execução'], 0))}
            </div>
            <div className="text-sm text-orange-600">Em Execução</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-700">
              {formatNumber(executionData.reduce((sum, p) => sum + p['Não Iniciadas'], 0))}
            </div>
            <div className="text-sm text-red-600">Não Iniciadas</div>
          </div>
        </div>
      </div>
    )
  }

  // Investment efficiency view
  const efficiencyData = data.map(program => ({
    programa: program.programa,
    investimento_por_uh: program.total_investimento / program.total_uh,
    execucao_percent: program.percentual_execucao_medio,
    total_uh: program.total_uh
  }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
        💡 Eficiência de Investimento
        <span className="ml-2 px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
          R$/UH vs % Execução
        </span>
      </h4>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={efficiencyData} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="programa" 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${PROGRAM_ICONS[value as keyof typeof PROGRAM_ICONS]} ${value}`}
            />
            <YAxis 
              yAxisId="left"
              tick={{ fontSize: 12 }}
              tickFormatter={formatCurrency}
            />
            <YAxis 
              yAxisId="right" 
              orientation="right"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'investimento_por_uh') return [formatCurrency(value as number), 'Investimento/UH']
                if (name === 'execucao_percent') return [`${(value as number).toFixed(1)}%`, '% Execução']
                return [value, name]
              }}
              labelFormatter={(label) => `${PROGRAM_ICONS[label as keyof typeof PROGRAM_ICONS]} ${label}`}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="investimento_por_uh"
              stroke="#9C27B0"
              fill="#9C27B0"
              fillOpacity={0.3}
              strokeWidth={3}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="execucao_percent"
              stroke="#FF5722"
              strokeWidth={3}
              dot={{ fill: '#FF5722', strokeWidth: 2, r: 6 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default ProgramChart