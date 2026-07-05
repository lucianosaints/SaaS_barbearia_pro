import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useAgendamentoStore from '../store/useAgendamentoStore';
import api from '../services/api';
import StepServicos from '../components/StepServicos';
import StepBarbeiros from '../components/StepBarbeiros';
import StepDataHora from '../components/StepDataHora';
import StepPagamento from '../components/StepPagamento';
import AuthModal from '../components/AuthModal';
import { motion, AnimatePresence } from 'framer-motion';

import bannerImg from '../imagem/Babearia2.jpg';

/**
 * Página AgendamentoWizard (Visão do Cliente - Mobile-first).
 * Orquestra as etapas de agendamento: Serviços -> Profissional -> Data/Hora.
 */
export default function AgendamentoWizard() {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  
  // States para carregamento do slug
  const [loadingEmpresa, setLoadingEmpresa] = useState(true);
  const [empresaNotFound, setEmpresaNotFound] = useState(false);

  const { empresaSlug } = useParams();
  const navigate = useNavigate();

  // Zustand
  const { empresaId, setEmpresaId, barbeiroId, servicosIds, dataHora, metodoPagamento, resetStore, userToken, setAuthModalOpen } = useAgendamentoStore();

  useEffect(() => {
    async function fetchEmpresa() {
      try {
        const response = await api.get(`/api/empresas/por-slug/${empresaSlug}/`);
        setEmpresaId(response.data.id);
      } catch (error) {
        console.error("Erro ao buscar empresa pelo slug", error);
        setEmpresaNotFound(true);
      } finally {
        setLoadingEmpresa(false);
      }
    }
    
    if (empresaSlug) {
      fetchEmpresa();
    } else {
      setEmpresaNotFound(true);
      setLoadingEmpresa(false);
    }
  }, [empresaSlug, setEmpresaId]);

  const isStepValid = () => {
    if (step === 1) return servicosIds.length > 0;
    if (step === 2) return barbeiroId !== null;
    if (step === 3) return dataHora !== null;
    if (step === 4) return metodoPagamento !== null;
    return false;
  };

  const handleNext = () => {
    if (isStepValid() && step < 4) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  // Faz a chamada de POST final no backend para criar o agendamento
  const handleFinalizarAgendamento = async () => {
    // Se logou avulso e não tem dados do agendamento, apenas sai.
    if (!servicosIds.length || !barbeiroId || !dataHora) return;

    setSubmitting(true);
    setSubmitError(null);

    try {
      const payload = {
        profissional: barbeiroId,
        servicos: servicosIds,
        data_hora_inicio: dataHora,
        metodo_pagamento: metodoPagamento,
      };

      await api.post('/api/agendamentos/', payload);
      setSuccess(true);
      resetStore();
    } catch (err) {
      console.error('Erro ao salvar agendamento:', err);
      setSubmitError(
        err.response?.data?.non_field_errors?.[0] || 
        err.response?.data?.detail || 
        'Ocorreu uma falha ao realizar o agendamento. Por favor, tente novamente.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Interceptador que exige autenticação
  const handleConfirmar = () => {
    if (!isStepValid()) return;
    
    // Se o cliente não estiver autenticado, abre o modal de login/cadastro
    if (!userToken) {
      setAuthModalOpen(true);
      return;
    }

    // Se estiver autenticado, finaliza o agendamento imediatamente
    handleFinalizarAgendamento();
  };

  if (success) {
    return (
      <div className="w-full max-w-md mx-auto py-12 px-4">
        <div className="card-premium text-center space-y-6">
          <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full flex items-center justify-center text-3xl mx-auto animate-bounce">
            ✓
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-text-primary">Agendado com Sucesso!</h1>
            <p className="text-text-muted text-sm">
              Seu horário foi reservado. Acompanhe pelo painel "Minha Agenda".
            </p>
          </div>
          <button
            onClick={() => {
              setSuccess(false);
              setStep(1);
            }}
            className="btn-gold w-full text-sm"
          >
            Novo Agendamento
          </button>
        </div>
      </div>
    );
  }

  if (loadingEmpresa) {
    return (
      <div className="w-full h-[60vh] flex flex-col items-center justify-center text-text-muted">
        <div className="w-8 h-8 border-4 border-gold border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-sm">Buscando barbearia...</p>
      </div>
    );
  }

  if (empresaNotFound) {
    return (
      <div className="w-full h-[60vh] flex flex-col items-center justify-center text-text-muted px-4 text-center">
        <h2 className="text-2xl font-bold text-white mb-2">Barbearia não encontrada</h2>
        <p className="text-sm max-w-sm mb-6">O link que você tentou acessar não existe ou a barbearia está inativa.</p>
        <button onClick={() => navigate('/')} className="btn-gold px-6">Ir para a Tela Inicial</button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto py-4 sm:py-8 px-4">
      {/* Banner da Barbearia */}
      <div className="w-full h-24 sm:h-32 rounded-2xl overflow-hidden border border-white/5 mb-4 sm:mb-6 relative shadow-lg shadow-black/35">
        <img src={bannerImg} alt="Barbeiro Pro" className="w-full h-full object-cover opacity-70" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-black/10 to-transparent"></div>
        <div className="absolute bottom-3 left-4">
          <span className="text-[9px] uppercase font-bold tracking-widest text-gold bg-background-darker/70 px-2 py-0.5 rounded border border-gold/25">Ambiente Premium</span>
        </div>
      </div>

      {/* Indicador de Passos */}
      <div className="flex justify-between items-center mb-4 sm:mb-8 px-4">
        {[1, 2, 3, 4].map((num) => (
          <div key={num} className="flex items-center">
            <div className={`w-8 h-8 rounded-full border font-bold text-xs flex items-center justify-center transition-all ${
              step >= num 
                ? 'bg-gold border-gold text-background-darker' 
                : 'border-white/10 text-text-muted bg-background-darker'
            }`}>
              {num}
            </div>
            {num < 4 && (
              <div className={`w-8 sm:w-16 h-[2px] transition-colors ${
                step > num ? 'bg-gold' : 'bg-white/10'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Conteúdo do Passo Ativo */}
      <div className="card-premium mb-4 sm:mb-6 min-h-[320px] sm:min-h-[380px] flex flex-col justify-between overflow-hidden">
        <div className="flex-1 flex flex-col justify-between">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              {step === 1 && <StepServicos />}
              {step === 2 && <StepBarbeiros />}
              {step === 3 && <StepDataHora />}
              {step === 4 && <StepPagamento />}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Notificação de Erro se houver */}
        {submitError && (
          <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-lg">
            ⚠️ {submitError}
          </div>
        )}
      </div>

      {/* Botões de Ação de Navegação */}
      <div className="flex gap-4">
        {step > 1 && (
          <button
            type="button"
            onClick={handleBack}
            className="btn-gold-outline flex-1 py-3 text-sm font-semibold"
            disabled={submitting}
          >
            Voltar
          </button>
        )}

        {step < 4 ? (
          <button
            type="button"
            onClick={handleNext}
            disabled={!isStepValid()}
            className={`px-8 py-3 rounded-lg font-bold text-sm transition-all ${
              isStepValid() 
              ? 'bg-gradient-to-r from-gold-light to-gold-dark text-background-darker hover:shadow-lg hover:shadow-gold/20 flex-1' 
              : 'bg-white/5 text-white/30 cursor-not-allowed flex-1'
            }`}
          >
            Avançar
          </button>
        ) : (
          <button
            type="button"
            onClick={handleConfirmar}
            disabled={!isStepValid() || submitting}
            className="btn-accent flex-1 py-3 text-sm font-semibold disabled:opacity-50"
          >
            {submitting ? 'Confirmando...' : 'Confirmar Agendamento ✂️'}
          </button>
        )}
      </div>

      {/* Modal de Autenticação do Cliente */}
      <AuthModal onAuthSuccess={handleFinalizarAgendamento} />
    </div>
  );
}
