/**
 * Comprehensive Data Quality Monitoring Dashboard
 * Real-time monitoring of data quality metrics
 */

import { useState, useEffect } from 'react'
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Activity,
  Database,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download
} from 'lucide-react'

interface QualityMetric {
  metric_name: string
  metric_value: number
  status: 'PASS' | 'WARNING' | 'FAIL'
  details: string
}

interface QualityAlert {
  alert_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  alert_message: string
  metric_value: number
}

interface QualitySummary {
  passed: number
  warnings: number
  failed: number
  total_checks: number
  pass_rate: number
  overall_status: string
  evaluated_at: string
}

export default function DataQualityDashboard() {
  const [metrics, setMetrics] = useState<QualityMetric[]>([])
  const [alerts, setAlerts] = useState<QualityAlert[]>([])
  const [summary, setSummary] = useState<QualitySummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [autoRefresh, setAutoRefresh] = useState(false)

  useEffect(() => {
    fetchQualityData()
    
    if (autoRefresh) {
      const interval = setInterval(fetchQualityData, 60000) // Refresh every minute
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const fetchQualityData = async () => {
    try {
      setLoading(true)
      
      // Fetch quality metrics
      const metricsResponse = await fetch('/api/v5/quality/metrics')
      const metricsData = await metricsResponse.json()
      setMetrics(metricsData.metrics || [])
      
      // Fetch alerts
      const alertsResponse = await fetch('/api/v5/quality/alerts')
      const alertsData = await alertsResponse.json()
      setAlerts(alertsData.alerts || [])
      
      // Fetch summary
      const summaryResponse = await fetch('/api/v5/quality/summary')
      const summaryData = await summaryResponse.json()
      setSummary(summaryData)
      
      setLastRefresh(new Date())
    } catch (error) {
      console.error('Failed to fetch quality data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PASS':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'WARNING':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'FAIL':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PASS':
        return 'bg-green-50 text-green-800 border-green-200'
      case 'WARNING':
        return 'bg-yellow-50 text-yellow-800 border-yellow-200'
      case 'FAIL':
        return 'bg-red-50 text-red-800 border-red-200'
      default:
        return 'bg-gray-50 text-gray-800 border-gray-200'
    }
  }

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'LOW':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const handleExport = async () => {
    try {
      const response = await fetch('/api/v5/quality/export')
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `quality_report_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export report:', error)
    }
  }

  if (loading && metrics.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Activity className="w-8 h-8 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Monitor de Qualidade de Dados
              </h2>
              <p className="text-sm text-gray-500">
                Última atualização: {lastRefresh.toLocaleString('pt-BR')}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
                autoRefresh 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
              <span>{autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}</span>
            </button>
            
            <button
              onClick={fetchQualityData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Atualizar</span>
            </button>
            
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Exportar</span>
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Taxa de Aprovação</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary.pass_rate.toFixed(1)}%
                  </p>
                </div>
                {summary.pass_rate >= 90 ? (
                  <TrendingUp className="w-8 h-8 text-green-500" />
                ) : (
                  <TrendingDown className="w-8 h-8 text-red-500" />
                )}
              </div>
            </div>
            
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-600">Aprovados</p>
                  <p className="text-2xl font-bold text-green-900">{summary.passed}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-yellow-600">Avisos</p>
                  <p className="text-2xl font-bold text-yellow-900">{summary.warnings}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
            
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-600">Falhas</p>
                  <p className="text-2xl font-bold text-red-900">{summary.failed}</p>
                </div>
                <XCircle className="w-8 h-8 text-red-500" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Alertas Ativos
          </h3>
          <div className="space-y-3">
            {alerts.map((alert, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 ${getAlertColor(alert.alert_level)}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-medium text-sm uppercase">
                      {alert.alert_level}
                    </span>
                    <p className="mt-1">{alert.alert_message}</p>
                  </div>
                  <span className="text-2xl font-bold">
                    {alert.metric_value.toLocaleString('pt-BR')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quality Metrics */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Métricas de Qualidade
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200">
          {metrics.map((metric, index) => (
            <div key={index} className="p-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(metric.status)}
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {metric.metric_name}
                    </h4>
                    <p className="text-sm text-gray-500">{metric.details}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <span className="text-lg font-semibold text-gray-700">
                    {metric.metric_value.toLocaleString('pt-BR')}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(metric.status)}`}>
                    {metric.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Overall Status */}
      {summary && (
        <div className={`rounded-lg p-6 text-center ${
          summary.overall_status === 'EXCELLENT' ? 'bg-green-100' :
          summary.overall_status === 'GOOD' ? 'bg-blue-100' :
          summary.overall_status === 'NEEDS ATTENTION' ? 'bg-yellow-100' :
          'bg-red-100'
        }`}>
          <Database className="w-12 h-12 mx-auto mb-3 text-gray-700" />
          <h3 className="text-xl font-bold text-gray-900">
            Status Geral: {summary.overall_status}
          </h3>
          <p className="text-gray-700 mt-2">
            {summary.total_checks} verificações realizadas
          </p>
        </div>
      )}
    </div>
  )
}