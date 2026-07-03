import React, { useState } from 'react'
import useAgendamentoStore from './store/useAgendamentoStore'
import AdminDashboard from './pages/AdminDashboard'
import AgendamentoWizard from './pages/AgendamentoWizard'
import PainelCliente from './pages/PainelCliente'
import FinanceiroDashboard from './pages/FinanceiroDashboard'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import backgroundImg from './imagem/Background.jpg'

function App() {
  const [currentTab, setCurrentTab] = useState('client') // 'client' ou 'admin'
  const { userToken, userNome, userTipo, logout, setAuthModalOpen } = useAgendamentoStore()

  return (
    <div 
      className="min-h-screen bg-background text-text-primary font-sans flex flex-col"
      style={{
        backgroundImage: `linear-gradient(rgba(18, 18, 18, 0.88), rgba(18, 18, 18, 0.94)), url(${backgroundImg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
        backgroundRepeat: 'no-repeat',
      }}
    >
      {/* Barra de Navegação Superior */}
      <header className="bg-background-paper border-b border-white/5 sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col gap-3 sm:flex-row justify-between items-center">
          <div className="flex items-center gap-3">
            <span className="text-2xl">💈</span>
            <span className="font-extrabold tracking-wider bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent uppercase">
              Barbeiro_pro
            </span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
            {userToken ? (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-text-secondary">Olá, <strong className="text-gold-light">{userNome}</strong></span>
                <button 
                  onClick={logout} 
                  className="text-rose-400 hover:text-rose-300 ml-1 font-semibold transition-colors"
                >
                  Sair
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setAuthModalOpen(true)}
                className="btn-gold-outline px-3 py-1 text-xs rounded-md"
              >
                Entrar
              </button>
            )}

            <nav className="flex bg-background-darker border border-white/10 rounded-lg p-0.5 sm:p-1">
              <button
                onClick={() => setCurrentTab('client')}
                className={`px-2.5 sm:px-4 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold rounded-md transition-all ${
                  currentTab === 'client'
                    ? 'bg-gold text-background'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                Agendar
              </button>
              {userToken && (
                <button
                  onClick={() => setCurrentTab('client_dashboard')}
                  className={`px-2.5 sm:px-4 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold rounded-md transition-all ${
                    currentTab === 'client_dashboard'
                      ? 'bg-gold text-background'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Minha Agenda
                </button>
              )}
              {userToken && userTipo === 'ADMINISTRADOR' && (
                <button
                  onClick={() => setCurrentTab('admin')}
                  className={`px-2.5 sm:px-4 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold rounded-md transition-all ${
                    currentTab === 'admin'
                      ? 'bg-gold text-background'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Painel Admin
                </button>
              )}
              {userToken && userTipo === 'ADMINISTRADOR' && (
                <button
                  onClick={() => setCurrentTab('finance')}
                  className={`px-2.5 sm:px-4 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold rounded-md transition-all ${
                    currentTab === 'finance'
                      ? 'bg-gold text-background'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Financeiro
                </button>
              )}
              <button
                onClick={() => setCurrentTab('landing')}
                className={`px-2.5 sm:px-4 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold rounded-md transition-all ${
                  currentTab === 'landing'
                    ? 'bg-gold text-background'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                Vitrine SaaS
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Área de Conteúdo Principal */}
      <main className="flex-1 flex flex-col justify-start sm:justify-center py-4 sm:py-0">
        {currentTab === 'client' && <AgendamentoWizard />}
        {currentTab === 'client_dashboard' && <PainelCliente />}
        {currentTab === 'admin' && (
          <ProtectedRoute 
            allowedRoles={['ADMINISTRADOR', 'PROFISSIONAL']} 
            onDenied={() => setCurrentTab('client_dashboard')}
          >
            <AdminDashboard />
          </ProtectedRoute>
        )}
        {currentTab === 'finance' && (
          <ProtectedRoute 
            allowedRoles={['ADMINISTRADOR']} 
            onDenied={() => setCurrentTab('client_dashboard')}
          >
            <FinanceiroDashboard />
          </ProtectedRoute>
        )}
        {currentTab === 'landing' && <LandingPage />}
      </main>

      {/* Rodapé institucional */}
      <footer className="text-center py-6 text-[10px] text-text-muted border-t border-white/5">
        &copy; 2026 Barbeiro_pro SaaS. Todos os direitos reservados.
      </footer>
    </div>
  )
}

export default App

// Force Vite HMR reload
