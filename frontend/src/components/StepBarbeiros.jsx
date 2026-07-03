import React, { useState, useEffect } from 'react';
import api from '../services/api';
import useAgendamentoStore from '../store/useAgendamentoStore';
import { motion } from 'framer-motion';

/**
 * Passo do Wizard para seleção do Barbeiro / Profissional.
 */
export default function StepBarbeiros() {
  const [barbeiros, setBarbeiros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Zustand
  const { barbeiroId, setBarbeiroId } = useAgendamentoStore();

  useEffect(() => {
    async function loadBarbeiros() {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/api/usuarios/');
        const users = response.data.results || response.data;
        const apenasProfissionais = users.filter(u => u.tipo === 'PROFISSIONAL' || u.tipo === 'ADMINISTRADOR');
        setBarbeiros(apenasProfissionais);
      } catch (err) {
        console.error('Erro ao buscar barbeiros:', err);
        setError('Falha ao obter lista de profissionais.');
      } finally {
        setLoading(false);
      }
    }
    loadBarbeiros();
  }, []);

  if (loading) {
    return (
      <div className="py-8 text-center text-sm text-text-muted">
        Carregando profissionais...
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
      transition: { staggerChildren: 0.1 }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 25 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 15 } }
  };

  return (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-lg font-bold text-gold-light">Escolha o Profissional</h2>
        <p className="text-text-muted text-xs">Selecione quem irá cuidar do seu visual</p>
      </div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 gap-3 max-h-[350px] overflow-y-auto pr-1"
      >
        {barbeiros.map((barbeiro) => {
          const isSelected = barbeiroId === barbeiro.id;
          const nomeCompleto = barbeiro.first_name 
            ? `${barbeiro.first_name} ${barbeiro.last_name || ''}` 
            : barbeiro.username;
          
          const avaliacao = parseFloat(barbeiro.avaliacao) || 5.0;

          return (
            <motion.div
              key={barbeiro.id}
              variants={cardVariants}
              whileHover={{ scale: 1.03, transition: { duration: 0.15 } }}
              whileTap={{ scale: 0.97 }}
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
                borderColor: { repeat: Infinity, duration: 2.5, ease: "easeInOut" },
                boxShadow: { repeat: Infinity, duration: 2.5, ease: "easeInOut" }
              } : { duration: 0.2 }}
              onClick={() => setBarbeiroId(barbeiro.id)}
              className={`p-4 rounded-xl border cursor-pointer text-center flex flex-col items-center gap-2 transition-colors duration-200 ${
                isSelected ? 'bg-gold/10' : 'bg-background-darker hover:border-white/20'
              }`}
            >
              {/* Foto real ou Inicial do Profissional */}
              <div className={`w-16 h-16 rounded-full overflow-hidden border flex items-center justify-center transition-colors ${
                isSelected ? 'border-gold' : 'border-white/10 text-gold-light bg-background'
              }`}>
                {barbeiro.foto ? (
                  <img 
                    src={barbeiro.foto.startsWith('http') ? barbeiro.foto : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${barbeiro.foto}`} 
                    alt={nomeCompleto} 
                    className="w-full h-full object-cover" 
                  />
                ) : (
                  <span className="text-xl font-bold">{nomeCompleto.charAt(0).toUpperCase()}</span>
                )}
              </div>

              <div className="mt-1">
                <h3 className="font-semibold text-xs text-text-primary line-clamp-1">{nomeCompleto}</h3>
                <div className="flex items-center justify-center gap-1 mt-0.5">
                  <span className="text-gold text-[10px]">{'⭐'.repeat(Math.round(avaliacao))}</span>
                  <span className="text-[10px] text-text-muted font-medium">{avaliacao.toFixed(1)}</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
