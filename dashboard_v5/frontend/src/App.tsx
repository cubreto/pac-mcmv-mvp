/**
 * MCMV Dashboard v5 - Main App Component
 * Modern React dashboard with performance optimization
 */

import React, { Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { ErrorBoundary } from 'react-error-boundary'

import { Layout } from './components/Layout'
import { LoadingSpinner } from './components/LoadingSpinner'
import { ErrorFallback } from './components/ErrorFallback'
import { FilterProvider } from './contexts/FilterContext'

// Lazy load pages for code splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'))
const ProgramPage = React.lazy(() => import('./pages/ProgramPage'))
const DataQuality = React.lazy(() => import('./pages/DataQuality'))
const RuralPage = React.lazy(() => import('./pages/RuralPage'))
const FARPage = React.lazy(() => import('./pages/FARPage'))
const FDSPage = React.lazy(() => import('./pages/FDSPage'))
const DadosPrioritariosPage = React.lazy(() => import('./pages/DadosPrioritariosPage'))

function App() {
  return (
    <FilterProvider>
      <ErrorBoundary
        FallbackComponent={ErrorFallback}
        onError={(error, errorInfo) => {
          console.error('App Error:', error, errorInfo)
        }}
      >
        <Layout>
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/program/:programa" element={<ProgramPage />} />
              <Route path="/rural" element={<RuralPage />} />
              <Route path="/far" element={<FARPage />} />
              <Route path="/fds" element={<FDSPage />} />
              <Route path="/dados-prioritarios" element={<DadosPrioritariosPage />} />
              <Route path="/data-quality" element={<DataQuality />} />
              <Route path="*" element={<Dashboard />} />
            </Routes>
          </Suspense>
        </Layout>
      </ErrorBoundary>
    </FilterProvider>
  )
}

export default App