import React, { useState, useEffect } from 'react';
import api from '../services/api';
import useAgendamentoStore from '../store/useAgendamentoStore';

export default function GestaoConfiguracoes() {
  const { userEmpresa } = useAgendamentoStore();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [pagamentoLoading, setPagamentoLoading] = useState(false);
  
  const [empresaInfo, setEmpresaInfo] = useState(null);
  
  const [config, setConfig] = useState({
    hora_abertura: '09:00',
    hora_fechamento: '19:00',
    intervalo_almoco_inicio: '12:00',
    intervalo_almoco_fim: '13:00'
  });

  useEffect(() => {
    if (userEmpresa && userEmpresa.id) {
      // Buscar dados atualizados
      api.get(`/api/empresas/${userEmpresa.id}/`).then(res => {
        setConfig({
          hora_abertura: res.data.hora_abertura ? res.data.hora_abertura.substring(0, 5) : '09:00',
          hora_fechamento: res.data.hora_fechamento ? res.data.hora_fechamento.substring(0, 5) : '19:00',
          intervalo_almoco_inicio: res.data.intervalo_almoco_inicio ? res.data.intervalo_almoco_inicio.substring(0, 5) : '',
          intervalo_almoco_fim: res.data.intervalo_almoco_fim ? res.data.intervalo_almoco_fim.substring(0, 5) : ''
        });
        setEmpresaInfo(res.data);
      }).catch(err => {
        console.error(err);
        // Fallback se a API for bloqueada (ex: trial expirado)
        if (err.response?.status === 402 || err.response?.status === 403) {
           setEmpresaInfo({
               ...userEmpresa,
               assinatura_ativa: false,
               em_trial: false
           });
        } else {
           setEmpresaInfo(userEmpresa || { assinatura_ativa: false, em_trial: false });
        }
      });
    }
  }, [userEmpresa]);

  const handleChange = (e) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);
    setError(null);
    try {
      await api.patch(`/api/empresas/${userEmpresa.id}/`, config);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
      setError('Erro ao salvar as configurações.');
    } finally {
      setLoading(false);
    }
  };

  const getDiasRestantes = () => {
    if (!empresaInfo || !empresaInfo.data_fim_trial) return null;
    const fim = new Date(empresaInfo.data_fim_trial);
    const hoje = new Date();
    const diffTime = fim - hoje;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  const handlePagar = async () => {
    setPagamentoLoading(true);
    try {
      const response = await api.post('/api/assinaturas/criar-assinatura/');
      if (response.data.ticket_url) {
        window.location.href = response.data.ticket_url;
      } else if (response.data.init_point) {
        window.location.href = response.data.init_point;
      } else {
        alert('Erro ao gerar o link de pagamento.');
      }
    } catch (err) {
      alert(err.response?.data?.error || 'Erro ao comunicar com Mercado Pago.');
    } finally {
      setPagamentoLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-text-primary">Configurações da Barbearia</h2>
        <p className="text-sm text-text-secondary mt-1">Defina seus horários de funcionamento e intervalo.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Painel de Horários */}
        <div className="bg-background-paper border border-white/5 p-6 rounded-xl w-full">
          <h3 className="text-lg font-bold text-white mb-4">Horários de Atendimento</h3>
        {success && (
          <div className="bg-green-500/10 border border-green-500/20 text-green-400 p-3 rounded-lg mb-4 text-sm font-semibold">
            ✅ Configurações salvas com sucesso!
          </div>
        )}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg mb-4 text-sm font-semibold">
            ❌ {error}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Horário de Abertura</label>
              <input
                type="time"
                name="hora_abertura"
                value={config.hora_abertura}
                onChange={handleChange}
                required
                className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Horário de Fechamento</label>
              <input
                type="time"
                name="hora_fechamento"
                value={config.hora_fechamento}
                onChange={handleChange}
                required
                className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:border-gold outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Início do Intervalo (Almoço)</label>
              <input
                type="time"
                name="intervalo_almoco_inicio"
                value={config.intervalo_almoco_inicio}
                onChange={handleChange}
                className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Fim do Intervalo (Almoço)</label>
              <input
                type="time"
                name="intervalo_almoco_fim"
                value={config.intervalo_almoco_fim}
                onChange={handleChange}
                className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:border-gold outline-none"
              />
            </div>
          </div>
          <p className="text-xs text-text-muted mb-4">Deixe o intervalo em branco caso não tenha pausa.</p>

          <button
            type="submit"
            disabled={loading}
            className="btn-gold w-full py-3 mt-4"
          >
            {loading ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </form>
        </div>

        {/* Painel de Assinatura */}
        <div className="bg-background-paper border border-white/5 p-6 rounded-xl w-full flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-gold">👑</span> Meu Plano Barbeiro_Pro
            </h3>
            
            {empresaInfo ? (
              <div className="space-y-4 mb-6">
                <div className="flex justify-between p-3 bg-black/40 rounded-lg border border-white/5">
                  <span className="text-sm text-gray-400">Status da Assinatura:</span>
                  <span className={`text-sm font-bold ${empresaInfo.assinatura_ativa ? 'text-green-500' : (empresaInfo.em_trial ? 'text-blue-400' : 'text-red-500')}`}>
                    {empresaInfo.assinatura_ativa ? 'Ativa' : (empresaInfo.em_trial ? `Em Teste (${getDiasRestantes() !== null ? getDiasRestantes() + ' dias restantes' : 'Ativo'})` : 'Inativa/Bloqueada')}
                  </span>
                </div>
                
                {empresaInfo.em_trial && !empresaInfo.assinatura_ativa && empresaInfo.data_fim_trial && (
                  <div className="flex justify-between p-3 bg-black/40 rounded-lg border border-white/5">
                    <span className="text-sm text-gray-400">Expira em:</span>
                    <span className="text-sm font-bold text-white">
                      {new Date(empresaInfo.data_fim_trial).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                )}
                
                {!empresaInfo.assinatura_ativa && empresaInfo.em_trial && (
                  <p className="text-xs text-gray-400 leading-relaxed bg-blue-500/10 p-3 rounded border border-blue-500/20">
                    Você pode antecipar o pagamento da sua assinatura. Ao pagar, você garante acesso ininterrupto sem aguardar o bloqueio após o período de teste.
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-500 animate-pulse">Carregando status do plano...</p>
            )}
          </div>

          <button
            onClick={handlePagar}
            disabled={pagamentoLoading}
            className="w-full bg-gradient-to-r from-gold-light via-gold to-gold-dark text-background-darker hover:shadow-[0_0_20px_rgba(212,175,55,0.4)] font-bold py-3 px-4 rounded-lg transition-all flex justify-center items-center gap-2 mt-auto"
          >
            {pagamentoLoading ? (
              <span className="w-5 h-5 border-2 border-background-darker/30 border-t-background-darker rounded-full animate-spin"></span>
            ) : (
              <>💳 Assinar Sistema (R$ 49,99/mês)</>
            )}
          </button>
        </div>

      </div>
    </div>
  );
}
