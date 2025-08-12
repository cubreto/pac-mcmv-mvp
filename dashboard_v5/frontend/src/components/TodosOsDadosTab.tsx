/**
 * MCMV Dashboard v5 - Todos os Dados Tab Component
 * Shows all historical snapshots from dados prioritarios
 */

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface TodosOsDadosTabProps {
  data: any
  isLoading: boolean
  error: any
  isFetching: boolean
}

// Program colors and icons
const PROGRAM_COLORS: Record<string, string> = {
  FAR: '#3B82F6',      // Blue
  FDS: '#10B981',      // Green
  Entidades: '#10B981', // Green (same as FDS)
  RURAL: '#F59E0B',    // Yellow
  default: '#6B7280'   // Gray
}

const PROGRAM_ICONS: Record<string, string> = {
  FAR: '🏢',
  FDS: '🏘️',
  Entidades: '🏘️',
  RURAL: '🌾',
  default: '📊'
}

export default function TodosOsDadosTab({ data, isLoading, error }: TodosOsDadosTabProps) {
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({})

  // Toggle expansion for a specific program/situacao combination
  const toggleExpanded = (key: string) => {
    setExpandedRows(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  // Group data by modalidade (program) and situacao with month/year details
  const groupedData = data?.data?.reduce((acc: any, item: any) => {
    const program = item.programa === 'Entidades' ? 'FDS' : item.programa
    const situacao = item.situacao_empreendimento || 'SEM SITUAÇÃO'
    const programKey = program
    
    // Initialize program group
    if (!acc[programKey]) {
      acc[programKey] = {
        programa: program,
        situacoes: {},
        totals: {
          projetos: 0,
          uh_contratadas: 0,
          uh_entregues: 0,
          valor_contratado: 0,
          valor_desembolsado: 0
        }
      }
    }
    
    // Initialize situacao within program
    if (!acc[programKey].situacoes[situacao]) {
      acc[programKey].situacoes[situacao] = {
        situacao: situacao,
        monthlyData: [],
        totals: {
          projetos: 0,
          uh_contratadas: 0,
          uh_entregues: 0,
          valor_contratado: 0,
          valor_desembolsado: 0
        }
      }
    }
    
    // Add monthly data with formatted month/year
    const monthYear = item.mes_movimento && item.ano_movimento
      ? `${String(item.mes_movimento).padStart(2, '0')}/${item.ano_movimento}`
      : 'N/A'
    
    // Data is already aggregated from materialized view
    acc[programKey].situacoes[situacao].monthlyData.push({
      ...item,
      monthYear,
      // Ensure numeric values
      projetos: item.projetos || 0,
      uh_contratadas: item.uh_contratadas || 0,
      uh_entregues: item.uh_entregues || 0,
      valor_contratado: parseFloat(item.valor_contratado) || 0,
      valor_desembolsado: parseFloat(item.valor_desembolsado) || 0
    })
    
    // Update situacao totals (avoiding double counting)
    // We'll calculate these from the monthly data later
    
    return acc
  }, {})

  // Calculate totals and convert to array format
  const programGroups = groupedData ? Object.values(groupedData).map((group: any) => {
    // Convert situacoes object to array
    const situacoesArray = Object.values(group.situacoes).map((situacaoData: any) => {
      // Calculate situacao totals from aggregated data
      // Data is aggregated by state, so we need to sum across all states for each month
      // and then take the latest month's total
      
      // Group by month/year first
      const monthlyTotals = new Map()
      
      situacaoData.monthlyData.forEach((item: any) => {
        const monthKey = `${item.ano_movimento}-${item.mes_movimento}`
        
        if (!monthlyTotals.has(monthKey)) {
          monthlyTotals.set(monthKey, {
            ano_movimento: item.ano_movimento,
            mes_movimento: item.mes_movimento,
            projetos: 0,
            uh_contratadas: 0,
            uh_entregues: 0,
            valor_contratado: 0,
            valor_desembolsado: 0
          })
        }
        
        const totals = monthlyTotals.get(monthKey)
        totals.projetos += item.projetos || 0
        totals.uh_contratadas += item.uh_contratadas || 0
        totals.uh_entregues += item.uh_entregues || 0
        totals.valor_contratado += item.valor_contratado || 0
        totals.valor_desembolsado += item.valor_desembolsado || 0
      })
      
      // Get the latest month's totals
      let totalProjetos = 0
      let totalUhContratadas = 0
      let totalUhEntregues = 0
      let totalValorContratado = 0
      let totalValorDesembolsado = 0
      
      const latestMonth = Array.from(monthlyTotals.values()).reduce((latest: any, current: any) => {
        const currentDate = current.ano_movimento * 12 + current.mes_movimento
        const latestDate = latest ? latest.ano_movimento * 12 + latest.mes_movimento : 0
        return currentDate > latestDate ? current : latest
      }, null)
      
      if (latestMonth) {
        totalProjetos = latestMonth.projetos
        totalUhContratadas = latestMonth.uh_contratadas
        totalUhEntregues = latestMonth.uh_entregues
        totalValorContratado = latestMonth.valor_contratado
        totalValorDesembolsado = latestMonth.valor_desembolsado
      }
      
      situacaoData.totals = {
        projetos: totalProjetos,
        uh_contratadas: totalUhContratadas,
        uh_entregues: totalUhEntregues,
        valor_contratado: totalValorContratado,
        valor_desembolsado: totalValorDesembolsado
      }
      return situacaoData
    })
    
    // Calculate program totals from situacao totals
    group.totals = situacoesArray.reduce((totals: any, situacao: any) => ({
      projetos: totals.projetos + situacao.totals.projetos,
      uh_contratadas: totals.uh_contratadas + situacao.totals.uh_contratadas,
      uh_entregues: totals.uh_entregues + situacao.totals.uh_entregues,
      valor_contratado: totals.valor_contratado + situacao.totals.valor_contratado,
      valor_desembolsado: totals.valor_desembolsado + situacao.totals.valor_desembolsado
    }), {
      projetos: 0,
      uh_contratadas: 0,
      uh_entregues: 0,
      valor_contratado: 0,
      valor_desembolsado: 0
    })
    
    return {
      ...group,
      situacoes: situacoesArray
    }
  }) : []

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Carregando dados históricos...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8">
        <div className="text-center text-red-600">
          <p className="text-lg font-semibold">Erro ao carregar dados</p>
          <p className="text-sm mt-2">{error.message || 'Tente novamente mais tarde'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200">
      <div className="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              📊 Dados Históricos - Histórico Completo
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Visualização de todos os snapshots mensais agrupados por programa e situação
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Total de Registros</div>
            <div className="text-lg font-bold text-gray-900">
              {data?.data?.length.toLocaleString('pt-BR')} registros
            </div>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gradient-to-r from-gray-700 to-gray-800">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                Programa / Situação
              </th>
              <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                Projetos
              </th>
              <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                UH Contratadas
              </th>
              <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                UH Entregues
              </th>
              <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                Valor Contratado
              </th>
              <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider border-r border-gray-600">
                Valor Desembolsado
              </th>
              <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">
                Investimento Total
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {programGroups.map((group: any, groupIndex: number) => (
              <>
                {/* Program Header Row */}
                <tr key={`header-${groupIndex}`} className="bg-gradient-to-r from-gray-100 to-gray-50">
                  <td colSpan={7} className="px-6 py-3">
                    <div className="flex items-center">
                      <span 
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold text-white"
                        style={{ backgroundColor: PROGRAM_COLORS[group.programa] || PROGRAM_COLORS.default }}
                      >
                        {PROGRAM_ICONS[group.programa] || PROGRAM_ICONS.default} {group.programa}
                      </span>
                    </div>
                  </td>
                </tr>

                {/* Situação Rows */}
                {group.situacoes
                  .sort((a: any, b: any) => b.totals.projetos - a.totals.projetos)
                  .map((situacao: any, situacaoIndex: number) => {
                    const situacaoKey = `${group.programa}-${situacao.situacao}`
                    const isExpanded = expandedRows[situacaoKey]
                    
                    return (
                      <>
                        {/* Situação Summary Row (Clickable) */}
                        <tr 
                          key={`${groupIndex}-${situacaoIndex}`} 
                          className="hover:bg-gray-50 transition-colors duration-150 cursor-pointer"
                          onClick={() => toggleExpanded(situacaoKey)}
                        >
                          <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                            <div className="flex items-center pl-8">
                              <button className="mr-2 text-gray-500 hover:text-gray-700">
                                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                              </button>
                              <div className={`flex-shrink-0 h-2 w-2 rounded-full mr-2 ${
                                situacao.situacao?.includes('CONCLUÍDO') ? 'bg-green-500' :
                                situacao.situacao?.includes('ANDAMENTO') ? 'bg-blue-500' :
                                situacao.situacao?.includes('PARALISADO') ? 'bg-red-500' :
                                situacao.situacao?.includes('DISTRATADO') ? 'bg-gray-500' :
                                'bg-yellow-500'
                              }`}></div>
                              <span className="text-sm text-gray-900">{situacao.situacao}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                            {situacao.totals.projetos?.toLocaleString('pt-BR')}
                          </td>
                          <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                            {situacao.totals.uh_contratadas?.toLocaleString('pt-BR')}
                          </td>
                          <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                            {situacao.totals.uh_entregues?.toLocaleString('pt-BR')}
                          </td>
                          <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                            {situacao.totals.valor_contratado > 0 ? `R$ ${(situacao.totals.valor_contratado / 1e9).toFixed(2)}B` : '-'}
                          </td>
                          <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                            {situacao.totals.valor_desembolsado > 0 ? `R$ ${(situacao.totals.valor_desembolsado / 1e9).toFixed(2)}B` : '-'}
                          </td>
                          <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900">
                            {(situacao.totals.valor_contratado + situacao.totals.valor_desembolsado) > 0 
                              ? `R$ ${((situacao.totals.valor_contratado + situacao.totals.valor_desembolsado) / 1e9).toFixed(2)}B` 
                              : '-'}
                          </td>
                        </tr>

                        {/* Monthly Detail Rows (Expandable) */}
                        {isExpanded && (() => {
                          // Aggregate monthly data across all states
                          const monthlyAggregated = new Map()
                          
                          situacao.monthlyData.forEach((item: any) => {
                            const monthKey = `${item.ano_movimento}-${item.mes_movimento}`
                            
                            if (!monthlyAggregated.has(monthKey)) {
                              monthlyAggregated.set(monthKey, {
                                ano_movimento: item.ano_movimento,
                                mes_movimento: item.mes_movimento,
                                monthYear: `${String(item.mes_movimento).padStart(2, '0')}/${item.ano_movimento}`,
                                projetos: 0,
                                uh_contratadas: 0,
                                uh_entregues: 0,
                                valor_contratado: 0,
                                valor_desembolsado: 0
                              })
                            }
                            
                            const totals = monthlyAggregated.get(monthKey)
                            totals.projetos += item.projetos || 0
                            totals.uh_contratadas += item.uh_contratadas || 0
                            totals.uh_entregues += item.uh_entregues || 0
                            totals.valor_contratado += item.valor_contratado || 0
                            totals.valor_desembolsado += item.valor_desembolsado || 0
                          })
                          
                          return Array.from(monthlyAggregated.values())
                            .sort((a: any, b: any) => {
                              // Sort by year and month descending
                              const aDate = a.ano_movimento * 100 + a.mes_movimento
                              const bDate = b.ano_movimento * 100 + b.mes_movimento
                              return bDate - aDate
                            })
                            .map((monthData: any, monthIndex: number) => {
                            return (
                              <tr 
                                key={`${groupIndex}-${situacaoIndex}-${monthIndex}`}
                                className="bg-gray-50 hover:bg-gray-100 transition-colors duration-150"
                              >
                                <td className="px-6 py-3 whitespace-nowrap border-r border-gray-200">
                                  <div className="flex items-center pl-16">
                                    <span className="text-xs text-gray-600">{monthData.monthYear}</span>
                                  </div>
                                </td>
                                <td className="px-6 py-3 text-center whitespace-nowrap text-xs text-gray-600 border-r border-gray-200">
                                  {monthData.projetos?.toLocaleString('pt-BR')}
                                </td>
                                <td className="px-6 py-3 text-center whitespace-nowrap text-xs text-gray-600 border-r border-gray-200">
                                  {monthData.uh_contratadas?.toLocaleString('pt-BR')}
                                </td>
                                <td className="px-6 py-3 text-center whitespace-nowrap text-xs text-gray-600 border-r border-gray-200">
                                  {monthData.uh_entregues?.toLocaleString('pt-BR')}
                                </td>
                                <td className="px-6 py-3 text-center whitespace-nowrap text-xs text-gray-600 border-r border-gray-200">
                                  {parseFloat(monthData.valor_contratado) > 0 
                                    ? `R$ ${(parseFloat(monthData.valor_contratado) / 1e9).toFixed(2)}B` 
                                    : '-'}
                                </td>
                                <td className="px-6 py-3 text-center whitespace-nowrap text-xs text-gray-600 border-r border-gray-200">
                                  {parseFloat(monthData.valor_desembolsado) > 0 
                                    ? `R$ ${(parseFloat(monthData.valor_desembolsado) / 1e9).toFixed(2)}B` 
                                    : '-'}
                                </td>
                                <td className="px-6 py-3 text-center whitespace-nowrap text-xs text-gray-600">
                                  {(parseFloat(monthData.valor_contratado) + parseFloat(monthData.valor_desembolsado)) > 0 
                                    ? `R$ ${((parseFloat(monthData.valor_contratado) + parseFloat(monthData.valor_desembolsado)) / 1e9).toFixed(2)}B` 
                                    : '-'}
                                </td>
                              </tr>
                            )
                          })
                        })()}
                      </>
                    )
                  })}

                {/* Program Subtotal Row */}
                <tr key={`subtotal-${groupIndex}`} className="bg-gradient-to-r from-blue-50 to-blue-100 font-semibold">
                  <td className="px-6 py-3 whitespace-nowrap text-sm border-r border-gray-200">
                    <span className="pl-4">Subtotal {group.programa}</span>
                  </td>
                  <td className="px-6 py-3 text-center whitespace-nowrap text-sm border-r border-gray-200">
                    {group.totals.projetos.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-3 text-center whitespace-nowrap text-sm border-r border-gray-200">
                    {group.totals.uh_contratadas.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-3 text-center whitespace-nowrap text-sm border-r border-gray-200">
                    {group.totals.uh_entregues.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-3 text-center whitespace-nowrap text-sm border-r border-gray-200">
                    R$ {(group.totals.valor_contratado / 1e9).toFixed(2)}B
                  </td>
                  <td className="px-6 py-3 text-center whitespace-nowrap text-sm border-r border-gray-200">
                    R$ {(group.totals.valor_desembolsado / 1e9).toFixed(2)}B
                  </td>
                  <td className="px-6 py-3 text-center whitespace-nowrap text-sm">
                    R$ {((group.totals.valor_contratado + group.totals.valor_desembolsado) / 1e9).toFixed(2)}B
                  </td>
                </tr>
              </>
            ))}

            {(!data?.data || data.data.length === 0) && (
              <tr>
                <td colSpan={7} className="text-center py-12 text-gray-500">
                  <p className="text-lg">Nenhum dado encontrado</p>
                  <p className="text-sm mt-1">Tente ajustar os filtros</p>
                </td>
              </tr>
            )}
          </tbody>

          {/* Grand Total Footer - Removed as requested */}
        </table>
      </div>
    </div>
  )
}