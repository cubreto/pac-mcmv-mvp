/**
 * MCMV Dashboard v5 - Program-specific Page
 * Individual program analysis (RURAL, FAR, FDS)
 */

import { useParams } from 'react-router-dom'

export default function ProgramPage() {
  const { programa } = useParams<{ programa: string }>()

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          📊 {programa} - Análise Detalhada
        </h1>
        <p className="text-gray-600">
          Esta página estará disponível em breve com análises detalhadas do programa {programa}.
        </p>
      </div>
    </div>
  )
}