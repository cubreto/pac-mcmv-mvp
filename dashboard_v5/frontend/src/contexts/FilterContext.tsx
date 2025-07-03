/**
 * MCMV Dashboard v5 - Global Filter Context
 * Provides shared filter state across all tabs (Dashboard, RURAL, FAR, FDS)
 */

import { createContext, useContext, useState, ReactNode, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

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
  const queryClient = useQueryClient()

  const updateFilter = useCallback((key: keyof GlobalFilterState, value: string | undefined) => {
    try {
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
        
        // Safely invalidate queries with specific query keys to prevent conflicts
        setTimeout(() => {
          try {
            // Invalidate using the proper query key factory
            queryClient.invalidateQueries({ 
              predicate: (query) => {
                const baseKey = query.queryKey[0] as string
                const queryType = query.queryKey[1] as string
                // Only invalidate MCMV queries with filter-dependent data
                return baseKey === 'mcmv' && [
                  'kpis',
                  'regional', 
                  'temporal',
                  'delivery-forecast'
                ].includes(queryType)
              }
            })
            
            // Also invalidate program-specific chart queries
            queryClient.invalidateQueries({ 
              predicate: (query) => {
                const baseKey = query.queryKey[0] as string
                return ['rural', 'far', 'fds'].includes(baseKey)
              }
            })
          } catch (error) {
            console.warn('Query invalidation failed:', error)
          }
        }, 0)
        
        return newFilters
      })
    } catch (error) {
      console.error('Filter update failed:', error)
    }
  }, [queryClient])

  const clearAllFilters = useCallback(() => {
    try {
      setFiltersState({})
      // Clear all filter-dependent data queries when filters are cleared
      setTimeout(() => {
        try {
          // Clear MCMV queries
          queryClient.invalidateQueries({ 
            predicate: (query) => {
              const baseKey = query.queryKey[0] as string
              const queryType = query.queryKey[1] as string
              return baseKey === 'mcmv' && [
                'kpis',
                'regional', 
                'temporal',
                'delivery-forecast'
              ].includes(queryType)
            }
          })
          
          // Clear program-specific queries
          queryClient.invalidateQueries({ 
            predicate: (query) => {
              const baseKey = query.queryKey[0] as string
              return ['rural', 'far', 'fds'].includes(baseKey)
            }
          })
        } catch (error) {
          console.warn('Query invalidation failed on clear:', error)
        }
      }, 0)
    } catch (error) {
      console.error('Clear filters failed:', error)
    }
  }, [queryClient])

  const setFilters = useCallback((newFilters: GlobalFilterState) => {
    try {
      setFiltersState(newFilters)
    } catch (error) {
      console.error('Set filters failed:', error)
    }
  }, [])

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