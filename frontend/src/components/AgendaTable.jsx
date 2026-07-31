import React from 'react';
import { FiEdit2, FiClock, FiTrash2 } from 'react-icons/fi';
import { FaWhatsapp, FaCut, FaCreditCard, FaRegCreditCard } from 'react-icons/fa';
import { MdOutlinePix } from 'react-icons/md';
import { BsCashCoin } from 'react-icons/bs';

export default function AgendaTable({ agendamentos, onEdit, onCancel }) {
  // Formatters
  const formatTime = (dateStr) => {
    if (!dateStr) return '-';
    const data = new Date(dateStr);
    return data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const data = new Date(dateStr);
    return data.toLocaleDateString('pt-BR');
  };

  const formatMoeda = (valor) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor || 0);
  };

  const calculateDuration = (inicio, fim) => {
    if (!inicio || !fim) return '-';
    const diff = new Date(fim) - new Date(inicio);
    return Math.floor(diff / 60000) + ' min';
  };

  // Status Badge Logic
  const renderStatusBadge = (status) => {
    switch (status) {
      case 'CONFIRMADO':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-green-500/20 text-green-400">Confirmado</span>;
      case 'PENDENTE':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-orange-500/20 text-orange-400">Pendente</span>;
      case 'CONCLUIDO':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-gray-500/20 text-gray-300">Concluído</span>;
      case 'CANCELADO':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-red-500/20 text-red-400">Cancelado</span>;
      default:
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-gray-500/20 text-gray-400">{status}</span>;
    }
  };

  // Payment UI
  const renderPayment = (metodo, status) => {
    let Icon = BsCashCoin;
    let color = 'text-gray-400';
    if (metodo === 'PIX') { Icon = MdOutlinePix; color = 'text-green-400'; }
    if (metodo === 'CREDITO') { Icon = FaCreditCard; color = 'text-gold'; }
    if (metodo === 'DEBITO') { Icon = FaRegCreditCard; color = 'text-blue-400'; }
    
    const isPaid = status === 'PAGO';
    
    return (
      <div className="flex items-center gap-2">
        <Icon className={color} size={18} />
        <span className={`text-xs font-semibold ${isPaid ? 'text-green-400' : 'text-orange-400'}`}>
          {isPaid ? 'Pago' : 'Pendente'}
        </span>
      </div>
    );
  };

  // Calculations for Footer
  const totalAgendamentos = agendamentos?.length || 0;
  const totalVendas = agendamentos?.reduce((acc, curr) => acc + parseFloat(curr.valor_total || 0), 0) || 0;

  if (!agendamentos || agendamentos.length === 0) {
    return (
      <div className="bg-[#1a1a1a] border border-gold/30 rounded-xl p-8 text-center text-gray-400">
        Nenhum agendamento encontrado para os filtros selecionados.
      </div>
    );
  }

  return (
    <div className="bg-[#1a1a1a] border border-gold/30 rounded-xl overflow-hidden shadow-2xl">
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-gold/20 bg-black/40 text-xs font-bold text-gold uppercase tracking-wider">
              <th className="px-6 py-4">Data</th>
              <th className="px-6 py-4">Horário</th>
              <th className="px-6 py-4">Cliente</th>
              <th className="px-6 py-4">Serviço</th>
              <th className="px-6 py-4">Barbeiro</th>
              <th className="px-6 py-4">Duração</th>
              <th className="px-6 py-4">Pagamento</th>
              <th className="px-6 py-4">Valor</th>
              <th className="px-6 py-4 text-center">Status</th>
              <th className="px-6 py-4 text-center">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-sm text-gray-200">
            {agendamentos.map((agendamento) => {
              const servicos = agendamento.servicos_detalhes || [];
              const obterUrlImagem = (urlOriginal) => {
                if (!urlOriginal) return null;
                // Se a URL apontar para o host interno do Docker, corrige para o domínio público
                if (urlOriginal.includes('backend:8000') || urlOriginal.includes('localhost:8000')) {
                  return urlOriginal.replace(/http:\/\/backend:8000|http:\/\/localhost:8000/, 'https://salaopro.site');
                }
                // Se a URL for relativa (começar apenas com /media/ ou /arquivos/), adiciona o domínio público na frente
                if (urlOriginal.startsWith('/media/') || urlOriginal.startsWith('/arquivos/')) {
                  return `https://salaopro.site${urlOriginal}`;
                }
                return urlOriginal;
              };

              const clienteFoto = obterUrlImagem(agendamento.cliente_foto);
              const barbeiroFoto = obterUrlImagem(agendamento.profissional_foto);

              return (
                <tr key={agendamento.id} className="hover:bg-white/[0.03] transition-colors">
                  {/* Data */}
                  <td className="px-6 py-4 font-bold text-md text-gray-300">
                    {formatDate(agendamento.data_hora_inicio)}
                  </td>
                  
                  {/* Horário */}
                  <td className="px-6 py-4 font-bold text-lg text-white">
                    {formatTime(agendamento.data_hora_inicio)}
                  </td>
                  
                  {/* Cliente */}
                  <td className="px-6 py-4">
                    <div className="flex flex-col items-start gap-2">
                      <img 
                        src={clienteFoto || `https://ui-avatars.com/api/?name=${agendamento.cliente_nome || 'Cliente'}&background=333&color=fbbf24`} 
                        alt="Cliente" 
                        className="w-8 h-8 rounded-full object-cover border border-gold/50"
                      />
                      <span className="font-semibold">{agendamento.cliente_nome || 'Cliente'}</span>
                    </div>
                  </td>
                  
                  {/* Serviço */}
                  <td className="px-6 py-4">
                    <div className="flex flex-col items-start gap-1">
                      <FaCut className="text-gold mb-1" size={16} />
                      <div className="max-w-[150px] truncate text-gray-300">
                        {servicos.length > 0 ? servicos.map(s => s.nome).join(', ') : 'Serviço'}
                      </div>
                    </div>
                  </td>

                  {/* Barbeiro */}
                  <td className="px-6 py-4">
                    <div className="flex flex-col items-start gap-2">
                      <img 
                        src={barbeiroFoto || `https://ui-avatars.com/api/?name=${agendamento.profissional_nome || 'Barbeiro'}&background=333&color=fbbf24`} 
                        alt="Barbeiro" 
                        className="w-8 h-8 rounded-full object-cover border border-gold/50"
                      />
                      <span className="text-gray-300">{agendamento.profissional_nome || 'Barbeiro'}</span>
                    </div>
                  </td>

                  {/* Duração */}
                  <td className="px-6 py-4 text-gray-400 font-medium">
                    <div className="flex items-center gap-2">
                      <FiClock /> {calculateDuration(agendamento.data_hora_inicio, agendamento.data_hora_fim)}
                    </div>
                  </td>

                  {/* Pagamento */}
                  <td className="px-6 py-4">
                    {renderPayment(agendamento.metodo_pagamento, agendamento.status_pagamento)}
                  </td>

                  {/* Valor */}
                  <td className="px-6 py-4 font-bold text-gold">
                    {formatMoeda(agendamento.valor_total)}
                  </td>

                  {/* Status */}
                  <td className="px-6 py-4 text-center">
                    {renderStatusBadge(agendamento.status)}
                  </td>

                  {/* Ações */}
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center gap-3">
                      <button 
                        onClick={() => onEdit && onEdit(agendamento)}
                        className="p-2 rounded-full hover:bg-gold/20 text-gold transition-colors"
                        title="Editar"
                      >
                        <FiEdit2 size={16} />
                      </button>

                      
                      {agendamento.cliente_telefone && (
                        <a 
                          href={`https://wa.me/55${agendamento.cliente_telefone.replace(/\D/g,'')}`}
                          target="_blank"
                          rel="noreferrer"
                          className="p-2 rounded-full bg-green-500 hover:bg-green-400 text-white shadow-lg shadow-green-500/30 transition-all"
                          title="WhatsApp"
                        >
                          <FaWhatsapp size={16} />
                        </a>
                      )}
                      
                      {agendamento.status !== 'CANCELADO' && agendamento.status !== 'CONCLUIDO' && onCancel && (
                        <button 
                          onClick={() => onCancel(agendamento)}
                          className="p-2 rounded-full hover:bg-red-500/20 text-red-500 transition-colors ml-2"
                          title="Cancelar Agendamento"
                        >
                          <FiTrash2 size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Visão Mobile: Cards */}
      <div className="block sm:hidden p-4 space-y-4 bg-background">
        {agendamentos.map((agendamento) => {
          const data = new Date(agendamento.data_hora_inicio);
          const dataFormatada = data.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
          const horaFormatada = data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
          
          const servicos = agendamento.servicos_detalhes || [];
          const nomesServicos = servicos.length > 0 ? servicos.map(s => s.nome).join(', ') : 'Serviços não listados';
          
          const obterUrlImagem = (urlOriginal) => {
            if (!urlOriginal) return null;
            if (urlOriginal.includes('backend:8000') || urlOriginal.includes('localhost:8000')) {
              return urlOriginal.replace(/http:\/\/backend:8000|http:\/\/localhost:8000/, 'https://salaopro.site');
            }
            if (urlOriginal.startsWith('/media/') || urlOriginal.startsWith('/arquivos/')) {
              return `https://salaopro.site${urlOriginal}`;
            }
            return urlOriginal;
          };
          
          const clienteFoto = obterUrlImagem(agendamento.cliente_foto);
          const isCancelado = agendamento.status === 'CANCELADO';

          return (
            <div key={agendamento.id} className={`flex flex-col bg-[#1a1a1a] rounded-xl border transition-colors shadow-lg shadow-black/20 ${isCancelado ? 'border-white/5 opacity-60' : 'border-gray-800'}`}>
              
              {/* Cabeçalho do Card */}
              <div className="flex justify-between items-center p-4 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <FiClock className="text-gray-400" size={16} />
                  <span className="text-gray-300 text-sm font-medium capitalize">{dataFormatada}</span>
                  <span className="text-gold font-bold text-lg border-l border-white/20 pl-2 ml-1">
                    {horaFormatada}
                  </span>
                </div>
                <div>
                  {renderStatusBadge(agendamento.status)}
                </div>
              </div>

              {/* Corpo do Card */}
              <div className="p-4 flex flex-col gap-3">
                <div className="flex items-center gap-3 mb-2">
                  <img 
                    src={clienteFoto || `https://ui-avatars.com/api/?name=${agendamento.cliente_nome || 'Cliente'}&background=333&color=fbbf24`} 
                    alt="Cliente" 
                    className="w-10 h-10 rounded-full object-cover border border-gold/50"
                  />
                  <div>
                    <h4 className="font-bold text-white text-base leading-tight">{agendamento.cliente_nome || 'Cliente'}</h4>
                    <p className="text-xs text-gray-400">Atendido por: <strong className="text-gray-300">{agendamento.profissional_nome || 'Barbeiro'}</strong></p>
                  </div>
                </div>

                <div className="flex flex-col gap-1">
                  <h3 className="text-sm font-semibold text-gray-300 tracking-tight flex items-center gap-1.5">
                    <FaCut className="text-gold" size={14} /> 
                    <span className="truncate">{nomesServicos}</span>
                  </h3>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                     <FiClock size={12} /> {calculateDuration(agendamento.data_hora_inicio, agendamento.data_hora_fim)}
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-2 pt-3 border-t border-white/5">
                  <div className="flex items-center gap-1.5">
                    {renderPayment(agendamento.metodo_pagamento, agendamento.status_pagamento)}
                  </div>
                  
                  <div className="flex items-center gap-1.5 bg-black/40 px-2.5 py-1 rounded-md border border-gold/20">
                    <span className="text-gold font-bold text-sm">{formatMoeda(agendamento.valor_total)}</span>
                  </div>
                </div>
              </div>

              {/* Rodapé (Ações) */}
              <div className="p-3 border-t border-gray-800 bg-black/20 flex justify-between items-center rounded-b-xl">
                <button 
                  onClick={() => onEdit && onEdit(agendamento)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all text-gold border border-gold/30 hover:bg-gold/10"
                >
                  <FiEdit2 size={14} /> Editar
                </button>

                <div className="flex gap-2">
                  {agendamento.cliente_telefone && (
                    <a 
                      href={`https://wa.me/55${agendamento.cliente_telefone.replace(/\D/g,'')}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-green-500 hover:bg-green-400 text-white shadow-lg shadow-green-500/30"
                    >
                      <FaWhatsapp size={14} /> Whats
                    </a>
                  )}
                  
                  {agendamento.status !== 'CANCELADO' && agendamento.status !== 'CONCLUIDO' && onCancel && (
                    <button 
                      onClick={() => onCancel(agendamento)}
                      className="p-1.5 rounded-lg border border-red-500/30 text-red-500 hover:bg-red-500/10 transition-colors"
                      title="Cancelar"
                    >
                      <FiTrash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="bg-black/60 border-t border-gold/20 px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="text-gray-400 text-sm font-medium">
          Mostrando {totalAgendamentos} agendamento(s)
        </div>
        <div className="text-gray-300 text-sm font-bold bg-black/40 px-4 py-2 rounded-lg border border-gold/10">
          Total de Vendas Hoje: <span className="text-gold text-lg ml-2">{formatMoeda(totalVendas)}</span>
        </div>
      </div>
    </div>
  );
}
