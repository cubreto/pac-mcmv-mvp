/**
 * MCMV Dashboard v5 - Main Layout Component
 * Production-ready layout with navigation and responsive design
 */

import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useHealthCheck, useConfiguration } from '../api/hooks'
import GlobalFilters from './GlobalFilters'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { data: health } = useHealthCheck()
  const { data: config } = useConfiguration()

  const navigation = [
    { name: 'Resumo', href: '/', icon: '📊' },
    { name: 'RURAL', href: '/rural', icon: '🌾' },
    { name: 'FAR', href: '/far', icon: '🏗️' },
    { name: 'FDS', href: '/fds', icon: '🏘️' },
    { name: 'Dados Prioritários', href: '/dados-prioritarios', icon: '📋' },
    // { name: 'Qualidade', href: '/data-quality', icon: '📈' }, // Hidden for now
  ]

  // Check if we're on Dados Prioritários page
  const isDadosPrioritarios = location.pathname === '/dados-prioritarios'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16">
            {/* MCMV Logo */}
            <div className="flex items-center mr-12">
              <img 
                src="/mcmv-logo.png" 
                alt="Minha Casa Minha Vida" 
                className="h-12 w-auto"
              />
            </div>

            {/* Navigation */}
            <nav className="flex space-x-8 flex-1 justify-center">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <span className="mr-2">{item.icon}</span>
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            {/* Status indicator and Caixa Logo */}
            <div className="flex items-center space-x-4">
              {health?.status === 'healthy' ? (
                <div className="flex items-center text-green-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm">Online</span>
                </div>
              ) : (
                <div className="flex items-center text-red-600">
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                  <span className="text-sm">Offline</span>
                </div>
              )}
              {/* Caixa Logo */}
              <div className="border-l border-gray-300 pl-4 ml-4">
                <img 
                  src="/caixa-logo.png" 
                  alt="Caixa Econômica Federal" 
                  className="h-10 w-auto"
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Novo Minha Casa Minha Vida Banner - Not shown on Dados Prioritários */}
      {!isDadosPrioritarios && (
        <div className="bg-gradient-to-r from-blue-800 to-blue-600 text-white py-4 shadow-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-center">
              Novo Minha Casa Minha Vida
            </h2>
            <p className="text-center text-blue-100 text-sm mt-1">
              Programa Nacional de Habitação
            </p>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Global Filters Bar - Only show on Dashboard page */}
        {location.pathname === '/' && (
          <GlobalFilters />
        )}
        
        {/* Page Content */}
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <div>
              MCMV v5.0.6 - High-performance housing program analytics
            </div>
            <div className="flex items-center space-x-4">
              {config && (
                <span>
                  API v{config.api_version}
                </span>
              )}
              <a 
                href="http://54.90.170.181:8503" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800"
              >
                Compare with v4 →
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}