/**
 * Centralized status color mapping for consistent visualization across all charts
 * Based on audit requirement (o): "Se possível, utilizar cores diferentes em cada categoria"
 */

export const STATUS_COLOR_MAP: Record<string, string> = {
  // Primary statuses
  'Em Andamento': '#1f77b4',      // Medium Blue
  'Atrasada': '#ff7f0e',          // Dark Orange
  'Normal': '#2ca02c',            // Light Green
  'Paralisada': '#d62728',        // Dark Red
  'Não Iniciada': '#9467bd',      // Purple
  'Outras': '#7f7f7f',            // Gray
  
  // Dados Prioritários specific statuses
  'CONCLUÍDO E ENTREGUE': '#2ca02c',     // Light Green (same as Normal - success state)
  'EM ANDAMENTO': '#1f77b4',             // Medium Blue (same as Em Andamento)
  'PARALISADO': '#d62728',                // Dark Red (same as Paralisada)
  'DESMOBILIZADO': '#bcbd22',             // Yellow-Green
  'DISTRATADO/CANCELADO': '#e377c2',      // Pink
  'FASE PROJETO': '#17becf',              // Cyan
  
  // Default fallback
  'default': '#8c564b'                    // Brown
};

/**
 * Get color for a given status
 * @param status - The status string
 * @returns Hex color code
 */
export function getStatusColor(status: string): string {
  return STATUS_COLOR_MAP[status] || STATUS_COLOR_MAP['default'];
}

/**
 * Get array of colors for given statuses
 * @param statuses - Array of status strings
 * @returns Array of hex color codes
 */
export function getStatusColors(statuses: string[]): string[] {
  return statuses.map(status => getStatusColor(status));
}

/**
 * Status display configuration with colors and labels
 */
export const STATUS_CONFIG = {
  'Em Andamento': {
    color: '#1f77b4',
    label: 'Em Andamento',
    icon: '🔄'
  },
  'Atrasada': {
    color: '#ff7f0e',
    label: 'Atrasada',
    icon: '⚠️'
  },
  'Normal': {
    color: '#2ca02c',
    label: 'Normal',
    icon: '✅'
  },
  'Paralisada': {
    color: '#d62728',
    label: 'Paralisada',
    icon: '🛑'
  },
  'Não Iniciada': {
    color: '#9467bd',
    label: 'Não Iniciada',
    icon: '⏳'
  },
  'Outras': {
    color: '#7f7f7f',
    label: 'Outras',
    icon: '📋'
  }
};