/**
 * Currency formatting utilities for MCMV Dashboard v5
 */

/**
 * Format currency values with appropriate units
 * Dashboard cards: Use billions (bi) when >= 1000M, otherwise millions (M)
 * Municipal tables: Use thousands (mil) for better readability of small values
 */

export function formatCurrencyDashboard(value: number): string {
  // For values >= 1 billion, show in billions
  if (value >= 1_000_000_000) {
    return `R$ ${(value / 1_000_000_000).toFixed(1)} bi`
  } else if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)}M`
  } else if (value >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(0)} mil`
  } else {
    return `R$ ${value.toFixed(0)}`
  }
}

export function formatCurrencyTable(value: number): string {
  if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)}M`
  } else if (value >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(0)} mil`
  } else {
    return `R$ ${value.toFixed(0)}`
  }
}

/**
 * Format currency for municipal breakdown tables
 * Uses "mil" (thousands) to avoid misleading small values like "R$ 0.1M"
 */
export function formatCurrencyMunicipal(value: number): string {
  if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)}M`
  } else if (value >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(0)} mil`
  } else {
    return `R$ ${value.toFixed(0)}`
  }
}

/**
 * Legacy function - replaced by formatCurrencyDashboard
 * @deprecated Use formatCurrencyDashboard instead
 */
export function formatCurrency(value: number): string {
  return formatCurrencyDashboard(value)
}