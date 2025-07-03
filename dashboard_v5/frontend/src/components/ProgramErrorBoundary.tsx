/**
 * MCMV Dashboard v5 - Program-specific Error Boundary
 * Handles errors within program pages to prevent full app crashes
 */

import React, { Component, ReactNode } from 'react'

interface ProgramErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: string | null
}

interface ProgramErrorBoundaryProps {
  children: ReactNode
  programName: string
}

export class ProgramErrorBoundary extends Component<ProgramErrorBoundaryProps, ProgramErrorBoundaryState> {
  constructor(props: ProgramErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): ProgramErrorBoundaryState {
    return { hasError: true, error, errorInfo: null }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`${this.props.programName} page error:`, error, errorInfo)
    this.setState({
      error,
      errorInfo: errorInfo.componentStack || null
    })
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-96 flex items-center justify-center p-4">
          <div className="max-w-lg w-full bg-white rounded-lg shadow-lg border border-red-200 p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Erro na página {this.props.programName}
                </h3>
              </div>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Ocorreu um erro ao carregar os dados do programa {this.props.programName}. 
                Isso pode ser devido a filtros incompatíveis ou problemas temporários de conectividade.
              </p>
              
              {this.state.error && (
                <details className="mt-4">
                  <summary className="text-sm text-gray-500 cursor-pointer">
                    Detalhes técnicos do erro
                  </summary>
                  <div className="mt-2 p-3 bg-red-50 rounded border border-red-200">
                    <pre className="text-xs text-red-700 overflow-auto">
                      <strong>Error:</strong> {this.state.error.message}
                      {this.state.errorInfo && (
                        <>
                          <br /><br />
                          <strong>Component Stack:</strong>
                          <br />
                          {this.state.errorInfo}
                        </>
                      )}
                    </pre>
                  </div>
                </details>
              )}
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={this.handleRetry}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                🔄 Tentar novamente
              </button>
              
              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 transition-colors"
              >
                🏠 Voltar ao Dashboard
              </button>
            </div>
            
            <div className="mt-4 text-center">
              <a 
                href="http://54.90.170.181:8503" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                🔄 Usar versão anterior (v4) →
              </a>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}