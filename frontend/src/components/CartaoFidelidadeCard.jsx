import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function CartaoFidelidadeCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFidelidade = async () => {
      try {
        const response = await api.get('/api/fidelidade/meu-cartao/');
        setData(response.data);
      } catch (err) {
        console.error('Erro ao buscar dados de fidelidade:', err);
        setError('Não foi possível carregar seu cartão fidelidade.');
      } finally {
        setLoading(false);
      }
    };
    fetchFidelidade();
  }, []);

  if (loading) {
    return (
      <div className="w-full bg-background-paper border border-white/5 rounded-2xl p-6 flex justify-center items-center">
        <span className="w-6 h-6 border-4 border-gold border-t-transparent rounded-full animate-spin"></span>
      </div>
    );
  }

  if (error || !data) {
    // Não renderizamos erro chamativo para não estragar a UX, apenas silenciamos ou mostramos um aviso leve.
    return null;
  }

  if (!data.ativo) {
    return null; // Não exibe se o programa estiver desativado pela empresa
  }

  const { meta, qtd_selos_atual, estilo, premios_disponiveis } = data;
  
  // Limita o preenchimento para não quebrar a UI
  const selosVisiveis = Math.min(qtd_selos_atual, meta);
  const progressoPercent = (selosVisiveis / meta) * 100;

  // Lógica de Renderização do Goku
  const renderGokuAvatar = () => {
    let emoji = "🧑🏻"; // Base
    let title = "Goku Base";
    
    if (selosVisiveis >= 9) {
      emoji = "🧑🏻‍🦳✨"; // Instinto Superior
      title = "Goku Instinto Superior";
    } else if (selosVisiveis >= 6) {
      emoji = "⚡👱🔥"; // SSJ3
      title = "Goku Super Saiyajin 3";
    } else if (selosVisiveis >= 3) {
      emoji = "👱💛"; // SSJ1
      title = "Goku Super Saiyajin 1";
    }

    if (selosVisiveis >= meta) {
      emoji = "🏆";
      title = "Recompensa Atingida!";
    }

    return (
      <div className="flex flex-col items-center">
        <div className="text-5xl md:text-6xl mb-2 animate-bounce hover:scale-110 transition-transform cursor-pointer" title={title}>
          {emoji}
        </div>
        <p className="text-xs font-bold text-gold uppercase tracking-widest">{title}</p>
      </div>
    );
  };

  // Lógica de Renderização do Classic (Grid de Joinhas/Tesouras)
  const renderClassicGrid = () => {
    const items = [];
    for (let i = 1; i <= meta; i++) {
      const isFilled = i <= selosVisiveis;
      items.push(
        <div 
          key={i} 
          className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center text-lg md:text-xl border-2 transition-all ${
            isFilled 
              ? 'bg-gold border-gold text-background-darker scale-110 shadow-[0_0_15px_rgba(212,175,55,0.4)]' 
              : 'bg-background-darker border-white/10 text-white/20'
          }`}
        >
          {isFilled ? '👍' : '✂️'}
        </div>
      );
    }

    return (
      <div className="flex flex-wrap justify-center gap-3">
        {items}
      </div>
    );
  };

  return (
    <div className="w-full bg-background-paper border border-white/5 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
      {/* Efeito de brilho de fundo */}
      <div className="absolute -top-10 -right-10 w-40 h-40 bg-gold/10 rounded-full blur-3xl group-hover:bg-gold/20 transition-colors pointer-events-none"></div>

      <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
        
        {/* Info Textual */}
        <div className="text-center md:text-left flex-1">
          <h3 className="text-xl font-bold text-white mb-1 flex items-center justify-center md:justify-start gap-2">
            <span className="text-gold">💳</span> Seu Cartão Fidelidade
          </h3>
          <p className="text-sm text-text-muted">
            Faltam <span className="text-gold font-bold">{meta - selosVisiveis}</span> cortes para o seu prêmio grátis!
          </p>
          
          {premios_disponiveis > 0 && (
            <div className="mt-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-3 rounded-xl text-sm font-semibold animate-pulse">
              🎉 Você tem {premios_disponiveis} prêmio(s) resgatável(is)! Converse com o barbeiro no próximo corte.
            </div>
          )}
        </div>

        {/* Visual do Progresso */}
        <div className="flex-1 w-full max-w-sm flex justify-center md:justify-end">
          {estilo === 'goku' ? renderGokuAvatar() : renderClassicGrid()}
        </div>
      </div>

      {/* Barra de Progresso Geral */}
      <div className="mt-6 w-full bg-background-darker rounded-full h-3 border border-white/5 overflow-hidden">
        <div 
          className="bg-gradient-to-r from-gold-dark via-gold to-gold-light h-full rounded-full transition-all duration-1000 ease-out relative"
          style={{ width: `${progressoPercent}%` }}
        >
          {/* Efeito de luz percorrendo a barra */}
          <div className="absolute top-0 left-0 right-0 bottom-0 bg-white/20 w-full animate-[shimmer_2s_infinite]"></div>
        </div>
      </div>
      <div className="mt-2 text-right text-xs font-bold text-text-secondary tracking-widest uppercase">
        {selosVisiveis} / {meta} SELOS
      </div>
    </div>
  );
}
