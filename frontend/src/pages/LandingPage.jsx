import React, { useState } from 'react';
import { motion } from 'framer-motion';
import useAgendamentoStore from '../store/useAgendamentoStore';
import videoBackground from '../imagem/salao_pro.mp4';
import logoImg from '../imagem/logo.png';
import i9builderImg from '../imagem/i9builder.png';
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
              src="/logo.png" 
              alt="Salão PRO" 
              className="h-12 w-auto object-contain drop-shadow-[0_0_15px_rgba(212,175,55,0.3)]" 
            />
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
      <section className="relative w-full min-h-[80vh] flex items-center justify-center overflow-hidden">
        
        {/* Vídeo Background */}
        <video 
          autoPlay 
          loop 
          muted 
          playsInline 
          className="absolute top-0 left-0 w-full h-full object-cover z-0" 
          src={videoBackground}
        ></video>

        {/* Overlay Escuro */}
        <div className="absolute inset-0 bg-black/70 z-10"></div>

        {/* Glow Decorativo */}
        <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px] bg-gold/10 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none z-10"></div>

        {/* Conteúdo Centralizado */}
        <div className="relative z-20 container mx-auto px-6 text-center">
          <motion.div 
            className="space-y-8 max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gold/10 border border-gold/20 text-gold text-sm font-semibold mb-2 backdrop-blur-sm shadow-[0_0_15px_rgba(212,175,55,0.15)]">
              <span className="w-2 h-2 rounded-full bg-gold animate-pulse"></span>
              O sistema Definitivo para a sua Barbearia.
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-extrabold text-white leading-tight">
              A Gestão da sua Barbearia e Salão no <span className="bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent drop-shadow-sm">Próximo Nível.</span>
            </h1>
            
            <p className="text-lg lg:text-2xl text-gray-300 max-w-2xl mx-auto leading-relaxed drop-shadow">
              Agenda inteligente, comissionamento automático e controle financeiro na palma da sua mão. 
              Menos burocracia, mais lucro.
            </p>

            <div className="pt-8">
              <button 
                onClick={() => setIsOnboardingOpen(true)}
                className="px-10 py-5 rounded-2xl font-bold text-background-darker bg-gradient-to-r from-gold-light via-gold to-gold-dark hover:shadow-[0_0_35px_rgba(212,175,55,0.6)] transform hover:-translate-y-1 transition-all duration-300 text-lg md:text-xl"
              >
                Começar Teste Grátis de 30 Dias
              </button>
              <p className="text-sm text-gray-400 mt-5 font-medium drop-shadow">Preço justo: <strong className="text-gold">R$ 49,99/mês</strong></p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* 3. Features Section */}
      <section className="w-full bg-bg-secondary/50 py-24 border-y border-white/5 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-4xl mx-auto mb-16">
            <h2 className="text-3xl lg:text-5xl font-extrabold text-white mb-6">
              Muito mais que uma agenda. <br className="hidden md:block" />
              <span className="bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">O seu novo Gerente Digital.</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            
            {/* Card 1 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="bg-[#1a1a1a] p-8 rounded-2xl border border-white/5 hover:border-yellow-600 shadow-lg hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300 group"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h14M12 5v14M12 20a8 8 0 100-16 8 8 0 000 16z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-100 mb-3">Agenda Anti-Furos com Sniper de Desistências</h3>
              <p className="text-gray-400 leading-relaxed text-sm">
                Fim das cadeiras vazias. Nosso sistema de Fila de Espera Inteligente detecta cancelamentos e notifica automaticamente os próximos clientes da fila. O seu faturamento é protegido no piloto automático.
              </p>
            </motion.div>

            {/* Card 2 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="bg-[#1a1a1a] p-8 rounded-2xl border border-white/5 hover:border-yellow-600 shadow-lg hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300 group"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-100 mb-3">Link Exclusivo (Zero Concorrência)</h3>
              <p className="text-gray-400 leading-relaxed text-sm">
                Chega de marketplaces que mostram o seu cliente para o vizinho. Você recebe um link exclusivo de agendamento focado 100% na sua marca e nos seus serviços.
              </p>
            </motion.div>

            {/* Card 3 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="bg-[#1a1a1a] p-8 rounded-2xl border border-white/5 hover:border-yellow-600 shadow-lg hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300 group"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-100 mb-3">Material de Marketing Automático</h3>
              <p className="text-gray-400 leading-relaxed text-sm">
                Com apenas um clique no painel, o sistema gera uma placa em PDF com o seu QR Code exclusivo, pronta para imprimir e colocar na sua bancada ou recepção.
              </p>
            </motion.div>

            {/* Card 4 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="bg-[#1a1a1a] p-8 rounded-2xl border border-white/5 hover:border-yellow-600 shadow-lg hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300 group"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-100 mb-3">Financeiro e Comissionamento em Tempo Real</h3>
              <p className="text-gray-400 leading-relaxed text-sm">
                Aposente as planilhas complexas. O sistema calcula automaticamente as comissões, controla o status de pagamento (Pix/Cartão) e exibe o seu lucro líquido do dia na tela inicial.
              </p>
            </motion.div>

            {/* Card 5 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="bg-[#1a1a1a] p-8 rounded-2xl border border-white/5 hover:border-yellow-600 shadow-lg hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300 group"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-100 mb-3">Gestão de Equipe Avançada</h3>
              <p className="text-gray-400 leading-relaxed text-sm">
                Controle total sobre a sua barbearia. Crie perfis individuais para cada barbeiro, gerencie permissões de acesso e permita que cada profissional acompanhe sua própria agenda de forma privada.
              </p>
            </motion.div>

            {/* Card 6 */}
            <motion.div 
              whileHover={{ y: -5 }}
              className="bg-[#1a1a1a] p-8 rounded-2xl border border-white/5 hover:border-yellow-600 shadow-lg hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all duration-300 group"
            >
              <div className="w-14 h-14 rounded-xl bg-gold/10 text-gold flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-100 mb-3">Experiência Premium para o Cliente</h3>
              <p className="text-gray-400 leading-relaxed text-sm">
                Seus clientes terão acesso a um painel moderno e intuitivo no celular, onde podem visualizar horários marcados, histórico de cortes e cancelar agendamentos de forma rápida.
              </p>
            </motion.div>

          </div>
        </div>
      </section>

      {/* 3.5. Ideias e Sugestões */}
      <section className="w-full bg-bg-primary py-16 relative z-10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div 
            whileHover={{ scale: 1.01 }}
            className="bg-gradient-to-br from-[#1a1a1a] to-[#222222] p-10 md:p-14 rounded-3xl border border-gold/20 shadow-[0_0_30px_rgba(212,175,55,0.08)] relative overflow-hidden group transition-all duration-500"
          >
            {/* Efeitos de brilho */}
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-gold/20 blur-[50px] rounded-full pointer-events-none group-hover:bg-gold/30 transition-all duration-500"></div>
            <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-gold/10 blur-[50px] rounded-full pointer-events-none group-hover:bg-gold/20 transition-all duration-500"></div>
            
            <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-6 relative z-10">
              💡 Tem uma ideia para o seu negócio? <br className="hidden md:block mt-2" />
              <span className="bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">Nós desenvolvemos.</span>
            </h2>
            
            <p className="text-gray-300 text-lg mb-10 leading-relaxed max-w-2xl mx-auto relative z-10">
              O Salão PRO evolui com você! Se precisa de uma funcionalidade exclusiva para a sua barbearia, mande sua sugestão. A equipe de engenharia da i9builder avalia e implementa novas ferramentas para tornar sua gestão ainda mais eficiente.
            </p>
            
            <a 
              href="mailto:contato@i9builder.com?subject=Sugest%C3%A3o%20de%20Nova%20Funcionalidade%20-%20Sal%C3%A3o%20PRO&body=Ol%C3%A1%20equipe%20i9builder,%20gostaria%20de%20sugerir%20a%20seguinte%20funcionalidade:"
              onClick={() => {
                navigator.clipboard.writeText('contato@i9builder.com');
                alert('E-mail (contato@i9builder.com) copiado para a área de transferência!');
              }}
              className="inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl font-bold text-background-darker bg-gradient-to-r from-gold-light via-gold to-gold-dark hover:shadow-[0_0_25px_rgba(212,175,55,0.5)] transform hover:-translate-y-1 transition-all duration-300 relative z-10"
            >
              📩 Enviar Ideia por E-mail
            </a>
          </motion.div>
        </div>
      </section>

      {/* 4. Footer */}
      <footer className="w-full bg-bg-primary py-8 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          
          {/* Esquerda: Copyright */}
          <div className="flex items-center justify-center md:justify-start gap-3 text-text-muted text-sm text-center md:text-left">
            <img 
              src={i9builderImg} 
              alt="i9builder Logo" 
              className="w-8 h-8 rounded-full object-cover border border-white/10 shadow-sm" 
            />
            <p>
              Copyright © {new Date().getFullYear()} Salão Pro. <br className="md:hidden" />
              Todos os direitos reservados <span className="text-white font-semibold">i9builder</span>
            </p>
          </div>

          {/* Direita: Contato e LGPD */}
          <div className="flex flex-col md:flex-row items-center gap-4">
            
            {/* Badge LGPD */}
            <div className="flex items-center gap-2 text-text-muted text-xs bg-bg-secondary px-4 py-2.5 rounded-lg border border-white/5 whitespace-nowrap shadow-sm">
              <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Sistema de acordo com a LGPD</span>
            </div>

            {/* Contato i9builder */}
            <a href="mailto:infor@salaopro.site" className="flex items-center gap-2 text-gold hover:text-gold-light text-sm transition-colors group bg-gold/5 px-4 py-2.5 rounded-lg border border-gold/10 hover:bg-gold/10 whitespace-nowrap shadow-sm">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span className="font-semibold">infor@salaopro.site</span>
            </a>

          </div>
          
        </div>
      </footer>

      {/* Modal de Registro do SaaS */}
      <OnboardingModal isOpen={isOnboardingOpen} onClose={() => setIsOnboardingOpen(false)} />

      {/* Modal de Autenticação */}
      <AuthModal />
    </div>
  );
}
