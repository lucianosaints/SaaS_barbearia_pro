import React, { useState } from 'react';
import { motion } from 'framer-motion';
import useAgendamentoStore from '../store/useAgendamentoStore';
import heroImage from '../imagem/Image 3.png';
import logoImg from '../imagem/logo.png';
import OnboardingModal from '../components/OnboardingModal';
import AuthModal from '../components/AuthModal';

export default function LandingPage() {
  const { setAuthModalOpen } = useAgendamentoStore();
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);

  return (
    <div className="min-h-screen bg-bg-primary font-sans text-text-primary selection:bg-gold/30">
      
      {/* 1. Navigation Bar */}
      <nav className="w-full border-b border-white/5 bg-bg-primary/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <img 
              src={logoImg} 
              alt="Ícone Barbeiro_Pro" 
              className="w-10 h-10 rounded-full object-cover border-2 border-gold shadow-[0_0_15px_rgba(212,175,55,0.3)]" 
            />
            <span className="text-xl font-bold tracking-wide text-white uppercase">
              Barbeiro_<span className="text-gold">Pro</span>
            </span>
          </div>

          {/* Botão Entrar */}
          <div>
            <button
              onClick={() => setAuthModalOpen(true)}
              className="px-6 py-2 rounded-full font-medium text-text-secondary hover:text-white border border-white/10 hover:border-gold/50 hover:bg-gold/10 transition-all duration-300"
            >
              Entrar
            </button>
          </div>
        </div>
      </nav>

      {/* 2. Hero Section */}
      <section className="relative w-full max-w-7xl mx-auto px-6 py-20 lg:py-32 flex flex-col lg:flex-row items-center gap-12 lg:gap-20">
        
        {/* Glow de fundo para dar um toque premium */}
        <div className="absolute top-1/2 left-1/4 w-[500px] h-[500px] bg-gold/5 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>

        {/* Texto (Lado Esquerdo) */}
        <motion.div 
          className="flex-1 space-y-8 z-10 text-center lg:text-left"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gold/10 border border-gold/20 text-gold text-sm font-semibold mb-2">
            <span className="w-2 h-2 rounded-full bg-gold animate-pulse"></span>
            O sistema Definitivo para a sua Barbearia.
          </div>
          
          <h1 className="text-5xl lg:text-6xl font-extrabold text-white leading-tight">
            A Gestão da sua Barbearia no <span className="bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">Próximo Nível.</span>
          </h1>
          
          <p className="text-lg lg:text-xl text-text-secondary max-w-xl mx-auto lg:mx-0 leading-relaxed">
            Agenda inteligente, comissionamento automático e controle financeiro na palma da sua mão. 
            Menos burocracia, mais lucro.
          </p>

          <div className="pt-4">
            <button 
              onClick={() => setIsOnboardingOpen(true)}
              className="px-8 py-4 rounded-xl font-bold text-background-darker bg-gradient-to-r from-gold-light via-gold to-gold-dark hover:shadow-[0_0_25px_rgba(212,175,55,0.5)] transform hover:-translate-y-1 transition-all duration-300 text-lg"
            >
              Começar Teste Grátis de 7 Dias
            </button>
            <p className="text-xs text-text-muted mt-4">Preço justo: <strong className="text-gold">R$ 49,99/mês</strong></p>
          </div>
        </motion.div>

        {/* Imagem (Lado Direito) */}
        <motion.div 
          className="flex-1 w-full max-w-lg lg:max-w-none relative z-10"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          {/* Imagem Premium */}
          <div className="relative aspect-square md:aspect-[4/3] lg:aspect-square w-full rounded-3xl bg-bg-secondary border border-white/5 shadow-2xl overflow-hidden group">
            <img 
              src={heroImage} 
              alt="Gestão de Barbearia Profissional" 
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" 
            />
            
            {/* Decoração interna simulando reflexo/vidro */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-black/40 pointer-events-none"></div>
            
            {/* Bordas decorativas */}
            <div className="absolute -inset-px rounded-3xl border border-gold/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
          </div>
        </motion.div>
      </section>

      {/* 3. Features Section */}
      <section className="w-full bg-bg-secondary/50 py-24 border-y border-white/5 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-6">
              Tudo o que você precisa para focar no que importa: <span className="text-gold">o corte.</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Card 1 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="card-premium bg-bg-secondary p-8 rounded-2xl border border-white/5 shadow-lg hover:border-gold/30 hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Agenda Anti-Furos</h3>
              <p className="text-text-secondary leading-relaxed text-sm">
                Notificações automáticas para clientes, gestão inteligente de horários e liberação rápida de vagas caso haja desistências.
              </p>
            </motion.div>

            {/* Card 2 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="card-premium bg-bg-secondary p-8 rounded-2xl border border-white/5 shadow-lg hover:border-gold/30 hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Financeiro Automático</h3>
              <p className="text-text-secondary leading-relaxed text-sm">
                Cálculo de comissões preciso, faturamento em tempo real e visualização de lucro líquido. Chega de planilhas complexas.
              </p>
            </motion.div>

            {/* Card 3 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="card-premium bg-bg-secondary p-8 rounded-2xl border border-white/5 shadow-lg hover:border-gold/30 hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Gestão de Equipe</h3>
              <p className="text-text-secondary leading-relaxed text-sm">
                Perfis individuais para barbeiros, controle avançado de permissões de acesso e fechamento de caixa independente.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* 4. Footer */}
      <footer className="w-full bg-bg-primary py-8 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 flex justify-center">
          <p className="text-text-muted text-sm text-center">
            Copyright © {new Date().getFullYear()} Barbeiro_Pro. Todos os direitos reservados i9builder @luciano.saints
          </p>
        </div>
      </footer>

      {/* Modal de Registro do SaaS */}
      <OnboardingModal isOpen={isOnboardingOpen} onClose={() => setIsOnboardingOpen(false)} />

      {/* Modal de Autenticação */}
      <AuthModal />
    </div>
  );
}
