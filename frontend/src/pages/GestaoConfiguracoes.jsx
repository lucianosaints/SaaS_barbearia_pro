import React, { useState, useEffect } from 'react';
import api from '../services/api';
import useAgendamentoStore from '../store/useAgendamentoStore';

export default function GestaoConfiguracoes() {
  const { userEmpresa } = useAgendamentoStore();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  
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
      }).catch(err => console.error(err));
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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-text-primary">Configurações da Barbearia</h2>
        <p className="text-sm text-text-secondary mt-1">Defina seus horários de funcionamento e intervalo.</p>
      </div>

      <div className="bg-background-paper border border-white/5 p-6 rounded-xl max-w-2xl">
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
    </div>
  );
}
