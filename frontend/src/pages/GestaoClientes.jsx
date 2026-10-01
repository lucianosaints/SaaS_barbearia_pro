import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function GestaoClientes() {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const fetchClientes = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/usuarios/');
      const list = response.data.results || response.data;
      // Garante que mostremos apenas clientes
      setClientes(list.filter(u => u.tipo === 'CLIENTE'));
    } catch (err) {
      console.error(err);
      setError('Erro ao carregar lista de clientes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClientes();
  }, []);

  const handleStatusChange = async (clienteId, novoStatus) => {
    try {
      // Fazendo a chamada assíncrona
      await api.patch(`/api/usuarios/${clienteId}/`, { status: novoStatus });
      
      // Atualiza o estado local para não precisar recarregar toda a lista
      setClientes(prev => prev.map(c => c.id === clienteId ? { ...c, status: novoStatus } : c));
      
      setSuccess(`Status do cliente atualizado para ${novoStatus} com sucesso!`);
      setTimeout(() => setSuccess(null), 4000);
    } catch (err) {
      console.error(err);
      setError('Erro ao atualizar status do cliente.');
      setTimeout(() => setError(null), 4000);
    }
  };

  if (loading && clientes.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-16">
        <div className="w-8 h-8 border-4 border-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-xs text-text-secondary">Carregando clientes...</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Gestão de Clientes</h2>
          <p className="text-text-muted text-xs mt-1">
            Gerencie o acesso e configure regras individuais de sinal (PIX) para seus clientes.
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm flex items-center gap-2 animate-in fade-in">
          <span>⚠️</span> {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-sm flex items-center gap-2 animate-in fade-in">
          <span>✅</span> {success}
        </div>
      )}

      {/* Lista de Clientes */}
      <div className="bg-background-paper border border-white/5 rounded-2xl overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[600px]">
          <thead>
            <tr className="border-b border-white/5 bg-background-darker/50 text-[10px] uppercase text-text-secondary tracking-wider font-semibold whitespace-nowrap">
              <th className="py-3 px-4">Nome do Cliente</th>
              <th className="py-3 px-4">E-mail</th>
              <th className="py-3 px-4">Telefone</th>
              <th className="py-3 px-4 text-center">Status e Regra PIX</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-sm">
            {clientes.map((cliente) => (
              <tr key={cliente.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-4 font-medium text-text-primary">
                  {cliente.first_name} {cliente.last_name}
                </td>
                <td className="py-3 px-4 text-text-secondary">{cliente.email}</td>
                <td className="py-3 px-4 text-text-secondary">{cliente.telefone || '—'}</td>
                <td className="py-3 px-4 text-center">
                  <select
                    value={cliente.status || 'ATIVO'}
                    onChange={(e) => handleStatusChange(cliente.id, e.target.value)}
                    className="bg-background-darker border border-white/10 text-white text-xs rounded-lg focus:ring-gold focus:border-gold block w-full p-2 outline-none cursor-pointer"
                  >
                    <option value="ATIVO">🟢 Ativo (Padrão)</option>
                    <option value="EXIGIR_SINAL">🟡 Exigir Sinal (50% PIX)</option>
                    <option value="BLOQUEADO">🔴 Bloqueado (Lista Negra)</option>
                  </select>
                </td>
              </tr>
            ))}
            {clientes.length === 0 && (
              <tr>
                <td colSpan="4" className="py-8 text-center text-text-muted">Nenhum cliente cadastrado ainda.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
