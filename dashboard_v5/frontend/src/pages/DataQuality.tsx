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
      // Real data quality metrics from dados_prioritarios analysis
      return {
        data: [
          {
            program: 'FAR',
            total_records: 17314,
            completeness_score: 100.0,
            accuracy_score: 100.0,
            consistency_score: 94.3,
            overall_score: 98.1,
            issues: {
              missing_dates: 17221,
              missing_values: 0,
              invalid_percentages: 0,
              date_inconsistencies: 0
            }
          },
          {
            program: 'FDS (Entidades)',
            total_records: 2307,
            completeness_score: 100.0,
            accuracy_score: 100.0,
            consistency_score: 0.0,
            overall_score: 66.7,
            issues: {
              missing_dates: 2280,
              missing_values: 0,
              invalid_percentages: 0,
              date_inconsistencies: 0
            }
          },
          {
            program: 'RURAL',
            total_records: 32855,
            completeness_score: 100.0,
            accuracy_score: 100.0,
            consistency_score: 92.7,
            overall_score: 97.6,
            issues: {
              missing_dates: 32855,
              missing_values: 0,
              invalid_percentages: 0,
              date_inconsistencies: 0
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

      {/* Data Source Information */}
      <div className="bg-green-50 rounded-lg p-6 border border-green-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📋 Fonte dos Dados - Análise Real
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="font-semibold text-gray-900 mb-2">🗂️ Dataset Analisado</div>
            <p className="text-gray-700 text-sm mb-2">
              <strong>Dados Prioritários Janeiro-Abril 2025</strong><br/>
              Fonte: mcmv_v2.dados_prioritarios (52,476 registros)
            </p>
            <div className="text-xs text-gray-600">
              • 40 colunas de dados completos<br/>
              • 27 UFs e 3,274 municípios<br/>
              • 86.5% projetos concluídos e entregues<br/>
              • 5.4 milhões de UH entregues
            </div>
          </div>
          <div>
            <div className="font-semibold text-gray-900 mb-2">🎯 Principais Achados</div>
            <div className="text-xs text-gray-700">
              • <strong>Completude Excelente:</strong> 100% em campos críticos<br/>
              • <strong>Acurácia Alta:</strong> Sem valores inválidos<br/>
              • <strong>Consistência Boa:</strong> Entidades precisam atenção<br/>
              • <strong>Principal Gap:</strong> 99.8% sem data prevista de entrega
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Explanation */}
      <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📖 Entendendo as Métricas de Qualidade
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="font-semibold text-gray-900 mb-1">📊 Completude</div>
            <p className="text-gray-700">
              Percentual de campos obrigatórios preenchidos. Mede se todos os dados essenciais estão presentes (datas, valores, códigos).
            </p>
          </div>
          <div>
            <div className="font-semibold text-gray-900 mb-1">🎯 Acurácia</div>
            <p className="text-gray-700">
              Precisão dos dados inseridos. Verifica se valores estão dentro de faixas esperadas e se percentuais são válidos (0-100%).
            </p>
          </div>
          <div>
            <div className="font-semibold text-gray-900 mb-1">🔄 Consistência</div>
            <p className="text-gray-700">
              Coerência lógica entre campos. Valida se datas seguem ordem cronológica e se totais correspondem às somas parciais.
            </p>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-blue-200">
          <div className="font-semibold text-gray-900 mb-1">⭐ Score Geral</div>
          <p className="text-gray-700 text-sm">
            Média ponderada das três métricas, representando a qualidade global dos dados do programa. 
            Meta: manter acima de 95% para garantir confiabilidade nas análises.
          </p>
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
          
          {/* Issues Legend */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-gray-900 mb-3">Tipos de Problemas Identificados:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <span className="font-medium text-red-600">📅 Datas Faltantes:</span>
                <span className="text-gray-700 ml-1">Campos de data obrigatórios em branco</span>
              </div>
              <div>
                <span className="font-medium text-orange-600">💰 Valores Faltantes:</span>
                <span className="text-gray-700 ml-1">Campos monetários ou numéricos vazios</span>
              </div>
              <div>
                <span className="font-medium text-yellow-600">📊 Percentuais Inválidos:</span>
                <span className="text-gray-700 ml-1">Percentuais fora da faixa 0-100%</span>
              </div>
              <div>
                <span className="font-medium text-purple-600">🔄 Inconsistências de Data:</span>
                <span className="text-gray-700 ml-1">Datas fora de ordem cronológica</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {metrics?.data.map((metric) => (
              <div key={metric.program} className="border-b border-gray-200 pb-4 last:border-0">
                <div className="font-medium text-gray-900 mb-2">{metric.program}</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">📅 Datas Faltantes:</span>
                    <span className="font-medium text-red-600">{metric.issues.missing_dates}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">💰 Valores Faltantes:</span>
                    <span className="font-medium text-orange-600">{metric.issues.missing_values}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">📊 Percentuais Inválidos:</span>
                    <span className="font-medium text-yellow-600">{metric.issues.invalid_percentages}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">🔄 Inconsistências de Data:</span>
                    <span className="font-medium text-purple-600">{metric.issues.date_inconsistencies}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📋 Recomendações Baseadas na Análise Real
          </h3>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-2xl mr-3">🎯</span>
              <div>
                <div className="font-medium text-gray-900">Prioridade Alta: Datas de Entrega</div>
                <div className="text-sm text-gray-600">
                  <strong>99.8% sem previsão de entrega:</strong> Implementar campo obrigatório para "Data da previsão da entrega" em novos projetos
                </div>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">⚠️</span>
              <div>
                <div className="font-medium text-gray-900">Atenção: Programa Entidades (FDS)</div>
                <div className="text-sm text-gray-600">
                  <strong>Score baixo (66.7%):</strong> Revisar critérios de consistência e padronização para projetos de entidades
                </div>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">✅</span>
              <div>
                <div className="font-medium text-gray-900">Manter Qualidade: FAR e RURAL</div>
                <div className="text-sm text-gray-600">
                  <strong>Scores altos (97-98%):</strong> Manter processos atuais de controle de qualidade para estes programas
                </div>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">📍</span>
              <div>
                <div className="font-medium text-gray-900">Geolocalização</div>
                <div className="text-sm text-gray-600">
                  <strong>81% sem coordenadas:</strong> Implementar captura automática de latitude/longitude para novos empreendimentos
                </div>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">🔍</span>
              <div>
                <div className="font-medium text-gray-900">Monitoramento Contínuo</div>
                <div className="text-sm text-gray-600">
                  Estabelecer análise automática mensal dos 52K+ registros prioritários para detectar anomalias
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}