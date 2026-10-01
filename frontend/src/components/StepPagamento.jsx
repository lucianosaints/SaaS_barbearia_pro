import React from 'react';
import useAgendamentoStore from '../store/useAgendamentoStore';
import { MdOutlinePix } from 'react-icons/md';
import { BsCashCoin } from 'react-icons/bs';
import { FaCreditCard, FaRegCreditCard } from 'react-icons/fa';

export default function StepPagamento() {
  const { metodoPagamento, setMetodoPagamento } = useAgendamentoStore();

  const metodos = [
    { id: 'PIX', nome: 'Pix', icon: <MdOutlinePix className="text-green-400" size={24} /> },
    { id: 'CREDITO', nome: 'Cartão de Crédito', icon: <FaCreditCard className="text-gold" size={24} /> },
    { id: 'DEBITO', nome: 'Cartão de Débito', icon: <FaRegCreditCard className="text-blue-400" size={24} /> },
    { id: 'DINHEIRO', nome: 'Dinheiro', icon: <BsCashCoin className="text-gray-400" size={24} /> },
  ];

  return (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-lg font-bold text-gold-light">Forma de Pagamento</h2>
        <p className="text-text-muted text-xs">Como você prefere pagar pelo serviço?</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {metodos.map((metodo) => {
          const isSelected = metodoPagamento === metodo.id;
          return (
            <button
              key={metodo.id}
              onClick={() => setMetodoPagamento(metodo.id)}
              className={`p-4 rounded-xl border flex flex-col items-center gap-3 transition-all duration-300 ${
                isSelected 
                ? 'bg-gold/10 border-gold shadow-[0_0_15px_rgba(212,175,55,0.2)]' 
                : 'bg-background-darker border-white/5 hover:border-white/20'
              }`}
            >
              {metodo.icon}
              <span className={`text-sm font-semibold ${isSelected ? 'text-gold' : 'text-text-primary'}`}>
                {metodo.nome}
              </span>
            </button>
          );
        })}
      </div>
      
      <p className="text-[10px] text-text-muted text-center pt-2">
        O pagamento será realizado no local, após o atendimento.
      </p>
    </div>
  );
}
