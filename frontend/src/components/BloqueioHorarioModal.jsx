import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function BloqueioHorarioModal({ isOpen, onClose, onSave }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [profissionais, setProfissionais] = useState([]);
  
  const [formData, setFormData] = useState({
    profissional: '',
    data: '',
    hora_inicio: '',
    hora_fim: '',
    motivo: ''
  });

  useEffect(() => {
    if (isOpen) {
      api.get('/api/usuarios/')
         .then(res => setProfissionais(res.data.filter(u => u.tipo === 'PROFISSIONAL')))
         .catch(err => console.error('Erro ao buscar profissionais:', err));
    }
  }, [isOpen]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const payload = {
        data_hora_inicio: `${formData.data}T${formData.hora_inicio}:00`,
        data_hora_fim: `${formData.data}T${formData.hora_fim}:00`,
        motivo: formData.motivo
      };
      if (formData.profissional) {
        payload.profissional = parseInt(formData.profissional, 10);
      }
      
      await api.post('/api/bloqueios/', payload);
      onSave();
    } catch (err) {
      console.error(err);
      setError('Erro ao criar bloqueio. Verifique os dados inseridos.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1a1a1a] border border-gold/20 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in zoom-in-95 duration-200">
        <h3 className="text-xl font-bold text-gold mb-1">Bloquear Horário</h3>
        <p className="text-sm text-gray-400 mb-6">Registre uma indisponibilidade na agenda.</p>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg mb-4 text-center">
            ❌ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1">Data</label>
            <input 
              type="date"
              name="data"
              value={formData.data}
              onChange={handleChange}
              required
              className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-gold outline-none"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1">Hora de Início</label>
              <input 
                type="time"
                name="hora_inicio"
                value={formData.hora_inicio}
                onChange={handleChange}
                required
                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1">Hora de Fim</label>
              <input 
                type="time"
                name="hora_fim"
                value={formData.hora_fim}
                onChange={handleChange}
                required
                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-gold outline-none"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1">Barbeiro (Opcional)</label>
            <select 
              name="profissional"
              value={formData.profissional}
              onChange={handleChange}
              className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-gold outline-none"
            >
              <option value="">Todos os barbeiros (Barbearia inteira)</option>
              {profissionais.map(p => (
                <option key={p.id} value={p.id}>{p.nome || p.username}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1">Motivo (Opcional)</label>
            <input 
              type="text"
              name="motivo"
              value={formData.motivo}
              onChange={handleChange}
              placeholder="Ex: Feriado, Almoço..."
              className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-gold outline-none"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button 
              type="button" 
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg bg-transparent border border-white/20 text-gray-300 font-semibold text-sm hover:bg-white/5 transition-colors"
            >
              Cancelar
            </button>
            <button 
              type="submit" 
              disabled={loading}
              className="flex-1 py-2.5 rounded-lg bg-gold text-black font-bold text-sm hover:bg-yellow-500 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Salvando...' : 'Confirmar Bloqueio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
