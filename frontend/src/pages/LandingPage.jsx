import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FiArrowUpRight, FiCalendar, FiCheck, FiCreditCard, FiMessageCircle, FiUsers, FiZap } from 'react-icons/fi';
import useAgendamentoStore from '../store/useAgendamentoStore';
import videoBackground from '../imagem/salao_pro.mp4';
import rafaelAvatar from '../imagem/depoimento-rafael.webp';
import julianaAvatar from '../imagem/depoimento-juliana.webp';
import marcosAvatar from '../imagem/depoimento-marcos.webp';
import OnboardingModal from '../components/OnboardingModal';
import AuthModal from '../components/AuthModal';
import TermsModal from '../components/TermsModal';

const benefits = [
  { icon: FiCalendar, title: 'Agenda que trabalha por você', text: 'Horários, bloqueios e fila de espera organizados em uma experiência simples para equipe e clientes.' },
  { icon: FiMessageCircle, title: 'WhatsApp no fluxo certo', text: 'Confirmações e lembretes automáticos mantêm sua agenda viva e reduzem as faltas.' },
  { icon: FiCreditCard, title: 'Financeiro sem planilhas', text: 'Acompanhe pagamentos, comissões e desempenho com números claros e prontos para decidir.' },
  { icon: FiUsers, title: 'Equipe em sintonia', text: 'Cada profissional enxerga sua rotina enquanto você mantém a visão completa da operação.' },
];

const proof = ['30 dias para experimentar', 'Configuração guiada', 'Feito para celular'];

const testimonials = [
  {
    initials: 'RM', avatar: rafaelAvatar, name: 'Rafael', business: 'Barbearia Central', time: '09:42',
    message: 'Cara, a agenda ficou muito mais organizada. Agora a equipe inteira sabe quem chega e em qual horário.',
    reply: 'E a fila de espera já ajudou por aí?',
    answer: 'Demais! Cancelou um horário ontem e em poucos minutos já entrou outro cliente. 🔥',
    color: 'from-cyan-400 to-blue-500',
  },
  {
    initials: 'JP', avatar: julianaAvatar, name: 'Juliana', business: 'Studio JP', time: '14:18',
    message: 'O que eu mais gostei foi enxergar o financeiro sem precisar abrir três planilhas diferentes.',
    reply: 'Ficou mais simples fechar o dia?',
    answer: 'Muito! Vejo pagamentos e comissões rapidinho pelo celular. Era exatamente o que eu precisava. 🙌',
    color: 'from-gold to-orange-400',
  },
  {
    initials: 'MS', avatar: marcosAvatar, name: 'Marcos', business: 'M7 Barber Club', time: '18:06',
    message: 'Meus clientes estão marcando sozinhos pelo link. Parou aquela troca infinita de mensagem pra achar horário.',
    reply: 'E o pessoal se adaptou bem?',
    answer: 'Na primeira semana já estavam usando. O painel é direto e fica ótimo no celular.',
    color: 'from-violet-400 to-fuchsia-500',
  },
];

export default function LandingPage() {
  const { setAuthModalOpen } = useAgendamentoStore();
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);

  return (
    <div className="min-h-screen overflow-hidden bg-background text-text-primary">
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-background-darker/70 backdrop-blur-2xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 lg:px-8">
          <button type="button" className="flex items-center gap-3" aria-label="Salão PRO - início">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white shadow-lg shadow-cyan-400/10">
              <img src="/logo.png" alt="" className="h-9 w-9 object-contain" />
            </span>
            <span className="text-lg font-extrabold tracking-tight">SALÃO<span className="text-gold">PRO</span></span>
          </button>
          <div className="flex items-center gap-2 sm:gap-4">
            <a href="#recursos" className="hidden text-sm font-semibold text-text-secondary transition hover:text-white sm:block">Recursos</a>
            <button onClick={() => setAuthModalOpen(true)} className="rounded-xl border border-white/15 bg-white/5 px-5 py-2.5 text-sm font-bold transition hover:border-white/30 hover:bg-white/10">Entrar</button>
          </div>
        </div>
      </nav>

      <main>
        <section className="relative flex min-h-[92vh] items-center pt-28">
          <video autoPlay loop muted playsInline className="absolute inset-0 h-full w-full object-cover opacity-25" src={videoBackground} />
          <div className="absolute inset-0 bg-[linear-gradient(90deg,#030914_8%,rgba(3,9,20,.94)_43%,rgba(3,9,20,.42)_100%)]" />
          <div className="absolute -right-24 top-32 h-80 w-80 rounded-full bg-cyan-400/20 blur-[110px]" />
          <div className="absolute left-1/3 top-2/3 h-72 w-72 rounded-full bg-gold/20 blur-[120px]" />

          <div className="relative mx-auto grid w-full max-w-7xl gap-12 px-5 pb-16 lg:grid-cols-[1.08fr_.92fr] lg:px-8">
            <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .65 }} className="max-w-3xl">
              <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-4 py-2 text-sm font-bold text-cyan-200">
                <FiZap /> Sua operação no ritmo do seu talento
              </div>
              <h1 className="text-5xl font-black leading-[.98] tracking-[-.055em] text-white sm:text-6xl lg:text-7xl xl:text-[5.4rem]">
                Agenda cheia.<br />Gestão <span className="bg-gradient-to-r from-gold via-orange-400 to-cyan-300 bg-clip-text text-transparent">leve.</span>
              </h1>
              <p className="mt-7 max-w-xl text-lg leading-8 text-text-secondary sm:text-xl">
                O Salão PRO conecta agenda, clientes, equipe e financeiro em um só lugar — bonito, rápido e fácil de usar.
              </p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <button onClick={() => setIsOnboardingOpen(true)} className="group inline-flex items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-gold to-accent-orange px-7 py-4 text-base font-extrabold text-white shadow-glow transition hover:-translate-y-1 hover:brightness-110">
                  Testar grátis por 30 dias <FiArrowUpRight className="transition group-hover:translate-x-1 group-hover:-translate-y-1" />
                </button>
                <button onClick={() => setAuthModalOpen(true)} className="rounded-2xl border border-white/15 bg-white/5 px-7 py-4 font-bold text-white backdrop-blur transition hover:bg-white/10">Já sou cliente</button>
              </div>
              <div className="mt-7 flex flex-wrap gap-x-6 gap-y-2 text-sm text-text-secondary">
                {proof.map(item => <span key={item} className="flex items-center gap-2"><FiCheck className="text-cyan-300" />{item}</span>)}
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, x: 35 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: .7, delay: .12 }} className="relative hidden items-end lg:flex">
              <div className="w-full rounded-[2rem] border border-white/15 bg-[#0b1728]/80 p-5 shadow-2xl backdrop-blur-xl">
                <div className="mb-5 flex items-center justify-between">
                  <div><p className="text-xs font-bold uppercase tracking-[.2em] text-cyan-300">Hoje</p><h2 className="mt-1 text-xl font-extrabold">Visão da agenda</h2></div>
                  <span className="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-bold text-emerald-300">Tudo em dia</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[['8','atendimentos'],['R$ 740','previstos'],['2','horários livres']].map(([value,label]) => <div key={label} className="rounded-2xl border border-white/10 bg-white/[.04] p-4"><strong className="block text-xl text-white">{value}</strong><span className="text-xs text-text-muted">{label}</span></div>)}
                </div>
                <div className="mt-4 space-y-3">
                  {[['09:00','Ana Paula','Corte + escova','bg-cyan-300'],['10:30','Rafael Lima','Corte masculino','bg-gold'],['13:00','Marina Costa','Coloração','bg-orange-400']].map(([time,name,service,color]) => <div key={time} className="flex items-center gap-4 rounded-2xl border border-white/10 bg-background-darker/55 p-4"><span className="w-12 text-sm font-black text-white">{time}</span><span className={`h-10 w-1 rounded-full ${color}`} /><div className="flex-1"><p className="font-bold text-white">{name}</p><p className="text-sm text-text-muted">{service}</p></div><span className="text-xs font-bold text-text-secondary">Confirmado</span></div>)}
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <section id="recursos" className="relative border-y border-white/10 bg-[#091629] py-24">
          <div className="mx-auto max-w-7xl px-5 lg:px-8">
            <div className="mb-12 grid gap-6 md:grid-cols-2 md:items-end">
              <div><span className="text-sm font-extrabold uppercase tracking-[.22em] text-gold">Menos ruído, mais resultado</span><h2 className="mt-4 text-4xl font-black tracking-tight text-white sm:text-5xl">Tudo o que move o seu negócio.</h2></div>
              <p className="max-w-xl text-lg leading-8 text-text-secondary md:justify-self-end">Do primeiro agendamento ao fechamento do dia, cada etapa fica mais clara para você, sua equipe e seus clientes.</p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {benefits.map(({ icon: Icon, title, text }, index) => <motion.article key={title} whileHover={{ y: -5 }} className="group rounded-[1.7rem] border border-white/10 bg-white/[.035] p-7 transition hover:border-white/20 hover:bg-white/[.06]">
                <div className="flex items-start gap-5"><span className={`grid h-14 w-14 shrink-0 place-items-center rounded-2xl ${index % 2 ? 'bg-gold/15 text-gold-light' : 'bg-cyan-300/15 text-cyan-200'}`}><Icon size={25} /></span><div><h3 className="text-xl font-extrabold text-white">{title}</h3><p className="mt-3 leading-7 text-text-secondary">{text}</p></div></div>
              </motion.article>)}
            </div>
          </div>
        </section>

        <section className="relative overflow-hidden px-5 py-24 lg:px-8">
          <div className="absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-400/10 blur-[130px]" />
          <div className="relative mx-auto max-w-7xl">
            <div className="mx-auto mb-12 max-w-3xl text-center">
              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-4 py-2 text-sm font-extrabold text-emerald-300">
                <FiMessageCircle /> Conversas que a gente gosta de receber
              </span>
              <h2 className="mt-5 text-4xl font-black tracking-tight text-white sm:text-5xl">Quando a rotina flui,<br />todo mundo percebe.</h2>
              <p className="mt-5 text-lg text-text-secondary">Exemplos ilustrativos de como o Salão PRO transforma o dia a dia de quem atende e administra.</p>
            </div>

            <div className="grid gap-5 lg:grid-cols-3">
              {testimonials.map((item, index) => (
                <motion.article
                  key={item.name}
                  initial={{ opacity: 0, y: 22 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: .25 }}
                  transition={{ delay: index * .1 }}
                  className="overflow-hidden rounded-[1.8rem] border border-white/10 bg-[#0a1726] shadow-2xl"
                >
                  <div className="flex items-center gap-3 border-b border-black/30 bg-[#202c33] px-5 py-4">
                    <span className={`h-11 w-11 shrink-0 overflow-hidden rounded-full bg-gradient-to-br ${item.color} p-[2px]`}>
                      <img src={item.avatar} alt={`Retrato ilustrativo de ${item.name}`} className="h-full w-full rounded-full object-cover" />
                    </span>
                    <div className="min-w-0 flex-1"><h3 className="font-extrabold text-white">{item.name}</h3><p className="truncate text-xs text-[#8696a0]">online · {item.business}</p></div>
                    <FiMessageCircle className="text-xl text-[#00a884]" />
                  </div>
                  <div className="wa-chat space-y-3 p-5">
                    <div className="wa-in max-w-[92%] rounded-lg rounded-tl-none bg-[#202c33] px-3.5 py-2.5 text-[15px] leading-[1.45] text-[#e9edef] shadow-md">
                      {item.message}<span className="ml-2 whitespace-nowrap text-[11px] text-[#8696a0]">{item.time}</span>
                    </div>
                    <div className="wa-out ml-auto max-w-[84%] rounded-lg rounded-tr-none bg-[#005c4b] px-3.5 py-2.5 text-[15px] leading-[1.45] text-[#e9edef] shadow-md">
                      {item.reply}<span className="ml-2 whitespace-nowrap text-[11px] text-[#90b8b0]">{item.time} <span className="font-bold text-[#53bdeb]">✓✓</span></span>
                    </div>
                    <div className="wa-in max-w-[92%] rounded-lg rounded-tl-none bg-[#202c33] px-3.5 py-2.5 text-[15px] leading-[1.45] text-[#e9edef] shadow-md">
                      {item.answer}<span className="ml-2 whitespace-nowrap text-[11px] text-[#8696a0]">{item.time}</span>
                    </div>
                  </div>
                </motion.article>
              ))}
            </div>
          </div>
        </section>

        <section className="px-5 py-24 lg:px-8">
          <div className="relative mx-auto max-w-7xl overflow-hidden rounded-[2.2rem] bg-gradient-to-br from-gold via-[#ed486a] to-[#8c3dce] px-6 py-16 text-center shadow-glow sm:px-12">
            <div className="absolute -left-20 -top-20 h-64 w-64 rounded-full border-[45px] border-white/10" />
            <div className="relative"><p className="text-sm font-black uppercase tracking-[.2em] text-white/75">R$ 49,99 por mês</p><h2 className="mx-auto mt-4 max-w-3xl text-4xl font-black tracking-tight text-white sm:text-5xl">Sua rotina pode ficar mais simples hoje.</h2><p className="mx-auto mt-5 max-w-2xl text-lg text-white/80">Experimente por 30 dias e veja sua operação ganhar ritmo, clareza e presença.</p><button onClick={() => setIsOnboardingOpen(true)} className="mt-8 inline-flex items-center gap-3 rounded-2xl bg-white px-7 py-4 font-extrabold text-[#761f55] shadow-xl transition hover:-translate-y-1">Criar minha conta <FiArrowUpRight /></button></div>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 px-5 py-8 text-sm text-text-muted"><div className="mx-auto flex max-w-7xl flex-col justify-between gap-4 sm:flex-row"><p>© {new Date().getFullYear()} Salão PRO · i9builder</p><div className="flex gap-5"><button type="button" onClick={() => setTermsOpen(true)} className="transition hover:text-white">Termos e Privacidade (LGPD)</button><a href="mailto:infor@salaopro.site" className="transition hover:text-white">infor@salaopro.site</a></div></div></footer>
      <OnboardingModal isOpen={isOnboardingOpen} onClose={() => setIsOnboardingOpen(false)} />
      <AuthModal />
      <TermsModal isOpen={termsOpen} onClose={() => setTermsOpen(false)} />
    </div>
  );
}
