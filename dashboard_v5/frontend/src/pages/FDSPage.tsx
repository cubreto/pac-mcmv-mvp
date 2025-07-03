/**
 * MCMV Dashboard v5 - FDS Program Analysis Page
 * Deep dive into FDS program with detailed KPIs, charts, and financial breakdown
 */

import { useKPIs } from '../api/hooks'
import { KPISkeleton } from '../components/LoadingSpinner'
import { useGlobalFilters } from '../contexts/FilterContext'
import { 
  FDSRegionChart,
  FDSStatusChart,
  FDSTimelineChart,
  FDSFinancialTable 
} from '../components/charts/FDSCharts'

export default function FDSPage() {
  const { filters } = useGlobalFilters()

  // Get FDS-specific KPI data with global filters applied
  const { data: kpis, isLoading: kpisLoading, error: kpisError } = useKPIs({
    programa: 'FDS',
    regiao: filters.region,
    state: filters.state,
    municipality: filters.municipality,
    status: filters.status
  })

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          🏘️ FDS - Análise Detalhada
        </h1>
        <p className="text-purple-100">
          Fundo de Desenvolvimento Social - Programa para grupos organizados e cooperativas habitacionais
        </p>
        <div className="mt-4 flex items-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-purple-400 rounded-full mr-2"></div>
            <span>Programa FDS</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
            <span>Dados em Tempo Real</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-8">
        {/* KPI Cards */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            🏘️ Indicadores FDS
          </h2>
          
          {kpisLoading ? (
            <KPISkeleton />
          ) : kpisError ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">Erro ao carregar KPIs: {kpisError.message}</p>
            </div>
          ) : kpis ? (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <KPICard
                title="Total Projetos"
                value={kpis.total_projetos.toLocaleString('pt-BR')}
                subtitle="Projetos FDS"
                color="purple"
              />
              <KPICard
                title="UH Contratadas"
                value={kpis.total_uh_contratadas.toLocaleString('pt-BR')}
                subtitle="Unidades Habitacionais"
                color="green"
              />
              <KPICard
                title="Valor Contratado"
                value={`R$ ${(kpis.total_contratado / 1e9).toFixed(1)}B`}
                subtitle="Valor contratado"
                color="blue"
              />
              <KPICard
                title="Valor Investido"
                value={`R$ ${(kpis.total_investimento / 1e9).toFixed(1)}B`}
                subtitle="Total investido"
                color="orange"
              />
              <KPICard
                title="Investimento/UH"
                value={`R$ ${kpis.investimento_medio_por_uh.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`}
                subtitle="Média por unidade"
                color="teal"
              />
            </div>
          ) : null}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* UH por Região e Situação */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              📊 UH por Região e Situação
            </h3>
            {kpisLoading ? (
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <p className="text-gray-500">Carregando...</p>
              </div>
            ) : (
              <FDSRegionChart filters={filters} />
            )}
          </div>

          {/* UH por Situação */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              📊 UH por Situação
            </h3>
            {kpisLoading ? (
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <p className="text-gray-500">Carregando...</p>
              </div>
            ) : (
              <FDSStatusChart filters={filters} />
            )}
          </div>
        </div>

        {/* Timeline Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📈 Timeline - Previsão de Entrega
          </h3>
          {kpisLoading ? (
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
              <p className="text-gray-500">Carregando...</p>
            </div>
          ) : (
            <FDSTimelineChart filters={filters} />
          )}
        </div>

        {/* Financial Table */}
        <FDSFinancialTable filters={filters} />
      </div>
    </div>
  )
}

interface KPICardProps {
  title: string
  value: string
  subtitle: string
  color: 'blue' | 'green' | 'purple' | 'orange' | 'teal'
}

function KPICard({ title, value, subtitle, color }: KPICardProps) {
  const colorClasses = {
    blue: 'bg-blue-500 text-blue-600 bg-blue-50',
    green: 'bg-green-500 text-green-600 bg-green-50',
    purple: 'bg-purple-500 text-purple-600 bg-purple-50',
    orange: 'bg-orange-500 text-orange-600 bg-orange-50',
    teal: 'bg-teal-500 text-teal-600 bg-teal-50',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 border-l-4 border-l-purple-500 hover:shadow-md transition-shadow">
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full ${colorClasses[color].split(' ')[0]} mr-3`}></div>
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-600">{title}</div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{subtitle}</div>
        </div>
      </div>
    </div>
  )
}