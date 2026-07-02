import React, { useState } from 'react'
import useAgendamentoStore from './store/useAgendamentoStore'
import AdminDashboard from './pages/AdminDashboard'
import AgendamentoWizard from './pages/AgendamentoWizard'
import PainelCliente from './pages/PainelCliente'

function App() {
  const [currentTab, setCurrentTab] = useState('client') // 'client' ou 'admin'
  const { userToken, userNome, logout } = useAgendamentoStore()

  return (
    <div className="min-h-screen bg-background text-text-primary font-sans flex flex-col">
      {/* Barra de Navegação Superior */}
      <header className="bg-background-paper border-b border-white/5 sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span className="text-2xl">💈</span>
            <span className="font-extrabold tracking-wider bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">
              GOLDEN BARBER
            </span>
          </div>

          <div className="flex items-center gap-4">
            {userToken && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-text-secondary">Olá, <strong className="text-gold-light">{userNome}</strong></span>
                <button 
                  onClick={logout} 
                  className="text-rose-400 hover:text-rose-300 ml-1 font-semibold transition-colors"
                >
                  Sair
                </button>
              </div>
            )}

            <nav className="flex bg-background-darker border border-white/10 rounded-lg p-1 hidden sm:flex">
              <button
                onClick={() => setCurrentTab('client')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
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
                  className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
                    currentTab === 'client_dashboard'
                      ? 'bg-gold text-background'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Minha Agenda
                </button>
              )}
              <button
                onClick={() => setCurrentTab('admin')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  currentTab === 'admin'
                    ? 'bg-gold text-background'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                Painel Admin
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Área de Conteúdo Principal */}
      <main className="flex-1 flex flex-col justify-center">
        {currentTab === 'client' && <AgendamentoWizard />}
        {currentTab === 'client_dashboard' && <PainelCliente />}
        {currentTab === 'admin' && <AdminDashboard />}
      </main>

      {/* Rodapé institucional */}
      <footer className="text-center py-6 text-[10px] text-text-muted border-t border-white/5">
        &copy; 2026 Golden Barber SaaS. Todos os direitos reservados.
      </footer>
    </div>
  )
}

export default App

// Force Vite HMR reload
