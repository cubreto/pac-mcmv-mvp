/**
 * MCMV Dashboard v5 - Previsão de Entrega Tab Component
 * Shows projects with delivery forecast dates
 */


interface PrevisaoEntregaTabProps {
  data: any
  isLoading: boolean
}

export default function PrevisaoEntregaTab({ data, isLoading }: PrevisaoEntregaTabProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8">
        <div className="flex justify-center items-center">
          <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="ml-2 text-gray-600">Carregando previsões de entrega...</span>
        </div>
      </div>
    )
  }

  if (!data || data.summary.total_projetos === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8 text-center">
        <div className="text-gray-500">
          <h3 className="text-xl font-semibold mb-2">Nenhuma previsão de entrega disponível</h3>
          <p className="text-sm">Os dados de previsão de entrega serão exibidos conforme disponibilizados no sistema.</p>
        </div>
      </div>
    )
  }

  const { projetos, timeline, summary } = data

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg p-4 border-l-4 border-blue-500 shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{summary.total_projetos}</div>
          <div className="text-sm text-gray-600">Projetos</div>
        </div>
        
        <div className="bg-white rounded-lg p-4 border-l-4 border-green-500 shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{summary.total_uh?.toLocaleString('pt-BR')}</div>
          <div className="text-sm text-gray-600">UH a Entregar</div>
        </div>
        
        <div className="bg-white rounded-lg p-4 border-l-4 border-purple-500 shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{summary.meses_com_entregas}</div>
          <div className="text-sm text-gray-600">Meses</div>
        </div>
        
        <div className="bg-white rounded-lg p-4 border-l-4 border-orange-500 shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{summary.modalidades_incluidas?.length || 0}</div>
          <div className="text-sm text-gray-600">Programas</div>
        </div>
      </div>

      {/* Timeline Chart */}
      {timeline && timeline.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Cronograma de Entregas
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {timeline.map((month: any) => (
              <div key={month.month} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">
                    {new Date(month.month + '-01').toLocaleDateString('pt-BR', { 
                      month: 'long', 
                      year: 'numeric' 
                    })}
                  </div>
                  <div className="mt-2 space-y-1">
                    <div className="text-sm text-gray-600">
                      <span className="font-semibold">{month.projetos}</span> projetos
                    </div>
                    <div className="text-sm text-gray-600">
                      <span className="font-semibold">{month.uh_total?.toLocaleString('pt-BR')}</span> UH
                    </div>
                    <div className="text-xs text-gray-500">
                      {month.modalidades?.join(', ') || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Projects Table */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        <div className="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-blue-100">
          <h3 className="text-xl font-bold text-gray-900">
            Projetos com Previsão de Entrega
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Detalhes dos {projetos?.length || 0} projetos com datas de entrega previstas
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gradient-to-r from-gray-700 to-gray-800">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">
                  APF
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">
                  Empreendimento
                </th>
                <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">
                  UF
                </th>
                <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">
                  Programa
                </th>
                <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">
                  UH a Entregar
                </th>
                <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">
                  Data Contratação
                </th>
                <th className="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">
                  Previsão Entrega
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {projetos?.map((projeto: any, index: number) => (
                <tr key={projeto.apf} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {projeto.apf}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                    <div className="truncate" title={projeto.nome_empreendimento}>
                      {projeto.nome_empreendimento}
                    </div>
                    <div className="text-xs text-gray-500">{projeto.municipio}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {projeto.sg_uf}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      projeto.modalidade === 'FAR' ? 'bg-green-100 text-green-800' :
                      projeto.modalidade === 'FDS' ? 'bg-purple-100 text-purple-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {projeto.modalidade}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900">
                    {projeto.uh_a_entregar?.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {projeto.data_contratacao ? 
                      new Date(projeto.data_contratacao).toLocaleDateString('pt-BR') : 
                      'N/A'
                    }
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {projeto.data_previsao_entrega ? 
                        new Date(projeto.data_previsao_entrega).toLocaleDateString('pt-BR') : 
                        'N/A'
                      }
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}