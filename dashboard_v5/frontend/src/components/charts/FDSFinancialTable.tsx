/**
 * FDS Financial Table - Advanced Expandable Design
 * Follows WorkingChart pattern to avoid React Error #310
 */

import { useMemo, useState, useCallback } from 'react'
import { useFDSFinancialTable } from '../../api/hooks'

interface FDSFinancialTableProps {
  filters?: {
    regiao?: string
    state?: string
    municipality?: string
    status?: string
  }
}

export default function FDSFinancialTable({ filters }: FDSFinancialTableProps) {
  // All hooks called unconditionally at top
  const { data, isLoading, error } = useFDSFinancialTable(filters)
  const [showAll, setShowAll] = useState(false)
  const [expandedStates, setExpandedStates] = useState<Set<string>>(new Set())

  // Group data by state - memoized to prevent re-renders
  const groupedData = useMemo(() => {
    if (!data?.data?.length) return []
    
    const grouped = data.data.reduce((acc: any, row: any) => {
      if (!acc[row.uf]) {
        acc[row.uf] = {
          state: row.uf,
          municipalities: [],
          totals: {
            projects: 0,
            uh: 0,
            value: 0,
            investment: 0
          }
        }
      }
      acc[row.uf].municipalities.push(row)
      acc[row.uf].totals.projects += row.total_projetos || 0
      acc[row.uf].totals.uh += row.total_uh_contratadas || 0
      acc[row.uf].totals.value += row.total_valor_contratado || 0
      acc[row.uf].totals.investment += row.total_investimento || 0
      return acc
    }, {})

    return Object.values(grouped).sort((a: any, b: any) => b.totals.uh - a.totals.uh)
  }, [data])

  // Memoized display data
  const displayData = useMemo(() => 
    showAll ? groupedData : groupedData.slice(0, 5),
    [groupedData, showAll]
  )

  // Toggle state expansion - useCallback to prevent re-renders
  const toggleStateExpansion = useCallback((state: string) => {
    setExpandedStates(prev => {
      const newSet = new Set(prev)
      if (newSet.has(state)) {
        newSet.delete(state)
      } else {
        newSet.add(state)
      }
      return newSet
    })
  }, [])

  // Early returns after all hooks
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">💰 Tabela Financeira FDS</h3>
        <div className="h-32 flex items-center justify-center bg-gray-50 rounded-lg">
          <p className="text-gray-500">Carregando dados financeiros...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">💰 Tabela Financeira FDS</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Erro ao carregar dados: {error.message}</p>
        </div>
      </div>
    )
  }

  if (!displayData.length) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">💰 Tabela Financeira FDS</h3>
        <div className="text-center py-8 text-gray-500">
          Nenhum dado financeiro disponível
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">💰 Tabela Financeira FDS</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Projetos
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                UH Contratadas
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Valor Contratado
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Investimento Total
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayData.map((stateData: any) => (
              <React.Fragment key={stateData.state}>
                <tr 
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => toggleStateExpansion(stateData.state)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div className="flex items-center">
                      <span className="mr-2">
                        {expandedStates.has(stateData.state) ? '▼' : '▶'}
                      </span>
                      {stateData.state}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {stateData.totals.projects.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {stateData.totals.uh.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    R$ {(stateData.totals.value / 1e6).toFixed(1)}M
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    R$ {(stateData.totals.investment / 1e6).toFixed(1)}M
                  </td>
                </tr>
                
                {expandedStates.has(stateData.state) && (
                  <tr>
                    <td colSpan={5} className="px-0 py-0">
                      <div className="bg-gray-50">
                        <table className="min-w-full">
                          <tbody className="divide-y divide-gray-200">
                            {stateData.municipalities.map((muni: any, idx: number) => (
                              <tr key={idx} className="hover:bg-gray-100">
                                <td className="pl-14 pr-6 py-3 text-sm text-gray-600">
                                  {muni.municipio}
                                </td>
                                <td className="px-6 py-3 text-sm text-gray-600 text-right">
                                  {muni.total_projetos?.toLocaleString('pt-BR') || 0}
                                </td>
                                <td className="px-6 py-3 text-sm text-gray-600 text-right">
                                  {muni.total_uh_contratadas?.toLocaleString('pt-BR') || 0}
                                </td>
                                <td className="px-6 py-3 text-sm text-gray-600 text-right">
                                  R$ {((muni.total_valor_contratado || 0) / 1e6).toFixed(1)}M
                                </td>
                                <td className="px-6 py-3 text-sm text-gray-600 text-right">
                                  R$ {((muni.total_investimento || 0) / 1e6).toFixed(1)}M
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
      
      {groupedData.length > 5 && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {showAll ? 'Mostrar menos' : `Mostrar todos (${groupedData.length} estados)`}
          </button>
        </div>
      )}
    </div>
  )
}

// React Fragment import for the component
import React from 'react'