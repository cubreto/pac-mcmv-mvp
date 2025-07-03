/**
 * MCMV Dashboard v5 - Global Filter Context
 * Provides shared filter state across all tabs (Dashboard, RURAL, FAR, FDS)
 */

import { createContext, useContext, useState, ReactNode } from 'react'

// Global filter state interface
export interface GlobalFilterState {
  region?: string
  state?: string
  municipality?: string
  status?: string
  programa?: string
}

// Context interface
interface FilterContextType {
  filters: GlobalFilterState
  updateFilter: (key: keyof GlobalFilterState, value: string | undefined) => void
  clearAllFilters: () => void
  setFilters: (filters: GlobalFilterState) => void
}

// Create the context
const FilterContext = createContext<FilterContextType | undefined>(undefined)

// Provider component
interface FilterProviderProps {
  children: ReactNode
}

export function FilterProvider({ children }: FilterProviderProps) {
  const [filters, setFiltersState] = useState<GlobalFilterState>({})

  const updateFilter = (key: keyof GlobalFilterState, value: string | undefined) => {
    setFiltersState(prev => {
      const newFilters = { ...prev, [key]: value || undefined }
      
      // Clear dependent filters when parent changes (cascading logic)
      if (key === 'region') {
        delete newFilters.state
        delete newFilters.municipality
      } else if (key === 'state') {
        delete newFilters.municipality
      }
      
      // Remove undefined values
      Object.keys(newFilters).forEach(k => {
        if (newFilters[k as keyof GlobalFilterState] === undefined) {
          delete newFilters[k as keyof GlobalFilterState]
        }
      })
      
      return newFilters
    })
  }

  const clearAllFilters = () => {
    setFiltersState({})
  }

  const setFilters = (newFilters: GlobalFilterState) => {
    setFiltersState(newFilters)
  }

  const contextValue: FilterContextType = {
    filters,
    updateFilter,
    clearAllFilters,
    setFilters
  }

  return (
    <FilterContext.Provider value={contextValue}>
      {children}
    </FilterContext.Provider>
  )
}

// Custom hook to use the filter context
export function useGlobalFilters() {
  const context = useContext(FilterContext)
  if (context === undefined) {
    throw new Error('useGlobalFilters must be used within a FilterProvider')
  }
  return context
}

// Export the context for direct access if needed
export { FilterContext }