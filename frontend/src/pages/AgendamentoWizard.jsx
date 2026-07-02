import React, { useState } from 'react';
import useAgendamentoStore from '../store/useAgendamentoStore';
import api from '../services/api';
import StepServicos from '../components/StepServicos';
import StepBarbeiros from '../components/StepBarbeiros';
import StepDataHora from '../components/StepDataHora';
import AuthModal from '../components/AuthModal';

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

  // Zustand
  const { barbeiroId, servicosIds, dataHora, resetStore, userToken, setAuthModalOpen } = useAgendamentoStore();

  // Verifica se o passo atual está válido para avançar
  const isStepValid = () => {
    if (step === 1) return servicosIds.length > 0;
    if (step === 2) return barbeiroId !== null;
    if (step === 3) return dataHora !== null;
    return false;
  };

  const handleNext = () => {
    if (isStepValid() && step < 3) {
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
    setSubmitting(true);
    setSubmitError(null);

    try {
      const payload = {
        profissional: barbeiroId,
        servicos: servicosIds,
        data_hora_inicio: dataHora,
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
              Seu horário foi reservado. Um e-mail de confirmação foi enviado!
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

  return (
    <div className="w-full max-w-md mx-auto py-8 px-4">
      {/* Banner da Barbearia */}
      <div className="w-full h-32 rounded-2xl overflow-hidden border border-white/5 mb-6 relative shadow-lg shadow-black/35">
        <img src={bannerImg} alt="Golden Barber Shop" className="w-full h-full object-cover opacity-70" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-black/10 to-transparent"></div>
        <div className="absolute bottom-3 left-4">
          <span className="text-[9px] uppercase font-bold tracking-widest text-gold bg-background-darker/70 px-2 py-0.5 rounded border border-gold/25">Ambiente Premium</span>
        </div>
      </div>

      {/* Indicador de Passos */}
      <div className="flex justify-between items-center mb-8 px-4">
        {[1, 2, 3].map((num) => (
          <div key={num} className="flex items-center">
            <div className={`w-8 h-8 rounded-full border font-bold text-xs flex items-center justify-center transition-all ${
              step >= num 
                ? 'bg-gold border-gold text-background' 
                : 'border-white/10 text-text-muted bg-background-darker'
            }`}>
              {num}
            </div>
            {num < 3 && (
              <div className={`w-16 h-[2px] transition-colors ${
                step > num ? 'bg-gold' : 'bg-white/10'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Conteúdo do Passo Ativo */}
      <div className="card-premium mb-6 min-h-[380px] flex flex-col justify-between">
        <div>
          {step === 1 && <StepServicos />}
          {step === 2 && <StepBarbeiros />}
          {step === 3 && <StepDataHora />}
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

        {step < 3 ? (
          <button
            type="button"
            onClick={handleNext}
            disabled={!isStepValid()}
            className="btn-gold flex-1 py-3 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
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
