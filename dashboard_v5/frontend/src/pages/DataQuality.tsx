/**
 * MCMV Dashboard v5 - Data Quality Page
 * Automated data quality monitoring with program-specific views
 */

import { useState } from 'react'
import { 
  AlertCircle, 
  CheckCircle, 
  XCircle, 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  FileWarning,
  Database
} from 'lucide-react'
import { 
  useDataQualityComprehensive, 
  useDataQualityProgram,
  useDataQualityDadosPrioritarios,
  useQualityTrends,
  useQualityAlerts
} from '../api/hooks'
import { apiClient } from '../api/client'
import { LoadingSpinner } from '../components/LoadingSpinner'
import QualityTrendChart from '../components/charts/QualityTrendChart'
import { formatCurrencyDashboard } from '../utils/formatters'
import ETLQualityReport from '../components/ETLQualityReport'
// import DataQualityDashboard from '../components/DataQualityDashboard'

// Translation function for alert names
const translateAlertName = (alertName: string): string => {
  const translations: { [key: string]: string } = {
    'Low Completeness Score': 'Pontuação de Completude Baixa',
    'High Missing Dates': 'Muitas Datas Ausentes',
    'High Missing Data': 'Muitos Dados Ausentes',
    'Low Accuracy Score': 'Pontuação de Precisão Baixa',
    'High Invalid Records': 'Muitos Registros Inválidos',
    'Low Consistency Score': 'Pontuação de Consistência Baixa',
    'High Data Errors': 'Muitos Erros de Dados',
    'Missing Contract Dates': 'Datas de Contrato Ausentes',
    'Missing Start Dates': 'Datas de Início Ausentes',
    'Missing End Dates': 'Datas de Fim Ausentes',
    'Invalid Progress Values': 'Valores de Progresso Inválidos',
    'Data Quality Alert': 'Alerta de Qualidade de Dados',
    'System Alert': 'Alerta do Sistema'
  }
  return translations[alertName] || alertName
}

// Tab component
interface TabProps {
  tabs: string[]
  activeTab: string
  onTabChange: (tab: string) => void
}

function Tabs({ tabs, activeTab, onTabChange }: TabProps) {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            className={`
              whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
              ${activeTab === tab
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            {tab}
          </button>
        ))}
      </nav>
    </div>
  )
}

// Quality Score Card Component
interface QualityScoreCardProps {
  title: string
  score: number
  icon: React.ReactNode
  trend?: number
}

function QualityScoreCard({ title, score, icon, trend }: QualityScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50'
    if (score >= 70) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <CheckCircle className="w-5 h-5 text-green-600" />
    if (score >= 70) return <AlertCircle className="w-5 h-5 text-yellow-600" />
    return <XCircle className="w-5 h-5 text-red-600" />
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {icon}
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        {getScoreIcon(score)}
      </div>
      
      <div className={`text-3xl font-bold rounded-lg p-4 text-center ${getScoreColor(score)}`}>
        {score.toFixed(1)}%
      </div>
      
      {trend !== undefined && (
        <div className="mt-4 flex items-center justify-center">
          {trend > 0 ? (
            <>
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-sm text-green-600">+{trend.toFixed(1)}%</span>
            </>
          ) : (
            <>
              <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
              <span className="text-sm text-red-600">{trend.toFixed(1)}%</span>
            </>
          )}
          <span className="text-sm text-gray-500 ml-1">vs mês anterior</span>
        </div>
      )}
    </div>
  )
}

// Issue Breakdown Component
interface IssueBreakdownProps {
  title: string
  issues: Array<{ label: string; count: number; percentage: number }>
  totalRecords: number
}

function IssueBreakdown({ title, issues, totalRecords }: IssueBreakdownProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="space-y-3">
        {issues.map((issue, index) => (
          <div key={index}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">{issue.label}</span>
              <span className="font-medium">
                {issue.count.toLocaleString('pt-BR')} ({issue.percentage.toFixed(1)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${issue.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Total de Registros</span>
          <span className="font-semibold">{totalRecords.toLocaleString('pt-BR')}</span>
        </div>
      </div>
    </div>
  )
}

// Overview Tab Component
function OverviewTab() {
  const { data, isLoading, error } = useDataQualityComprehensive()

  if (isLoading) return <LoadingSpinner />
  if (error) return <div className="text-red-600">Erro ao carregar dados de qualidade</div>
  if (!data) return null

  const { program_data, dados_prioritarios, overall_health } = data

  return (
    <div className="space-y-6">
      {/* Overall Health */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Saúde Geral dos Dados</h2>
            <p className="text-blue-100">
              Score médio de qualidade: {overall_health.average_score.toFixed(1)}%
            </p>
          </div>
          <div className={`text-4xl font-bold px-6 py-3 rounded-lg ${
            overall_health.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
          }`}>
            {overall_health.status === 'healthy' ? '✓ Saudável' : '⚠ Atenção'}
          </div>
        </div>
      </div>

      {/* Program Summary */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Qualidade por Programa</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {program_data.metrics.map((prog: any) => (
            <QualityScoreCard
              key={prog.programa}
              title={prog.programa}
              score={prog.overall_score}
              icon={<Database className="w-6 h-6 text-gray-600" />}
            />
          ))}
        </div>
      </div>

      {/* Dados Prioritários Summary */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Dados Prioritários - Resumo</h3>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total de Registros</p>
              <p className="text-2xl font-bold">
                {dados_prioritarios.summary.total_records?.toLocaleString('pt-BR') || '0'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">UHs Contratadas</p>
              <p className="text-2xl font-bold">
                {dados_prioritarios.summary.total_uh_contracted?.toLocaleString('pt-BR') || '0'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Execução Média</p>
              <p className="text-2xl font-bold">
                {dados_prioritarios.summary.avg_execution?.toFixed(1) || '0'}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Dados Faltantes</p>
              <p className="text-2xl font-bold text-red-600">
                {dados_prioritarios.summary.missing_delivery_dates?.toLocaleString('pt-BR') || '0'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Program Tab Component
function ProgramTab({ programa }: { programa: string }) {
  const { data, isLoading, error } = useDataQualityProgram(programa)

  if (isLoading) return <LoadingSpinner />
  if (error) return <div className="text-red-600">Erro ao carregar dados do programa</div>
  if (!data || !data.metrics) return null

  const metrics = data.metrics

  // Calculate percentages for issues
  const missingDataIssues = [
    { 
      label: 'Data de Contratação', 
      count: metrics.missing_contract_date,
      percentage: (metrics.missing_contract_date / metrics.total_records) * 100
    },
    { 
      label: 'Data de Início', 
      count: metrics.missing_start_date,
      percentage: (metrics.missing_start_date / metrics.total_records) * 100
    },
    { 
      label: 'Data de Conclusão', 
      count: metrics.missing_end_date,
      percentage: (metrics.missing_end_date / metrics.total_records) * 100
    },
    { 
      label: 'Nome do Empreendimento', 
      count: metrics.missing_name,
      percentage: (metrics.missing_name / metrics.total_records) * 100
    },
    { 
      label: 'Município', 
      count: metrics.missing_municipality,
      percentage: (metrics.missing_municipality / metrics.total_records) * 100
    },
  ]

  const dataQualityIssues = [
    { 
      label: 'Progresso Inválido', 
      count: metrics.invalid_progress,
      percentage: (metrics.invalid_progress / metrics.total_records) * 100
    },
    { 
      label: 'UH Inválidas', 
      count: metrics.invalid_uh,
      percentage: (metrics.invalid_uh / metrics.total_records) * 100
    },
    { 
      label: 'Investimento Inválido', 
      count: metrics.invalid_investment,
      percentage: (metrics.invalid_investment / metrics.total_records) * 100
    },
    { 
      label: 'Início antes da Contratação', 
      count: metrics.start_before_contract,
      percentage: (metrics.start_before_contract / metrics.total_records) * 100
    },
  ]

  return (
    <div className="space-y-6">
      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QualityScoreCard
          title="Completude"
          score={metrics.completeness_score}
          icon={<FileWarning className="w-6 h-6 text-blue-600" />}
        />
        <QualityScoreCard
          title="Precisão"
          score={metrics.accuracy_score}
          icon={<BarChart3 className="w-6 h-6 text-green-600" />}
        />
        <QualityScoreCard
          title="Consistência"
          score={metrics.consistency_score}
          icon={<CheckCircle className="w-6 h-6 text-purple-600" />}
        />
      </div>

      {/* Statistics Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Estatísticas do Programa</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Progresso Médio</p>
            <p className="text-2xl font-bold">{metrics.avg_progress?.toFixed(1) || '0'}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Investimento Total</p>
            <p className="text-2xl font-bold">
              {formatCurrencyDashboard(metrics.total_investment)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Período dos Dados</p>
            <p className="text-sm font-medium">
              {new Date(metrics.earliest_contract).toLocaleDateString('pt-BR')} - 
              {new Date(metrics.latest_contract).toLocaleDateString('pt-BR')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Última Atualização</p>
            <p className="text-sm font-medium">
              {new Date(metrics.latest_movement).toLocaleDateString('pt-BR')}
            </p>
          </div>
        </div>
      </div>

      {/* Issue Breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <IssueBreakdown
          title="Dados Faltantes"
          issues={missingDataIssues}
          totalRecords={metrics.total_records}
        />
        <IssueBreakdown
          title="Problemas de Qualidade"
          issues={dataQualityIssues}
          totalRecords={metrics.total_records}
        />
      </div>
    </div>
  )
}

// Dados Prioritários Tab Component
function DadosPrioritariosTab() {
  const { data, isLoading, error } = useDataQualityDadosPrioritarios()

  if (isLoading) return <LoadingSpinner />
  if (error) return <div className="text-red-600">Erro ao carregar dados prioritários</div>
  if (!data) return null

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Resumo Geral</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total de Registros</p>
            <p className="text-2xl font-bold">
              {data.summary.total_records?.toLocaleString('pt-BR')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Municípios</p>
            <p className="text-2xl font-bold">
              {data.summary.total_municipalities?.toLocaleString('pt-BR')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">UHs Contratadas</p>
            <p className="text-2xl font-bold">
              {data.summary.total_uh_contracted?.toLocaleString('pt-BR')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Valor Total</p>
            <p className="text-2xl font-bold">
              {formatCurrencyDashboard(data.summary.total_value_contracted)}
            </p>
          </div>
        </div>
      </div>

      {/* Quality by Modalidade */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Qualidade por Modalidade</h3>
        <div className="space-y-4">
          {data.by_modalidade.map((mod: any) => (
            <div key={mod.modalidade} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold">{mod.modalidade}</h4>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">
                    {mod.total_records.toLocaleString('pt-BR')} registros
                  </span>
                  <span className={`text-lg font-bold px-3 py-1 rounded ${
                    mod.overall_score >= 90 ? 'bg-green-100 text-green-800' :
                    mod.overall_score >= 70 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {mod.overall_score.toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Completude</p>
                  <p className="text-xl font-semibold">{mod.completeness_score.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Precisão</p>
                  <p className="text-xl font-semibold">{mod.accuracy_score.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Consistência</p>
                  <p className="text-xl font-semibold">{mod.consistency_score.toFixed(1)}%</p>
                </div>
              </div>

              {/* Key Issues */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm font-medium text-gray-700 mb-2">Principais Problemas:</p>
                <div className="flex flex-wrap gap-2">
                  {mod.missing_delivery_date > 0 && (
                    <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                      {mod.missing_delivery_date} sem data de entrega
                    </span>
                  )}
                  {mod.missing_coordinates > 0 && (
                    <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                      {mod.missing_coordinates} sem coordenadas
                    </span>
                  )}
                  {mod.invalid_progress > 0 && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                      {mod.invalid_progress} com progresso inválido
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Monitoring Tab Component
function MonitoringTab() {
  const [selectedProgram, setSelectedProgram] = useState<string>('')
  const [trendDays, setTrendDays] = useState(30)
  const [exportFormat, setExportFormat] = useState<'excel' | 'json'>('excel')
  const [isExporting, setIsExporting] = useState(false)

  const { data: trendsData, isLoading: trendsLoading } = useQualityTrends(
    selectedProgram || undefined, 
    trendDays
  )
  const { data: alertsData, isLoading: alertsLoading } = useQualityAlerts(true)

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const result = await apiClient.exportQualityReport(exportFormat, {
        programa: selectedProgram || undefined
      })
      
      if (exportFormat === 'json') {
        // Para JSON, criar um arquivo para download
        const jsonString = JSON.stringify(result, null, 2)
        const blob = new Blob([jsonString], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `quality_report_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        alert('Relatório JSON baixado com sucesso!')
      }
    } catch (error) {
      console.error('Export failed:', error)
      alert('Erro ao exportar relatório')
    } finally {
      setIsExporting(false)
    }
  }

  const handleCaptureSnapshot = async () => {
    try {
      const result = await apiClient.captureQualitySnapshot()
      alert(`Snapshot agendado: ${result.message}`)
    } catch (error) {
      console.error('Snapshot failed:', error)
      alert('Erro ao capturar snapshot')
    }
  }

  const handleCheckAlerts = async () => {
    try {
      const result = await apiClient.checkQualityAlerts()
      alert(`Alertas verificados: ${result.alerts_triggered} disparados de ${result.alerts_checked} configurados`)
    } catch (error) {
      console.error('Alert check failed:', error)
      alert('Erro ao verificar alertas')
    }
  }

  if (trendsLoading || alertsLoading) return <LoadingSpinner />

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Controles de Monitoramento</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Programa
            </label>
            <select
              value={selectedProgram}
              onChange={(e) => setSelectedProgram(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">Todos</option>
              <option value="FAR">FAR</option>
              <option value="FDS">FDS</option>
              <option value="RURAL">RURAL</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Período (dias)
            </label>
            <select
              value={trendDays}
              onChange={(e) => setTrendDays(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value={7}>7 dias</option>
              <option value={30}>30 dias</option>
              <option value={60}>60 dias</option>
              <option value={90}>90 dias</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Formato de Exportação
            </label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'excel' | 'json')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="excel">Excel</option>
              <option value="json">JSON</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isExporting ? 'Exportando...' : 'Exportar Relatório'}
            </button>
          </div>
        </div>
        
        <div className="mt-4 flex gap-4">
          <button
            onClick={handleCaptureSnapshot}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Capturar Snapshot
          </button>
          <button
            onClick={handleCheckAlerts}
            className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
          >
            Verificar Alertas
          </button>
        </div>
      </div>

      {/* Trends Chart */}
      {trendsData?.trends && trendsData.trends.length > 0 && (
        <QualityTrendChart data={trendsData.trends} />
      )}

      {/* Active Alerts */}
      {alertsData?.alerts && alertsData.alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Alertas Configurados</h3>
          
          <div className="space-y-3">
            {alertsData.alerts.map((alert: any, index: number) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{translateAlertName(alert.alert_name)}</h4>
                    <p className="text-sm text-gray-600">
                      {alert.target_program} - {alert.target_metric} {alert.comparison_operator} {alert.threshold_value}%
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      alert.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {alert.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                    {alert.recent_triggers > 0 && (
                      <p className="text-sm text-red-600 mt-1">
                        {alert.recent_triggers} disparos recentes
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-sm font-medium text-gray-600">Pontos de Dados</h4>
          <p className="text-2xl font-bold text-gray-900">
            {trendsData?.trends?.length || 0}
          </p>
          <p className="text-sm text-gray-500">Últimos {trendDays} dias</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-sm font-medium text-gray-600">Alertas Ativos</h4>
          <p className="text-2xl font-bold text-gray-900">
            {alertsData?.alerts?.filter((a: any) => a.is_active).length || 0}
          </p>
          <p className="text-sm text-gray-500">Monitorando qualidade</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-sm font-medium text-gray-600">Última Análise</h4>
          <p className="text-2xl font-bold text-gray-900">
            {new Date().toLocaleDateString('pt-BR')}
          </p>
          <p className="text-sm text-gray-500">Atualização diária</p>
        </div>
      </div>
    </div>
  )
}

// Main Data Quality Component
export default function DataQuality() {
  const [activeTab, setActiveTab] = useState('Visão Geral')
  
  const tabs = [
    'Visão Geral',
    'FAR',
    'FDS', 
    'RURAL',
    'Dados Prioritários',
    'Monitoramento',
    'ETL Quality'
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-700 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          📊 Qualidade dos Dados
        </h1>
        <p className="text-purple-100">
          Monitoramento automatizado da qualidade e integridade dos dados do programa MCMV
        </p>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'Visão Geral' && <OverviewTab />}
        {activeTab === 'FAR' && <ProgramTab programa="FAR" />}
        {activeTab === 'FDS' && <ProgramTab programa="FDS" />}
        {activeTab === 'RURAL' && <ProgramTab programa="RURAL" />}
        {activeTab === 'Dados Prioritários' && <DadosPrioritariosTab />}
        {activeTab === 'Monitoramento' && <MonitoringTab />}
        {activeTab === 'ETL Quality' && <ETLQualityReport />}
      </div>
    </div>
  )
}