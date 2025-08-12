/**
 * MCMV Dashboard v5 - Estado Atual Tab Component
 * Shows latest snapshot per project (current state) with beautiful grouped table style
 */

interface EstadoAtualTabProps {
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

export default function EstadoAtualTab({ data, isLoading, error }: EstadoAtualTabProps) {
  // Group data by program first, then by situação
  const groupedData = data?.data?.reduce((acc: any, item: any) => {
    const program = item.programa === 'Entidades' ? 'FDS' : item.programa
    if (!acc[program]) {
      acc[program] = {
        programa: program,
        situacoes: [],
        totals: {
          projetos: 0,
          uh_contratadas: 0,
          uh_entregues: 0,
          valor_contratado: 0,
          valor_desembolsado: 0
        }
      }
    }
    
    // Add situação data
    acc[program].situacoes.push(item)
    
    // Update totals
    acc[program].totals.projetos += item.projetos || 0
    acc[program].totals.uh_contratadas += item.uh_contratadas || 0
    acc[program].totals.uh_entregues += item.uh_entregues || 0
    acc[program].totals.valor_contratado += parseFloat(item.valor_contratado) || 0
    acc[program].totals.valor_desembolsado += parseFloat(item.valor_desembolsado) || 0
    
    return acc
  }, {})

  const programGroups = groupedData ? Object.values(groupedData) : []

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Carregando estado atual...</span>
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
      <div className="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-blue-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              Estado Atual dos Projetos
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Snapshot de Maio/2025 agrupado por programa e situação
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
                  <td colSpan={6} className="px-6 py-3">
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
                  .sort((a: any, b: any) => b.projetos - a.projetos)
                  .map((item: any, index: number) => {
                    const valorTotal = (parseFloat(item.valor_contratado) || 0) + (parseFloat(item.valor_desembolsado) || 0)
                    
                    return (
                      <tr key={`${groupIndex}-${index}`} className="hover:bg-gray-50 transition-colors duration-150">
                        <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                          <div className="flex items-center pl-8">
                            <div className={`flex-shrink-0 h-2 w-2 rounded-full mr-2 ${
                              item.situacao_empreendimento?.includes('CONCLUÍDO') ? 'bg-green-500' :
                              item.situacao_empreendimento?.includes('ANDAMENTO') ? 'bg-blue-500' :
                              item.situacao_empreendimento?.includes('PARALISADO') ? 'bg-red-500' :
                              item.situacao_empreendimento?.includes('DISTRATADO') ? 'bg-gray-500' :
                              'bg-yellow-500'
                            }`}></div>
                            <span className="text-sm text-gray-900">{item.situacao_empreendimento}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                          {item.projetos?.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                          {item.uh_contratadas?.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                          {item.uh_entregues?.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-6 py-4 text-center whitespace-nowrap text-sm text-gray-900">
                          {valorTotal > 0 ? `R$ ${(valorTotal / 1e9).toFixed(2)}B` : '-'}
                        </td>
                      </tr>
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
                  <td className="px-6 py-3 text-center whitespace-nowrap text-sm">
                    R$ {((group.totals.valor_contratado + group.totals.valor_desembolsado) / 1e9).toFixed(2)}B
                  </td>
                </tr>
              </>
            ))}

            {(!data?.data || data.data.length === 0) && (
              <tr>
                <td colSpan={5} className="text-center py-12 text-gray-500">
                  <p className="text-lg">Nenhum dado encontrado</p>
                  <p className="text-sm mt-1">Tente ajustar os filtros</p>
                </td>
              </tr>
            )}
          </tbody>

          {/* Grand Total Footer */}
          {data?.summary && (
            <tfoot className="bg-gradient-to-r from-gray-800 to-gray-900">
              <tr>
                <td className="px-6 py-5 whitespace-nowrap text-sm font-bold border-r border-gray-700">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-white text-gray-800">
                    TOTAL GERAL
                  </span>
                </td>
                <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold border-r border-gray-700">
                  <span className="bg-white text-gray-800 px-3 py-1 rounded-lg">
                    {data.summary.total_projetos?.toLocaleString('pt-BR')}
                  </span>
                </td>
                <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold border-r border-gray-700">
                  <span className="bg-white text-gray-800 px-3 py-1 rounded-lg">
                    {data.summary.total_uh_contratadas?.toLocaleString('pt-BR')}
                  </span>
                </td>
                <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold border-r border-gray-700">
                  <span className="bg-white text-gray-800 px-3 py-1 rounded-lg">
                    {data.summary.total_uh_entregues?.toLocaleString('pt-BR')}
                  </span>
                </td>
                <td className="px-6 py-5 whitespace-nowrap text-center text-sm font-bold">
                  <span className="bg-white text-gray-800 px-3 py-1 rounded-lg">
                    R$ {(((data.summary.total_valor_contratado || 0) + (data.summary.total_valor_desembolsado || 0)) / 1e9).toFixed(1)}B
                  </span>
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  )
}