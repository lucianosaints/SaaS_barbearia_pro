import React from 'react';
import { FiCalendar } from 'react-icons/fi';
import { BsCashCoin } from 'react-icons/bs';

export default function ClientAgendaCard({ agendamento, isFuturo, onCancel }) {
  const data = new Date(agendamento.data_hora_inicio);
  const dataFormatada = data.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
  const horaFormatada = data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  
  const detalhes = agendamento.servicos_detalhes || [];
  const nomesServicos = detalhes.map(s => s.nome).join(', ') || 'Serviços não listados';
  const valorTotal = detalhes.reduce((acc, curr) => acc + parseFloat(curr.preco), 0);

  const obterUrlImagem = (urlOriginal) => {
    if (!urlOriginal) return null;
    if (urlOriginal.includes('backend:8000') || urlOriginal.includes('localhost:8000')) {
      return urlOriginal.replace(/http:\/\/backend:8000|http:\/\/localhost:8000/, 'https://salaopro.site');
    }
    if (urlOriginal.startsWith('/media/')) {
      return `https://salaopro.site${urlOriginal}`;
    }
    return urlOriginal;
  };

  const profissionalFoto = obterUrlImagem(agendamento.profissional_foto);

  const formatMoeda = (valor) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor || 0);
  };

  // Status Badge Logic
  const renderStatusBadge = (status) => {
    switch (status) {
      case 'CONFIRMADO':
        return <span className="px-3 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-green-500/20 text-green-400 border border-green-500/30">Confirmado</span>;
      case 'PENDENTE':
        return <span className="px-3 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-orange-500/20 text-orange-400 border border-orange-500/30">Pendente</span>;
      case 'CONCLUIDO':
        return <span className="px-3 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-gray-500/20 text-gray-300 border border-gray-500/30">Concluído</span>;
      case 'CANCELADO':
        return <span className="px-3 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">Cancelado</span>;
      default:
        return <span className="px-3 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/30">{status}</span>;
    }
  };

  const isCancelado = agendamento.status === 'CANCELADO';

  return (
    <div className={`flex flex-col bg-[#1a1a1a] rounded-xl border transition-colors shadow-lg shadow-black/20 ${
      isCancelado ? 'border-white/5 opacity-60' : 'border-gray-800 hover:border-yellow-600'
    }`}>
      
      {/* Cabeçalho */}
      <div className="flex justify-between items-center p-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <FiCalendar className="text-gray-400" size={16} />
          <span className="text-gray-300 text-sm font-medium capitalize">{dataFormatada}</span>
          <span className="text-gold font-bold text-lg border-l border-white/20 pl-2 ml-1">
            {horaFormatada}
          </span>
        </div>
        <div>
          {renderStatusBadge(agendamento.status)}
        </div>
      </div>

      {/* Corpo */}
      <div className="p-4 flex flex-col gap-3">
        <h3 className="text-lg font-bold text-white tracking-tight">{nomesServicos}</h3>
        
        <div className="flex items-center justify-between mt-1">
          <div className="flex items-center gap-2">
            <img 
              src={profissionalFoto || `https://ui-avatars.com/api/?name=${agendamento.profissional_nome || 'Barbeiro'}&background=333&color=fbbf24`} 
              alt="Profissional" 
              className="w-6 h-6 rounded-full object-cover border border-gold/50"
            />
            <span className="text-gray-400 text-sm">{agendamento.profissional_nome || 'Barbeiro'}</span>
          </div>
          
          <div className="flex items-center gap-1.5 bg-black/40 px-2.5 py-1 rounded-md border border-gold/20">
            <BsCashCoin className="text-gold" size={14} />
            <span className="text-gold font-bold text-sm">{formatMoeda(valorTotal)}</span>
          </div>
        </div>
      </div>

      {/* Rodapé */}
      <div className="p-3 border-t border-gray-800 bg-black/20 flex justify-end">
        {isFuturo && !isCancelado ? (
          <button
            onClick={() => onCancel(agendamento.id)}
            className="w-full sm:w-auto px-4 py-2 rounded-lg text-xs font-bold transition-all text-gray-400 border border-gray-700 hover:bg-rose-500/10 hover:text-rose-400 hover:border-rose-500/50"
          >
            CANCELAR AGENDAMENTO
          </button>
        ) : (
          agendamento.empresa_slug && (
            <a
              href={`/agendar/${agendamento.empresa_slug}`}
              className="w-full sm:w-auto px-4 py-2 rounded-lg text-xs font-bold transition-all bg-transparent text-gold border border-gold/30 hover:bg-gold/10 text-center block"
            >
              AGENDAR NOVAMENTE
            </a>
          )
        )}
      </div>
    </div>
  );
}
