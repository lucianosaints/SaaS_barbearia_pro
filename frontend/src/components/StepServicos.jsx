import React, { useState, useEffect } from 'react';
import api from '../services/api';
import useAgendamentoStore from '../store/useAgendamentoStore';
import { motion } from 'framer-motion';

/**
 * Passo do Wizard para seleção de Serviços.
 * Permite que o cliente selecione múltiplos serviços para agendamento.
 */
export default function StepServicos() {
  const [servicos, setServicos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Zustand
  const { empresaId, servicosIds, toggleServicoId } = useAgendamentoStore();

  useEffect(() => {
    async function loadServicos() {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/api/servicos/', {
          params: { empresa_id: empresaId }
        });
        setServicos(response.data.results || response.data);
      } catch (err) {
        console.error('Erro ao buscar serviços:', err);
        setError('Falha ao obter lista de serviços.');
      } finally {
        setLoading(false);
      }
    }
    if (empresaId) {
      loadServicos();
    }
  }, [empresaId]);

  if (loading) {
    return (
      <div className="py-8 text-center text-sm text-text-muted">
        Carregando serviços...
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-6 bg-red-500/10 text-red-400 text-sm border border-red-500/20 rounded-xl text-center">
        {error}
      </div>
    );
  }

  // Configurações de Animação
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 25 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 15 } }
  };

  return (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-lg font-bold text-gold-light">Escolha os Serviços</h2>
        <p className="text-text-muted text-xs">Você pode selecionar múltiplos serviços para uma mesma sessão</p>
      </div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-3 max-h-[350px] overflow-y-auto pr-1"
      >
        {servicos.map((servico) => {
          const isSelected = servicosIds.includes(servico.id);
          return (
            <motion.div
              key={servico.id}
              variants={cardVariants}
              whileHover={{ scale: 1.02, transition: { duration: 0.15 } }}
              whileTap={{ scale: 0.98 }}
              animate={isSelected ? {
                borderColor: ["rgba(212, 175, 55, 0.4)", "rgba(212, 175, 55, 0.9)", "rgba(212, 175, 55, 0.4)"],
                boxShadow: [
                  "0 0 0px rgba(212, 175, 55, 0)",
                  "0 0 10px rgba(212, 175, 55, 0.35)",
                  "0 0 0px rgba(212, 175, 55, 0)"
                ]
              } : {
                borderColor: "rgba(255, 255, 255, 0.05)",
                boxShadow: "0 0 0px rgba(0,0,0,0)"
              }}
              transition={isSelected ? {
                borderColor: { repeat: Infinity, duration: 2, ease: "easeInOut" },
                boxShadow: { repeat: Infinity, duration: 2, ease: "easeInOut" }
              } : { duration: 0.2 }}
              onClick={() => toggleServicoId(servico.id)}
              className={`p-4 rounded-xl border cursor-pointer flex justify-between items-center transition-colors duration-200 ${
                isSelected ? 'bg-gold/10' : 'bg-background-darker hover:border-white/20'
              }`}
            >
              <div>
                <h3 className="font-semibold text-sm text-text-primary">{servico.nome}</h3>
                <span className="text-xs text-text-muted">⏱️ {servico.duracao_minutos} minutos</span>
              </div>
              <div className="text-right">
                <span className="font-bold text-sm text-accent-orange">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(servico.preco)}
                </span>
                <div className={`w-5 h-5 rounded-full border flex items-center justify-center mt-1.5 transition-colors ${
                  isSelected ? 'bg-gold border-gold' : 'border-white/20'
                }`}>
                  {isSelected && <span className="text-[10px] text-background font-bold">✓</span>}
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
