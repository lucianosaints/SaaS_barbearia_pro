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
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-gold/20 bg-black/40 text-xs font-bold text-gold uppercase tracking-wider">
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
              const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
              
              const getFotoUrl = (path) => {
                  if (!path) return null;
                  if (path.startsWith('http')) return path;
                  return `${baseUrl}${path}`;
              };

              const clienteFoto = getFotoUrl(agendamento.cliente_foto);
              const barbeiroFoto = getFotoUrl(agendamento.profissional_foto);

              return (
                <tr key={agendamento.id} className="hover:bg-white/[0.03] transition-colors">
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
