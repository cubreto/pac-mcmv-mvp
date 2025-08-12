/**
 * MCMV Dashboard v5 - RURAL Program Specific Filters
 * Adds tipo and modalidade_proposta filters for RURAL page
 */

import { useRuralFilters } from '../api/hooks'
import { LoadingSpinner } from './LoadingSpinner'

interface RuralFiltersProps {
  tipo?: string
  modalidadeProposta?: string
  onTipoChange: (value: string | undefined) => void
  onModalidadeChange: (value: string | undefined) => void
}

export default function RuralFilters({ 
  tipo, 
  modalidadeProposta, 
  onTipoChange, 
  onModalidadeChange 
}: RuralFiltersProps) {
  const { data: ruralFilters, isLoading } = useRuralFilters()

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600">Carregando filtros RURAL...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Filtros Específicos RURAL
        </h3>
        {(tipo || modalidadeProposta) && (
          <button
            onClick={() => {
              onTipoChange(undefined)
              onModalidadeChange(undefined)
            }}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Limpar filtros RURAL
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Tipo Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tipo
          </label>
          <select
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            value={tipo || ''}
            onChange={(e) => onTipoChange(e.target.value || undefined)}
          >
            <option value="">Todos</option>
            {ruralFilters?.data?.tipos?.map((tipoOption) => (
              <option key={tipoOption.value} value={tipoOption.value}>
                {tipoOption.label}
              </option>
            ))}
          </select>
        </div>

        {/* Modalidade Proposta Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Modalidade da Proposta
          </label>
          <select
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            value={modalidadeProposta || ''}
            onChange={(e) => onModalidadeChange(e.target.value || undefined)}
          >
            <option value="">Todas</option>
            {ruralFilters?.data?.modalidades?.map((modalidadeOption) => (
              <option key={modalidadeOption.value} value={modalidadeOption.value}>
                {modalidadeOption.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filters Summary */}
      {(tipo || modalidadeProposta) && (
        <div className="mt-4 p-3 bg-orange-50 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm text-orange-700">
                Filtros RURAL ativos:
                {tipo && <span className="ml-2 font-medium">Tipo: {tipo}</span>}
                {tipo && modalidadeProposta && <span className="mx-1">•</span>}
                {modalidadeProposta && <span className="ml-2 font-medium">Modalidade: {modalidadeProposta}</span>}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}