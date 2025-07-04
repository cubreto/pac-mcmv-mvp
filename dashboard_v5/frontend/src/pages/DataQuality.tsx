/**
 * MCMV Dashboard v5 - Data Quality Page
 * Data quality metrics and validation reports
 */

import { useQuery } from '@tanstack/react-query'
import { LoadingSpinner } from '../components/LoadingSpinner'

interface DataQualityMetrics {
  program: string
  total_records: number
  completeness_score: number
  accuracy_score: number
  consistency_score: number
  overall_score: number
  issues: {
    missing_dates: number
    missing_values: number
    invalid_percentages: number
    date_inconsistencies: number
  }
}

export default function DataQuality() {
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['data-quality'],
    queryFn: async () => {
      // Simulated data until API endpoint is ready
      return {
        data: [
          {
            program: 'FAR',
            total_records: 12450,
            completeness_score: 92.5,
            accuracy_score: 88.3,
            consistency_score: 95.2,
            overall_score: 91.7,
            issues: {
              missing_dates: 234,
              missing_values: 567,
              invalid_percentages: 89,
              date_inconsistencies: 45
            }
          },
          {
            program: 'FDS',
            total_records: 8932,
            completeness_score: 89.8,
            accuracy_score: 91.2,
            consistency_score: 93.5,
            overall_score: 91.5,
            issues: {
              missing_dates: 178,
              missing_values: 423,
              invalid_percentages: 67,
              date_inconsistencies: 32
            }
          },
          {
            program: 'RURAL',
            total_records: 5678,
            completeness_score: 94.2,
            accuracy_score: 90.5,
            consistency_score: 96.8,
            overall_score: 93.8,
            issues: {
              missing_dates: 98,
              missing_values: 234,
              invalid_percentages: 23,
              date_inconsistencies: 12
            }
          }
        ] as DataQualityMetrics[]
      }
    },
    staleTime: 60 * 60 * 1000, // 1 hour cache
  })

  if (isLoading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">Erro ao carregar métricas de qualidade</p>
      </div>
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 95) return 'text-green-600 bg-green-50'
    if (score >= 85) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 95) return '✅'
    if (score >= 85) return '⚠️'
    return '❌'
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          📈 Qualidade dos Dados
        </h1>
        <p className="text-indigo-100">
          Monitoramento contínuo da qualidade e integridade dos dados MCMV
        </p>
        <div className="mt-4 flex items-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
            <span>Alta Qualidade (&gt;95%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-400 rounded-full mr-2"></div>
            <span>Atenção (85-95%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-400 rounded-full mr-2"></div>
            <span>Crítico (&lt;85%)</span>
          </div>
        </div>
      </div>

      {/* Overall Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-indigo-500">
          <div className="text-sm font-medium text-gray-600">Total de Registros</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {metrics?.data.reduce((sum, m) => sum + m.total_records, 0).toLocaleString('pt-BR')}
          </div>
          <div className="text-sm text-gray-500">Across all programs</div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="text-sm font-medium text-gray-600">Qualidade Média</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {((metrics?.data?.reduce((sum, m) => sum + m.overall_score, 0) || 0) / (metrics?.data?.length || 1)).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Overall score</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <div className="text-sm font-medium text-gray-600">Problemas Identificados</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {metrics?.data.reduce((sum, m) => 
              sum + m.issues.missing_dates + m.issues.missing_values + 
              m.issues.invalid_percentages + m.issues.date_inconsistencies, 0
            ).toLocaleString('pt-BR')}
          </div>
          <div className="text-sm text-gray-500">Total issues</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="text-sm font-medium text-gray-600">Última Atualização</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
          </div>
          <div className="text-sm text-gray-500">{new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
      </div>

      {/* Program Quality Metrics */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            📊 Métricas de Qualidade por Programa
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Programa
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completude
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acurácia
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Consistência
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score Geral
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Registros
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metrics?.data.map((metric) => (
                <tr key={metric.program} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{metric.program}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(metric.completeness_score)}`}>
                      {getScoreIcon(metric.completeness_score)} {metric.completeness_score.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(metric.accuracy_score)}`}>
                      {getScoreIcon(metric.accuracy_score)} {metric.accuracy_score.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(metric.consistency_score)}`}>
                      {getScoreIcon(metric.consistency_score)} {metric.consistency_score.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ${getScoreColor(metric.overall_score)}`}>
                      {metric.overall_score.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {metric.total_records.toLocaleString('pt-BR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Issues Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🔍 Problemas por Tipo
          </h3>
          <div className="space-y-4">
            {metrics?.data.map((metric) => (
              <div key={metric.program} className="border-b border-gray-200 pb-4 last:border-0">
                <div className="font-medium text-gray-900 mb-2">{metric.program}</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Datas Faltantes:</span>
                    <span className="font-medium">{metric.issues.missing_dates}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Valores Faltantes:</span>
                    <span className="font-medium">{metric.issues.missing_values}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Percentuais Inválidos:</span>
                    <span className="font-medium">{metric.issues.invalid_percentages}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Inconsistências de Data:</span>
                    <span className="font-medium">{metric.issues.date_inconsistencies}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📋 Recomendações
          </h3>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-2xl mr-3">1️⃣</span>
              <div>
                <div className="font-medium text-gray-900">Validação de Datas</div>
                <div className="text-sm text-gray-600">Implementar validação automática para datas de contratação e início de obra</div>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">2️⃣</span>
              <div>
                <div className="font-medium text-gray-900">Campos Obrigatórios</div>
                <div className="text-sm text-gray-600">Definir campos obrigatórios no sistema de entrada de dados</div>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">3️⃣</span>
              <div>
                <div className="font-medium text-gray-900">Revisão Periódica</div>
                <div className="text-sm text-gray-600">Estabelecer processo de revisão mensal dos dados críticos</div>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">4️⃣</span>
              <div>
                <div className="font-medium text-gray-900">Treinamento</div>
                <div className="text-sm text-gray-600">Capacitar equipes responsáveis pela entrada de dados</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}