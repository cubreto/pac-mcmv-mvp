/**
 * ETL Quality Report Component
 * Shows forensic analysis of data quality issues found during ETL
 */

import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react'

interface ETLQualityReportProps {
  programa?: string
}

interface QualityIssue {
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  details: {
    affected_records?: number
    sample_apfs?: string[]
    [key: string]: any
  }
}

interface QualityReport {
  timestamp: string
  table: string
  total_issues: number
  quality_score: number
  issues: QualityIssue[]
  statistics: {
    total_records: number
    unique_projects: number
    snapshot_count: number
    date_range: {
      start: string
      end: string
    }
    coverage: {
      states: number
      municipalities: number
    }
  }
}

// Translation helpers
const translateIssueType = (type: string): string => {
  const translations: { [key: string]: string } = {
    'espacos_extras': 'Espaços extras',
    'espacos_duplos': 'Espaços duplos',
    'inconsistencia_temporal': 'Inconsistência temporal',
    'dados_mes_incorreto': 'Dados de mês incorreto',
    'registros_duplicados': 'Registros duplicados',
    'valor_numerico_invalido': 'Valor numérico inválido',
    'campo_obrigatorio_ausente': 'Campo obrigatório ausente',
    'periodo_data_invalido': 'Período de data inválido',
    'valores_atipicos': 'Valores atípicos'
  }
  return translations[type] || type
}

const translateDetailKey = (key: string): string => {
  const translations: { [key: string]: string } = {
    'estado': 'Estado',
    'municipio': 'Município',
    'tamanho': 'Tamanho',
    'tamanho_limpo': 'Tamanho limpo',
    'registros_afetados': 'Registros afetados',
    'mes': 'Mês',
    'data_atual': 'Data atual',
    'data_esperada': 'Data esperada',
    'data_movimento': 'Data movimento',
    'quantidade_registros': 'Quantidade de registros',
    'apfs_exemplo': 'APFs exemplo',
    'apfs_duplicados': 'APFs duplicados',
    'total_registros_duplicados': 'Total registros duplicados',
    'campo': 'Campo',
    'quantidade_invalida': 'Quantidade inválida',
    'quantidade_ausente': 'Quantidade ausente',
    'percentual_ausente': 'Percentual ausente',
    'quantidade': 'Quantidade',
    'data_minima': 'Data mínima',
    'data_maxima': 'Data máxima',
    'quantidade_atipica': 'Quantidade atípica',
    'valor_minimo': 'Valor mínimo',
    'valor_maximo': 'Valor máximo',
    'affected_records': 'Registros afetados'
  }
  return translations[key] || key
}

export default function ETLQualityReport({ programa }: ETLQualityReportProps) {
  const [report, setReport] = useState<QualityReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set())

  useEffect(() => {
    fetchQualityReport()
  }, [programa])

  const fetchQualityReport = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v5/etl-quality/analysis?table=dados_prioritarios')
      if (!response.ok) throw new Error('Failed to fetch quality report')
      const data = await response.json()
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load quality report')
    } finally {
      setLoading(false)
    }
  }

  const toggleIssue = (index: number) => {
    const newExpanded = new Set(expandedIssues)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedIssues(newExpanded)
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'medium':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'low':
        return <Info className="w-5 h-5 text-blue-500" />
      default:
        return <CheckCircle className="w-5 h-5 text-green-500" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'medium':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      case 'low':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const filteredIssues = report?.issues.filter(issue => 
    selectedSeverity === 'all' || issue.severity === selectedSeverity
  ) || []

  const severityCounts = report?.issues.reduce((acc, issue) => {
    acc[issue.severity] = (acc[issue.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>) || {}

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">
          <XCircle className="w-12 h-12 mx-auto mb-2" />
          <p>{error}</p>
        </div>
      </div>
    )
  }

  if (!report) return null

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Análise de Qualidade ETL
          </h3>
          <div className={`text-2xl font-bold ${getScoreColor(report.quality_score)}`}>
            {report.quality_score}%
          </div>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Última análise: {new Date(report.timestamp).toLocaleString('pt-BR')}
        </p>
      </div>

      {/* Statistics Summary */}
      <div className="p-6 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {report.statistics.total_records.toLocaleString('pt-BR')}
            </div>
            <div className="text-sm text-gray-500">Registros Totais</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {report.statistics.unique_projects.toLocaleString('pt-BR')}
            </div>
            <div className="text-sm text-gray-500">Projetos Únicos</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {report.statistics.snapshot_count}
            </div>
            <div className="text-sm text-gray-500">Snapshots</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-orange-600">
              {report.total_issues}
            </div>
            <div className="text-sm text-gray-500">Problemas Detectados</div>
          </div>
        </div>
      </div>

      {/* Severity Filter */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Filtrar por severidade:</span>
          <button
            onClick={() => setSelectedSeverity('all')}
            className={`px-3 py-1 rounded-full text-sm ${
              selectedSeverity === 'all' 
                ? 'bg-gray-800 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Todos ({report.total_issues})
          </button>
          {['critical', 'high', 'medium', 'low'].map(severity => (
            severityCounts[severity] > 0 && (
              <button
                key={severity}
                onClick={() => setSelectedSeverity(severity)}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedSeverity === severity 
                    ? 'bg-gray-800 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {severity === 'critical' ? 'Crítico' : severity === 'high' ? 'Alto' : severity === 'medium' ? 'Médio' : 'Baixo'} ({severityCounts[severity] || 0})
              </button>
            )
          ))}
        </div>
      </div>

      {/* Issues List */}
      <div className="divide-y divide-gray-200">
        {filteredIssues.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            Nenhum problema encontrado com a severidade selecionada
          </div>
        ) : (
          filteredIssues.map((issue, index) => (
            <div key={index} className="p-4 hover:bg-gray-50">
              <div 
                className="flex items-start cursor-pointer"
                onClick={() => toggleIssue(index)}
              >
                <div className="flex-shrink-0 mr-3">
                  {getSeverityIcon(issue.severity)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">
                      {issue.description}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(issue.severity)}`}>
                      {issue.severity === 'critical' ? 'crítico' : issue.severity === 'high' ? 'alto' : issue.severity === 'medium' ? 'médio' : 'baixo'}
                    </span>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    Tipo: {translateIssueType(issue.type)}
                    {issue.details.affected_records && (
                      <span className="ml-2">
                        • {issue.details.affected_records.toLocaleString('pt-BR')} registros afetados
                      </span>
                    )}
                  </div>
                  
                  {expandedIssues.has(index) && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <h5 className="text-xs font-medium text-gray-700 mb-2">Detalhes:</h5>
                      <div className="space-y-1 text-xs text-gray-600">
                        {Object.entries(issue.details).map(([key, value]) => (
                          <div key={key} className="flex">
                            <span className="font-medium mr-2">
                              {translateDetailKey(key)}:
                            </span>
                            <span className="text-gray-800">
                              {Array.isArray(value) 
                                ? value.slice(0, 3).join(', ') + (value.length > 3 ? '...' : '')
                                : typeof value === 'object'
                                ? JSON.stringify(value)
                                : String(value)
                              }
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Common Issues Examples */}
      <div className="p-6 bg-blue-50 border-t border-blue-100">
        <h4 className="text-sm font-medium text-blue-900 mb-2">
          Tipos de Problemas Detectados:
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Registros de meses anteriores em snapshots recentes</li>
          <li>• Municípios com espaços extras no início/fim</li>
          <li>• Municípios com espaços duplos (ex: "SÃO  PAULO")</li>
          <li>• Datas de movimento inconsistentes</li>
          <li>• APFs duplicados no mesmo período</li>
          <li>• Valores numéricos inválidos ou atípicos</li>
        </ul>
      </div>
    </div>
  )
}