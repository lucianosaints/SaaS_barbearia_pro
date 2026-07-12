import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell 
} from 'recharts';
import api from '../services/api';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

/**
 * Componente FinanceiroDashboard.
 * Apresenta o painel de faturamento, comissionamento e lucro líquido da empresa.
 */
export default function FinanceiroDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');

  const fetchFinanceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (dataInicio && dataFim) {
        params.data_inicio = dataInicio;
        params.data_fim = dataFim;
      }
      const response = await api.get('/api/financas/dashboard/', { params });
      setData(response.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'Erro ao carregar os dados financeiros.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinanceData();
  }, [dataInicio, dataFim]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-16">
        <div className="w-10 h-10 border-4 border-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-xs text-text-secondary">Carregando painel financeiro...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-6 text-center max-w-md w-full">
          <span className="text-3xl">⚠️</span>
          <h3 className="mt-2 font-bold text-rose-400">Acesso Negado ou Erro</h3>
          <p className="mt-1.5 text-xs text-text-muted leading-relaxed">{error}</p>
        </div>
      </div>
    );
  }

  const { faturamento_bruto, total_comissoes, lucro_liquido, desempenho_profissionais } = data;

  // Formato para gráfico de Pizza (Lucro vs Comissões)
  const pieData = [
    { name: 'Lucro Líquido', value: lucro_liquido, color: '#10b981' },
    { name: 'Comissões', value: total_comissoes, color: '#f97316' },
  ].filter(item => item.value > 0);

  // Formatação de Moeda
  const formatCurrency = (val) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
  };

  const exportarPDF = () => {
    if (!data || data.desempenho_profissionais.length === 0) {
      alert("Não há dados para exportar.");
      return;
    }

    const doc = new jsPDF();
    doc.setFontSize(18);
    doc.text('Relatório Financeiro - Salão Pro', 14, 22);
    
    doc.setFontSize(11);
    doc.setTextColor(100);
    doc.text(`Período: ${dataInicio ? dataInicio.split('-').reverse().join('/') : 'Início do mês'} até ${dataFim ? dataFim.split('-').reverse().join('/') : 'Hoje'}`, 14, 30);
    
    doc.text(`Faturamento Bruto: ${formatCurrency(faturamento_bruto)}`, 14, 38);
    doc.text(`Comissões Pagas: ${formatCurrency(total_comissoes)}`, 14, 44);
    doc.text(`Lucro Líquido: ${formatCurrency(lucro_liquido)}`, 14, 50);

    const tableColumn = ["Profissional", "Faturamento Gerado", "Comissão Devida"];
    const tableRows = [];

    data.desempenho_profissionais.forEach(barbeiro => {
      const rowData = [
        barbeiro.nome,
        formatCurrency(barbeiro.faturamento),
        formatCurrency(barbeiro.comissao)
      ];
      tableRows.push(rowData);
    });

    doc.autoTable({
      startY: 58,
      head: [tableColumn],
      body: tableRows,
      theme: 'grid',
      headStyles: { fillColor: [212, 175, 55], textColor: 0 },
    });

    doc.save('relatorio-financeiro-salaopro.pdf');
  };

  return (
    <div className="w-full max-w-6xl mx-auto py-6 px-4 space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">
            Dashboard Financeiro
          </h1>
          <p className="text-text-muted text-xs sm:text-sm">
            Acompanhamento de faturamento bruto, custos comissionados e lucros.
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-background-paper border border-white/10 rounded-lg px-3 py-1.5">
            <span className="text-xs text-text-secondary">De:</span>
            <input 
              type="date" 
              value={dataInicio} 
              onChange={(e) => setDataInicio(e.target.value)}
              className="bg-transparent text-sm text-white outline-none"
            />
            <span className="text-xs text-text-secondary ml-2">Até:</span>
            <input 
              type="date" 
              value={dataFim} 
              onChange={(e) => setDataFim(e.target.value)}
              className="bg-transparent text-sm text-white outline-none"
            />
          </div>
          <button 
            onClick={exportarPDF}
            className="bg-gold text-background-darker hover:bg-gold-light px-4 py-2 rounded-lg font-bold text-sm transition-colors"
          >
            📄 Exportar PDF
          </button>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Faturamento Bruto */}
        <div className="bg-background-paper border border-white/5 rounded-2xl p-5 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gold/5 rounded-full blur-2xl group-hover:bg-gold/10 transition-colors"></div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-gold-light/75">Faturamento Bruto</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-gold mt-1.5">{formatCurrency(faturamento_bruto)}</h2>
          <p className="text-[10px] text-text-muted mt-2">Total transacionado em agendamentos concluídos.</p>
        </div>

        {/* Total Comissões */}
        <div className="bg-background-paper border border-white/5 rounded-2xl p-5 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-orange-500/5 rounded-full blur-2xl group-hover:bg-orange-500/10 transition-colors"></div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-orange-400">Comissões Pagas</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-accent-orange mt-1.5">{formatCurrency(total_comissoes)}</h2>
          <p className="text-[10px] text-text-muted mt-2">Fração destinada ao pagamento dos profissionais.</p>
        </div>

        {/* Lucro Líquido */}
        <div className="bg-background-paper border border-white/5 rounded-2xl p-5 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors"></div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400">Lucro Líquido</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-emerald-500 mt-1.5">{formatCurrency(lucro_liquido)}</h2>
          <p className="text-[10px] text-text-muted mt-2">Saldo líquido mantido pelo estabelecimento.</p>
        </div>
      </div>

      {/* Gráficos e Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de Desempenho por Barbeiro */}
        <div className="bg-background-paper border border-white/5 rounded-2xl p-5 flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="font-bold text-sm text-text-primary">Faturamento vs Comissão por Profissional</h3>
            <p className="text-text-muted text-[11px]">Comparativo de receitas geradas e comissões.</p>
          </div>
          <div className="h-64 w-full">
            {desempenho_profissionais.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-text-muted">Nenhum dado disponível</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={desempenho_profissionais} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="nome" stroke="#a3a3a3" fontSize={10} />
                  <YAxis stroke="#a3a3a3" fontSize={10} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e1e1e', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    itemStyle={{ fontSize: 11 }}
                    labelStyle={{ color: '#fff', fontSize: 12, fontWeight: 'bold' }}
                    formatter={(value) => [formatCurrency(value), '']}
                  />
                  <Legend wrapperStyle={{ fontSize: 10, paddingTop: 10 }} />
                  <Bar dataKey="faturamento" name="Faturamento" fill="#d4af37" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="comissao" name="Comissão" fill="#f97316" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Divisão de Receitas */}
        <div className="bg-background-paper border border-white/5 rounded-2xl p-5 flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="font-bold text-sm text-text-primary">Distribuição de Receita</h3>
            <p className="text-text-muted text-[11px]">Distribuição percentual do faturamento total do estabelecimento.</p>
          </div>
          <div className="flex-1 flex flex-col sm:flex-row items-center justify-center gap-6">
            <div className="h-48 w-48 relative">
              {pieData.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-text-muted">Sem dados</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e1e1e', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      itemStyle={{ fontSize: 11 }}
                      formatter={(value) => [formatCurrency(value), '']}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="space-y-3">
              {pieData.map((item, idx) => {
                const percent = faturamento_bruto > 0 ? ((item.value / faturamento_bruto) * 100).toFixed(1) : 0;
                return (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="w-3.5 h-3.5 rounded" style={{ backgroundColor: item.color }}></div>
                    <div>
                      <h4 className="text-xs font-semibold text-text-primary">{item.name}</h4>
                      <span className="text-[10px] text-text-muted">{percent}% ({formatCurrency(item.value)})</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Ranking de Desempenho */}
      <div className="bg-background-paper border border-white/5 rounded-2xl p-5">
        <div className="mb-4">
          <h3 className="font-bold text-sm text-text-primary">Ranking de Profissionais</h3>
          <p className="text-text-muted text-[11px]">Lista ordenada de arrecadação por prestador de serviço.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 text-[10px] uppercase text-text-secondary tracking-wider font-semibold">
                <th className="py-2.5 px-3">Profissional</th>
                <th className="py-2.5 px-3 text-right">Faturamento Gerado</th>
                <th className="py-2.5 px-3 text-right">Comissão Devida</th>
                <th className="py-2.5 px-3 text-right">Participação</th>
              </tr>
            </thead>
            <tbody>
              {desempenho_profissionais.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-6 text-center text-xs text-text-muted">Nenhum profissional com atividade registrada este mês.</td>
                </tr>
              ) : (
                desempenho_profissionais.map((barbeiro, idx) => {
                  const part = faturamento_bruto > 0 ? ((barbeiro.faturamento / faturamento_bruto) * 100).toFixed(1) : 0;
                  return (
                    <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors text-xs">
                      <td className="py-3 px-3 font-semibold text-text-primary">
                        {idx === 0 && <span className="mr-1.5">🏆</span>}
                        {barbeiro.nome}
                      </td>
                      <td className="py-3 px-3 text-right font-medium text-gold-light">{formatCurrency(barbeiro.faturamento)}</td>
                      <td className="py-3 px-3 text-right text-orange-400">{formatCurrency(barbeiro.comissao)}</td>
                      <td className="py-3 px-3 text-right text-text-secondary">{part}%</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
