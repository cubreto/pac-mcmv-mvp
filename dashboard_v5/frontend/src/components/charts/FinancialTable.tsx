/**
 * Financial Table - Advanced Expandable Design
 * Follows WorkingChart pattern to avoid React Error #310
 */

import { useMemo, useState, useCallback } from 'react'
import { useRuralFinancialTable } from '../../api/hooks'

interface FinancialTableProps {
  filters?: {
    regiao?: string
    state?: string
    municipality?: string
    status?: string
  }
}

export default function FinancialTable({ filters }: FinancialTableProps) {
  // All hooks called unconditionally at top
  const { data, isLoading, error } = useRuralFinancialTable(filters)
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

  // Memoize display data to prevent re-renders
  const displayData = useMemo(() => 
    showAll ? groupedData : groupedData.slice(0, 5),
    [showAll, groupedData]
  )

  // Memoize toggle function to prevent re-renders
  const toggleState = useCallback((stateCode: string) => {
    const newExpanded = new Set(expandedStates)
    if (newExpanded.has(stateCode)) {
      newExpanded.delete(stateCode)
    } else {
      newExpanded.add(stateCode)
    }
    setExpandedStates(newExpanded)
  }, [expandedStates])

  // Early returns after all hooks are called
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-8 bg-gray-200 rounded"></div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        ❌ Erro ao carregar dados financeiros: {error.message}
      </div>
    )
  }

  if (!groupedData.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        Nenhum dado financeiro disponível
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-500">
          {data?.data?.length || 0} municípios • {groupedData.length} estados
        </div>
      </div>

      <div className="space-y-2">
        {displayData.map((stateGroup: any) => {
          const isExpanded = expandedStates.has(stateGroup.state)
          const avgInvestmentPerUH = stateGroup.totals.uh > 0 
            ? stateGroup.totals.investment / stateGroup.totals.uh 
            : 0

          return (
            <div key={stateGroup.state} className="border rounded-lg">
              {/* State Summary Row */}
              <div 
                className="px-4 py-3 bg-gray-50 hover:bg-gray-100 cursor-pointer flex items-center justify-between"
                onClick={() => toggleState(stateGroup.state)}
              >
                <div className="flex items-center space-x-4">
                  <div className="flex items-center">
                    <span className="text-lg mr-2">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                    <span className="font-semibold text-gray-900">
                      {stateGroup.state}
                    </span>
                    <span className="ml-2 text-sm text-gray-500">
                      ({stateGroup.municipalities.length} municípios)
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-6 text-sm">
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {stateGroup.totals.projects.toLocaleString('pt-BR')}
                    </div>
                    <div className="text-gray-500">Projetos</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {stateGroup.totals.uh.toLocaleString('pt-BR')}
                    </div>
                    <div className="text-gray-500">UH</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      R$ {(stateGroup.totals.investment / 1e9).toFixed(1)}B
                    </div>
                    <div className="text-gray-500">Investimento</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      R$ {avgInvestmentPerUH.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                    </div>
                    <div className="text-gray-500">Invest./UH</div>
                  </div>
                </div>
              </div>

              {/* Expanded Municipality Details */}
              {isExpanded && (
                <div className="border-t">
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead className="bg-gray-25">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Município
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Projetos
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            UH
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Investimento
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Invest./UH
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {stateGroup.municipalities
                          .sort((a: any, b: any) => (b.total_uh_contratadas || 0) - (a.total_uh_contratadas || 0))
                          .map((row: any, index: number) => (
                          <tr key={index} className="hover:bg-gray-25">
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {row.municipio}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {row.total_projetos?.toLocaleString('pt-BR')}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {row.total_uh_contratadas?.toLocaleString('pt-BR')}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              R$ {(row.total_investimento / 1e6)?.toFixed(1)}M
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              R$ {row.investimento_medio_uh?.toLocaleString('pt-BR')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Show More/Less Button */}
      {groupedData.length > 5 && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
          >
            {showAll ? 'Mostrar Menos' : `Mostrar Todos (${groupedData.length} estados)`}
          </button>
        </div>
      )}
    </div>
  )
}