import React from 'react';

export default function TermsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/85 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="terms-title">
      <div className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-background-paper shadow-2xl">
        <header className="flex items-start justify-between border-b border-white/10 p-5">
          <div><h2 id="terms-title" className="text-xl font-extrabold text-white">Termos de Uso e Aviso de Privacidade</h2><p className="mt-1 text-xs text-text-muted">Versão 1.0 — 24 de setembro de 2026</p></div>
          <button type="button" onClick={onClose} className="text-xl text-text-muted hover:text-white" aria-label="Fechar">✕</button>
        </header>
        <div className="space-y-5 overflow-y-auto p-6 text-sm leading-6 text-text-secondary">
          <section><h3 className="font-bold text-white">1. Serviço e aceitação</h3><p>O Salão PRO fornece recursos de agenda, gestão de clientes, equipe, comunicação e financeiro para estabelecimentos de beleza. Ao criar uma conta, o usuário declara ter capacidade para contratar, fornecer dados verdadeiros e usar o serviço de forma lícita.</p></section>
          <section><h3 className="font-bold text-white">2. Responsabilidades</h3><p>O usuário é responsável por proteger suas credenciais, manter seus dados atualizados e definir corretamente os acessos de sua equipe. É proibido usar a plataforma para fraude, violação de direitos, envio abusivo de mensagens ou tratamento ilícito de dados.</p></section>
          <section><h3 className="font-bold text-white">3. Dados tratados e finalidades</h3><p>Podemos tratar nome, e-mail, telefone, dados de acesso, empresa vinculada, agenda, serviços, pagamentos e registros técnicos para criar e administrar contas, executar agendamentos, enviar comunicações solicitadas, processar pagamentos, prevenir fraude, manter segurança, prestar suporte e cumprir obrigações legais.</p></section>
          <section><h3 className="font-bold text-white">4. Bases legais e papéis</h3><p>O tratamento poderá ocorrer para execução do contrato, cumprimento de obrigação legal ou regulatória, exercício regular de direitos, legítimo interesse com avaliação aplicável e consentimento quando exigido. Cada estabelecimento é responsável pelas decisões sobre os dados de seus clientes; o Salão PRO poderá atuar como operador segundo suas instruções e como controlador dos dados necessários à conta, cobrança, segurança e suporte.</p></section>
          <section><h3 className="font-bold text-white">5. Compartilhamento e armazenamento</h3><p>Dados podem ser compartilhados, no limite necessário, com provedores de hospedagem, banco de dados, e-mail, WhatsApp, pagamentos e suporte. Não vendemos dados pessoais. Os dados são mantidos pelo tempo necessário às finalidades informadas e aos prazos legais, com eliminação ou anonimização quando aplicável.</p></section>
          <section><h3 className="font-bold text-white">6. Segurança</h3><p>Adotamos medidas técnicas e administrativas razoáveis, incluindo controle de acesso, autenticação, registros de auditoria e backups. Nenhum ambiente é absolutamente invulnerável; incidentes relevantes serão tratados conforme a legislação.</p></section>
          <section><h3 className="font-bold text-white">7. Direitos do titular</h3><p>O titular pode solicitar confirmação e acesso, correção, anonimização, bloqueio ou eliminação quando cabível, portabilidade conforme regulamentação, informações sobre compartilhamento, revisão de decisões automatizadas e revogação de consentimento. Algumas informações poderão ser conservadas por obrigação legal ou exercício de direitos.</p></section>
          <section><h3 className="font-bold text-white">8. Comunicações e integrações</h3><p>Mensagens operacionais podem ser enviadas por e-mail ou WhatsApp para confirmações, lembretes e alertas. Integrações de terceiros também estão sujeitas às regras de seus respectivos fornecedores.</p></section>
          <section><h3 className="font-bold text-white">9. Disponibilidade e encerramento</h3><p>Podemos realizar manutenções e suspender usos que violem estes Termos. O usuário pode solicitar encerramento da conta, observadas cobranças, guarda legal e preservação de registros necessários.</p></section>
          <section><h3 className="font-bold text-white">10. Contato e alterações</h3><p>Solicitações sobre privacidade e exercício de direitos podem ser enviadas para <a className="text-gold hover:underline" href="mailto:infor@salaopro.site">infor@salaopro.site</a>. Alterações relevantes destes documentos serão comunicadas e uma nova concordância poderá ser solicitada.</p></section>
          <p className="rounded-xl border border-amber-400/20 bg-amber-400/10 p-3 text-xs text-amber-200">Este texto é uma base operacional alinhada aos princípios de transparência e direitos da LGPD e deve receber revisão jurídica considerando a empresa responsável, os fornecedores contratados e os fluxos reais de dados.</p>
        </div>
        <footer className="border-t border-white/10 p-4 text-right"><button type="button" onClick={onClose} className="btn-gold px-6 py-2">Fechar</button></footer>
      </div>
    </div>
  );
}
