/**
 * MCMV Dashboard v5 - Main Dashboard Page
 * Executive summary with KPIs and tabbed analysis
 * Updated: 2025-07-02 05:50 - Added Delivery Forecast
 */

import { useState } from 'react'
import { useKPIs, useRegionalSummary, useDeliveryForecast, useProgramSummary } from '../api/hooks'
import { KPISkeleton, ChartSkeleton } from '../components/LoadingSpinner'
import RegionalChart from '../components/charts/RegionalChart'
import ProgramChart from '../components/charts/ProgramChart'
import DeliveryForecastChart from '../components/charts/DeliveryForecastChart'
import { useGlobalFilters } from '../contexts/FilterContext'
import { formatCurrencyDashboard } from '../utils/formatters'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('regiao')
  const { filters } = useGlobalFilters()

  // API calls with filter support
  const { data: kpis, isLoading: kpisLoading, error: kpisError } = useKPIs({
    programa: filters.programa,
    regiao: filters.region,
    state: filters.state,
    municipality: filters.municipality
  })
  
  const { data: regional, isLoading: regionalLoading, error: regionalError } = useRegionalSummary({
    programa: filters.programa,
    regiao: filters.region,
    state: filters.state,
    municipality: filters.municipality
  })
  const { data: programs, isLoading: programsLoading, error: programsError } = useProgramSummary({
    regiao: filters.region,
    state: filters.state,
    municipality: filters.municipality,
    programa: filters.programa
  })
  const { data: deliveryForecast, isLoading: forecastLoading, error: forecastError } = useDeliveryForecast({
    programa: filters.programa,
    regiao: filters.region,
    state: filters.state,
    municipality: filters.municipality
  })

  const tabs = [
    { id: 'regiao', label: 'Por Região' },
    { id: 'programa', label: 'Por Programa' },
    { id: 'previsao', label: 'Previsão de Entregas' },
  ]

  return (
    <div className="space-y-8">


      {/* KPI Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Indicadores Principais
          </h2>
          
          <div className="flex items-center space-x-4">
            {kpis?.data_atualizacao && (
              <span className="text-sm text-gray-500">
                Posição: {new Date(kpis.data_atualizacao).toLocaleDateString('pt-BR')}
              </span>
            )}
            
            {Object.keys(filters).length > 0 && (
              <div className="flex items-center space-x-2 text-sm">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-blue-600 font-medium">
                  {Object.keys(filters).length} filtro(s) aplicado(s)
                </span>
              </div>
            )}
          </div>
        </div>
        
        {kpisLoading ? (
          <KPISkeleton />
        ) : kpisError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Erro ao carregar KPIs: {kpisError.message}</p>
          </div>
        ) : kpis ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              title="Total Projetos"
              value={kpis.total_projetos.toLocaleString('pt-BR')}
              subtitle="Projetos MCMV"
              color="blue"
            />
            <KPICard
              title="Total UH"
              value={kpis.total_uh_contratadas.toLocaleString('pt-BR')}
              subtitle="Unidades Habitacionais"
              color="green"
            />
            <KPICard
              title="Investimento Total"
              value={formatCurrencyDashboard(kpis.total_investimento)}
              subtitle="Valor investido"
              color="purple"
            />
            <KPICard
              title="Em Execução"
              value={kpis.uh_em_execucao.toLocaleString('pt-BR')}
              subtitle="UH em andamento"
              color="teal"
            />
          </div>
        ) : null}
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm transition-colors duration-200 flex items-center`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'regiao' && (
            <div>
              {regionalLoading ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ChartSkeleton />
                  <ChartSkeleton />
                </div>
              ) : regionalError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">Erro ao carregar dados regionais: {regionalError.message}</p>
                </div>
              ) : regional ? (
                <RegionalChart data={regional.data} type="mixed" />
              ) : null}
            </div>
          )}

          {activeTab === 'programa' && (
            <div>
              {programsLoading ? (
                <div className="space-y-6">
                  <ChartSkeleton />
                  <ChartSkeleton />
                </div>
              ) : programsError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">Erro ao carregar dados dos programas: {programsError.message}</p>
                </div>
              ) : programs ? (
                <div className="space-y-8">
                  {/* Program Overview */}
                  <ProgramChart 
                    data={programs.data}
                    type="overview"
                  />
                  
                  {/* Execution Status */}
                  <div className="mt-8">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Status de Execução
                    </h3>
                    <ProgramChart 
                      data={programs.data}
                      type="execution"
                    />
                  </div>
                </div>
              ) : null}
            </div>
          )}

          {activeTab === 'previsao' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Previsão de Conclusão de Obras por Programa
              </h2>
              
              {forecastLoading ? (
                <div className="space-y-6">
                  <ChartSkeleton />
                  <ChartSkeleton />
                </div>
              ) : forecastError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">Erro ao carregar previsão de entregas: {forecastError.message}</p>
                </div>
              ) : deliveryForecast ? (
                <div className="space-y-8">
                  {/* Summary Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white rounded-lg p-4 border-l-4 border-blue-500 shadow-sm">
                      <p className="text-sm text-gray-600">Meses com Entregas</p>
                      <p className="text-2xl font-bold text-gray-900">{deliveryForecast.summary.total_months}</p>
                    </div>
                    <div className="bg-white rounded-lg p-4 border-l-4 border-green-500 shadow-sm">
                      <p className="text-sm text-gray-600">Total UH - Conclusão de Obra</p>
                      <p className="text-2xl font-bold text-gray-900">{deliveryForecast.summary.total_uh_forecast.toLocaleString('pt-BR')}</p>
                    </div>
                    <div className="bg-white rounded-lg p-4 border-l-4 border-orange-500 shadow-sm">
                      <p className="text-sm text-gray-600">Pico de Entregas</p>
                      <p className="text-2xl font-bold text-gray-900">{deliveryForecast.summary.peak_month}</p>
                    </div>
                  </div>

                  {/* Timeline Chart */}
                  <DeliveryForecastChart 
                    data={deliveryForecast.data}
                    type="timeline"
                  />
                  
                  {/* Cumulative Chart */}
                  <div className="mt-8">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Entregas Acumuladas
                    </h3>
                    <DeliveryForecastChart 
                      data={deliveryForecast.data}
                      type="cumulative"
                    />
                  </div>
                </div>
              ) : null}
            </div>
          )}

        </div>
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
    <div className="bg-white rounded-lg shadow p-6 border-l-4 border-l-gray-200 hover:shadow-md transition-shadow">
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
}/* cache buster Wed Jul  2 05:35:28 UTC 2025 */
