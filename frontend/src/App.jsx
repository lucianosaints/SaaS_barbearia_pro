import React, { useState, useEffect } from 'react'
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import useAgendamentoStore from './store/useAgendamentoStore'
import AdminDashboard from './pages/AdminDashboard'
import AgendamentoWizard from './pages/AgendamentoWizard'
import PainelCliente from './pages/PainelCliente'
import FinanceiroDashboard from './pages/FinanceiroDashboard'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import Assinatura from './pages/Assinatura'
import backgroundImg from './imagem/Background.jpg'
import i9builderImg from './imagem/i9builder.png'

import logoImg from './imagem/logo.png'
import WhatsAppButton from './components/WhatsAppButton'

function App() {
  const [currentTab, setCurrentTab] = useState('landing') // 'landing' por padrão para visitantes
  const { userToken, userNome, userTipo, userEmpresa, logout, setAuthModalOpen } = useAgendamentoStore()

  const location = useLocation();
  const navigate = useNavigate();

  // Redireciona para a landing page se logout, ou para o dashboard se login
  useEffect(() => {
    if (location.pathname.startsWith('/agendar/') || location.pathname.startsWith('/admin/assinatura')) {
       // Se estiver na rota de agendamento ou assinatura, não força a aba landing.
       return;
    }
    if (!userToken) {
      setCurrentTab('landing');
    } else if (currentTab === 'landing') {
      // Quando logar a partir da landing page, redireciona para a aba correta
      if (userTipo === 'ADMINISTRADOR' || userTipo === 'PROFISSIONAL') {
        setCurrentTab('admin');
      } else {
        setCurrentTab('client_dashboard');
      }
    }
  }, [userToken, userTipo, location.pathname]);

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
      {/* Barra de Navegação Superior (Oculta na Landing Page e na tela de Agendamento Pública) */}
      {(currentTab !== 'landing' || userToken) && (
        <header className="bg-background-paper border-b border-white/5 sticky top-0 z-50 px-6 py-4">
          <div className="max-w-7xl mx-auto flex flex-col gap-3 sm:flex-row justify-between items-center">
            <div className="flex items-center gap-3">
              <img 
                src="/logo.png" 
                alt="Salão PRO" 
                className="h-10 sm:h-12 w-auto object-contain drop-shadow-[0_0_15px_rgba(212,175,55,0.3)]" 
              />
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

            <nav className="flex flex-wrap justify-center bg-background-darker border border-white/10 rounded-lg p-1 sm:p-1 gap-1">
              {/* Visitante não logado */}
              {!userToken && (
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
              )}

              {/* Botões Comuns para Administradores/Profissionais */}
              {userToken && (userTipo === 'ADMINISTRADOR' || userTipo === 'PROFISSIONAL') && userEmpresa && userEmpresa.slug && (
                <button
                  onClick={() => window.open(`/agendar/${userEmpresa.slug}`, '_blank')}
                  className={`px-2.5 sm:px-4 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold rounded-md transition-all text-text-secondary hover:text-text-primary`}
                >
                  Ver Meu Agendamento
                </button>
              )}

              {/* Cliente */}
              {userToken && userTipo === 'CLIENTE' && (
                <button
                  onClick={() => {
                     // Em vez de mudar para tab 'client', que não existe mais para o genérico,
                     // a gente pode mandar pro dashboard de cliente.
                     setCurrentTab('client_dashboard');
                     navigate('/');
                  }}
                  className={`px-2.5 sm:px-4 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold rounded-md transition-all ${
                    currentTab === 'client_dashboard'
                      ? 'bg-gold text-background'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Minha Agenda
                </button>
              )}

              {/* Admin ou Profissional */}
              {userToken && (userTipo === 'ADMINISTRADOR' || userTipo === 'PROFISSIONAL') && (
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
            </nav>
          </div>
        </div>
      </header>
      )}

      <main className="flex-1 flex flex-col justify-start sm:justify-center py-4 sm:py-0">
        {location.pathname.startsWith('/agendar/') ? (
          <Routes>
            <Route path="/agendar/:empresaSlug" element={<AgendamentoWizard />} />
          </Routes>
        ) : location.pathname.startsWith('/admin/assinatura') ? (
          <Routes>
            <Route path="/admin/assinatura" element={<Assinatura />} />
          </Routes>
        ) : (
          <>
            {currentTab === 'client_dashboard' && (
              <ProtectedRoute 
                allowedRoles={['CLIENTE']} 
                onDenied={() => setCurrentTab('landing')}
              >
                <PainelCliente />
              </ProtectedRoute>
            )}
            {currentTab === 'admin' && (
              <ProtectedRoute 
                allowedRoles={['ADMINISTRADOR', 'PROFISSIONAL']} 
                onDenied={() => setCurrentTab(userToken ? 'client_dashboard' : 'landing')}
              >
                <AdminDashboard />
              </ProtectedRoute>
            )}
            {currentTab === 'finance' && (
              <ProtectedRoute 
                allowedRoles={['ADMINISTRADOR']} 
                onDenied={() => setCurrentTab(userToken ? 'admin' : 'landing')}
              >
                <FinanceiroDashboard />
              </ProtectedRoute>
            )}
            {currentTab === 'landing' && <LandingPage />}
          </>
        )}
      </main>

      {/* Rodapé institucional */}
      {(currentTab !== 'landing' || userToken) && (
        <footer className="py-4 flex items-center justify-center gap-3 text-xs text-text-muted border-t border-white/5 mt-auto">
          <img 
            src={i9builderImg} 
            alt="i9builder Logo" 
            className="w-8 h-8 rounded-full object-cover border border-white/10 shadow-sm" 
          />
          <span>&copy; {new Date().getFullYear()} Salão Pro. Todos os direitos reservados i9builder @luciano.saints</span>
        </footer>
      )}

      {/* Botão Flutuante do WhatsApp */}
      <WhatsAppButton />
    </div>
  )
}

export default App

// Force Vite HMR reload
