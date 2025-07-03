/**
 * MCMV Dashboard v5 - Dados Prioritários Page
 * Historical data analysis with simplified table view
 */

import React, { useState } from 'react'
import { useDadosPrioritarios, useDadosPrioritariosFilters } from '../api/hooks'

interface DadosPrioritariosFilters {
  ano_contratacao?: number
  mes_movimento?: number
  ano_movimento?: number
}

export default function DadosPrioritariosPage() {
  const [filters, setFilters] = useState<DadosPrioritariosFilters>({})

  // Get dados prioritarios data with filters
  const { data, isLoading, error } = useDadosPrioritarios(filters)
  const { data: filterOptions, isLoading: filtersLoading } = useDadosPrioritariosFilters()

  const updateFilter = (key: keyof DadosPrioritariosFilters, value: number | undefined) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }))
  }

  const clearFilters = () => {
    setFilters({})
  }

  const hasActiveFilters = Object.keys(filters).length > 0

  // Month names for display
  const monthNames = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-600 to-gray-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          📋 Dados Prioritários - Análise Histórica
        </h1>
        <p className="text-gray-100">
          Dados históricos dos programas habitacionais com métricas de entrega e execução
        </p>
        <div className="mt-4 flex items-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-400 rounded-full mr-2"></div>
            <span>Dados Históricos</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
            <span>fl_dados_prioritarios = TRUE</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              🔍 Filtros Específicos
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Filtros para dados históricos prioritários
            </p>
          </div>
          
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-3 py-1.5 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
            >
              🗑️ Limpar Filtros
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Ano de Contratação */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📅 Ano de Contratação
            </label>
            <select
              value={filters.ano_contratacao || ''}
              onChange={(e) => updateFilter('ano_contratacao', e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              disabled={filtersLoading}
            >
              <option value="">Todos os Anos</option>
              {filterOptions?.anos_contratacao?.map((ano: number) => (
                <option key={ano} value={ano}>
                  {ano}
                </option>
              ))}
            </select>
          </div>

          {/* Ano de Movimento */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📆 Ano de Movimento
            </label>
            <select
              value={filters.ano_movimento || ''}
              onChange={(e) => updateFilter('ano_movimento', e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              disabled={filtersLoading}
            >
              <option value="">Todos os Anos</option>
              {filterOptions?.movimento_dates && Object.keys(filterOptions.movimento_dates).map((ano: string) => (
                <option key={ano} value={ano}>
                  {ano}
                </option>
              ))}
            </select>
          </div>

          {/* Mês de Movimento */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🗓️ Mês de Movimento
            </label>
            <select
              value={filters.mes_movimento || ''}
              onChange={(e) => updateFilter('mes_movimento', e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              disabled={filtersLoading || !filters.ano_movimento}
            >
              <option value="">Todos os Meses</option>
              {filters.ano_movimento && 
                filterOptions?.movimento_dates?.[filters.ano_movimento]?.map((mes: number) => (
                  <option key={mes} value={mes}>
                    {monthNames[mes - 1]} ({mes})
                  </option>
                ))
              }
            </select>
          </div>
        </div>

        {/* Filter Summary */}
        {hasActiveFilters && data?.summary && (
          <div className="border-t border-gray-200 pt-4 mt-4">
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-gray-600">
                  {Object.keys(filters).length} filtro(s) ativo(s)
                </span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                <span className="text-gray-600">
                  {data.summary.total_projetos?.toLocaleString('pt-BR')} projetos
                </span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                <span className="text-gray-600">
                  {data.summary.total_uh_contratadas?.toLocaleString('pt-BR')} UH contratadas
                </span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                <span className="text-gray-600">
                  {data.summary.overall_percentual_entregues}% entregues
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        <div className="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-gray-900 flex items-center">
                📊 Tabela de Dados Prioritários
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Agrupado por programa e situação do empreendimento
              </p>
            </div>
            {data?.summary && (
              <div className="text-right">
                <div className="text-sm text-gray-500">Total Geral</div>
                <div className="text-lg font-bold text-gray-900">
                  {data.summary.total_projetos?.toLocaleString('pt-BR')} projetos
                </div>
              </div>
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="p-8">
            <div className="animate-pulse space-y-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-8 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <div className="text-red-600">
              <p className="text-lg font-medium">Erro ao carregar dados</p>
              <p className="text-sm mt-1">{error.message}</p>
            </div>
          </div>
        ) : data?.data?.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-300">
              <thead className="bg-gradient-to-r from-gray-700 to-gray-800">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                    <div className="flex items-center">
                      🏠 Programa
                    </div>
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                    <div className="flex items-center">
                      📋 Situação do Empreendimento
                    </div>
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                    <div className="flex items-center justify-center">
                      📊 Projetos
                    </div>
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                    <div className="flex items-center justify-center">
                      🏗️ UH Contratadas
                    </div>
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                    <div className="flex items-center justify-center">
                      ✅ UH Entregues
                    </div>
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                    <div className="flex items-center justify-center">
                      📈 % Entregues
                    </div>
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">
                    <div className="flex items-center justify-center">
                      ⏳ UH Vigentes
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {/* Group data by program and add subtotals */}
                {(() => {
                  // Group data by program
                  const groupedData = data.data.reduce((acc: any, row: any) => {
                    if (!acc[row.programa]) {
                      acc[row.programa] = {
                        rows: [],
                        totals: {
                          projetos: 0,
                          uh_contratadas: 0,
                          uh_entregues: 0,
                          uh_vigentes: 0
                        }
                      }
                    }
                    acc[row.programa].rows.push(row)
                    acc[row.programa].totals.projetos += row.projetos || 0
                    acc[row.programa].totals.uh_contratadas += row.uh_contratadas || 0
                    acc[row.programa].totals.uh_entregues += row.uh_entregues || 0
                    acc[row.programa].totals.uh_vigentes += row.uh_vigentes || 0
                    return acc
                  }, {})

                  // Sort programs: FAR, FDS, RURAL
                  const programOrder = ['FAR', 'FDS', 'RURAL']
                  const sortedPrograms = programOrder.filter(p => groupedData[p])

                  return sortedPrograms.map((programa: string) => {
                    const group = groupedData[programa]
                    const totals = group.totals
                    const percentual = totals.uh_contratadas > 0 
                      ? ((totals.uh_entregues / totals.uh_contratadas) * 100).toFixed(1)
                      : '0'

                    return (
                      <React.Fragment key={programa}>
                        {/* Program Subtotal Row */}
                        <tr className={`${
                          programa === 'FAR' ? 'bg-gradient-to-r from-green-100 to-green-50 border-l-4 border-green-500' :
                          programa === 'FDS' ? 'bg-gradient-to-r from-purple-100 to-purple-50 border-l-4 border-purple-500' :
                          'bg-gradient-to-r from-yellow-100 to-yellow-50 border-l-4 border-yellow-500'
                        } font-bold text-gray-800 shadow-sm`}>
                          <td className="px-6 py-5 whitespace-nowrap text-sm border-r border-gray-200">
                            <div className="flex items-center">
                              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                programa === 'FAR' ? 'bg-green-500 text-white' :
                                programa === 'FDS' ? 'bg-purple-500 text-white' :
                                'bg-yellow-500 text-white'
                              }`}>
                                {programa === 'FAR' ? '🏗️' : programa === 'FDS' ? '🏘️' : '🌾'} {programa}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-5 whitespace-nowrap text-sm font-semibold border-r border-gray-200">
                            <span className="text-gray-700">SUBTOTAL {programa}</span>
                          </td>
                          <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold border-r border-gray-200">
                            <span className="bg-white px-3 py-1 rounded-lg shadow-sm">
                              {totals.projetos.toLocaleString('pt-BR')}
                            </span>
                          </td>
                          <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold border-r border-gray-200">
                            <span className="bg-white px-3 py-1 rounded-lg shadow-sm">
                              {totals.uh_contratadas.toLocaleString('pt-BR')}
                            </span>
                          </td>
                          <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold border-r border-gray-200">
                            <span className="bg-white px-3 py-1 rounded-lg shadow-sm">
                              {totals.uh_entregues.toLocaleString('pt-BR')}
                            </span>
                          </td>
                          <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold border-r border-gray-200">
                            <span className={`px-3 py-1 rounded-lg font-bold text-white shadow-sm ${
                              parseFloat(percentual) >= 80 ? 'bg-green-500' :
                              parseFloat(percentual) >= 50 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}>
                              {percentual}%
                            </span>
                          </td>
                          <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold">
                            <span className="bg-white px-3 py-1 rounded-lg shadow-sm">
                              {totals.uh_vigentes.toLocaleString('pt-BR')}
                            </span>
                          </td>
                        </tr>

                        {/* Detail rows for this program */}
                        {group.rows.map((row: any, idx: number) => {
                          // Status color coding based on situacao
                          const getStatusStyle = (situacao: string) => {
                            switch (situacao) {
                              case 'CONCLUÍDO E ENTREGUE':
                                return 'bg-green-50 text-green-800 border-green-200'
                              case 'EM ANDAMENTO':
                                return 'bg-blue-50 text-blue-800 border-blue-200'
                              case 'PARALISADO':
                                return 'bg-red-50 text-red-800 border-red-200'
                              case 'DESIMOBILIZADO':
                                return 'bg-gray-50 text-gray-800 border-gray-200'
                              case 'DISTRATADO/CANCELADO':
                                return 'bg-orange-50 text-orange-800 border-orange-200'
                              default:
                                return 'bg-gray-50 text-gray-700 border-gray-200'
                            }
                          }

                          return (
                            <tr key={`${programa}-${idx}`} className="hover:bg-gray-50 transition-colors duration-150 border-b border-gray-100">
                              <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                                <div className="w-4 h-4 rounded-full bg-gradient-to-r opacity-30" style={{
                                  background: programa === 'FAR' ? 'linear-gradient(to right, #10b981, #059669)' :
                                             programa === 'FDS' ? 'linear-gradient(to right, #8b5cf6, #7c3aed)' :
                                             'linear-gradient(to right, #f59e0b, #d97706)'
                                }}></div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getStatusStyle(row.situacao_empreendimento)}`}>
                                  {row.situacao_empreendimento}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900 border-r border-gray-200">
                                <span className="bg-gray-50 px-2 py-1 rounded">
                                  {row.projetos?.toLocaleString('pt-BR')}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900 border-r border-gray-200">
                                <span className="bg-blue-50 px-2 py-1 rounded text-blue-800">
                                  {row.uh_contratadas?.toLocaleString('pt-BR')}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900 border-r border-gray-200">
                                <span className="bg-green-50 px-2 py-1 rounded text-green-800">
                                  {row.uh_entregues?.toLocaleString('pt-BR')}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-center text-sm border-r border-gray-200">
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold text-white ${
                                  row.percentual_entregues >= 80 ? 'bg-green-500' :
                                  row.percentual_entregues >= 50 ? 'bg-yellow-500' :
                                  'bg-red-500'
                                }`}>
                                  {row.percentual_entregues}%
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900">
                                <span className="bg-orange-50 px-2 py-1 rounded text-orange-800">
                                  {row.uh_vigentes?.toLocaleString('pt-BR')}
                                </span>
                              </td>
                            </tr>
                          )
                        })}
                      </React.Fragment>
                    )
                  })
                })()}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">
            <p className="text-lg">Nenhum dado encontrado</p>
            <p className="text-sm mt-1">Tente ajustar os filtros</p>
          </div>
        )}

        {/* Summary Footer */}
        {data?.summary && (
          <div className="bg-gradient-to-r from-gray-800 to-gray-900 px-6 py-6 border-t border-gray-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-lg font-bold text-white flex items-center">
                  📊 TOTAIS GERAIS
                </span>
              </div>
              <div className="grid grid-cols-5 gap-6">
                <div className="text-center">
                  <div className="text-xs text-gray-300 uppercase tracking-wider">Projetos</div>
                  <div className="text-lg font-bold text-white">
                    {data.summary.total_projetos?.toLocaleString('pt-BR')}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-300 uppercase tracking-wider">UH Contratadas</div>
                  <div className="text-lg font-bold text-blue-300">
                    {data.summary.total_uh_contratadas?.toLocaleString('pt-BR')}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-300 uppercase tracking-wider">UH Entregues</div>
                  <div className="text-lg font-bold text-green-300">
                    {data.summary.total_uh_entregues?.toLocaleString('pt-BR')}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-300 uppercase tracking-wider">% Entregues</div>
                  <div className={`text-lg font-bold ${
                    data.summary.overall_percentual_entregues >= 80 ? 'text-green-300' :
                    data.summary.overall_percentual_entregues >= 50 ? 'text-yellow-300' :
                    'text-red-300'
                  }`}>
                    {data.summary.overall_percentual_entregues}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-300 uppercase tracking-wider">UH Vigentes</div>
                  <div className="text-lg font-bold text-orange-300">
                    {data.summary.total_uh_vigentes?.toLocaleString('pt-BR')}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}