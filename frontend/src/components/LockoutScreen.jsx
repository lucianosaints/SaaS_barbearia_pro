import React, { useState } from 'react';
import { motion } from 'framer-motion';
import api from '../services/api';

export default function LockoutScreen() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pixData, setPixData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [meses, setMeses] = useState(1);

  const valorBase = 49.99;
  const valorTotal = (valorBase * meses).toFixed(2).replace('.', ',');

  const handleCheckout = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/assinaturas/criar-assinatura/', { meses });
      if (response.data.qr_code_base64 && response.data.qr_code) {
        setPixData({
          qr_code_base64: response.data.qr_code_base64,
          qr_code: response.data.qr_code
        });
      } else {
        setError('Erro ao gerar o código PIX. Formato inválido ou indisponível.');
      }
    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        setError('Erro: ' + err.response.data.error);
      } else {
        setError('Ocorreu um erro de comunicação com o servidor.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (pixData?.qr_code) {
      navigator.clipboard.writeText(pixData.qr_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] bg-bg-primary text-text-primary p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full bg-bg-secondary p-8 rounded-2xl shadow-premium border border-border-color text-center"
      >
        <div className="w-16 h-16 bg-red-500/20 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-8 h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
          </svg>
        </div>

        <h2 className="text-2xl font-bold mb-4 text-white">Acesso Bloqueado</h2>
        <p className="text-text-muted mb-8 text-sm">
          Seu período de teste (Free Trial) expirou ou sua assinatura está pendente.
          Para continuar usando o painel administrativo da sua barbearia, por favor, regularize sua assinatura.
        </p>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {!pixData ? (
          <div className="w-full flex flex-col gap-4">
            <div className="flex flex-col gap-2 mb-2">
              <label className="text-left text-sm text-text-muted font-semibold">Quantos meses deseja renovar?</label>
              <div className="flex bg-bg-primary p-1 rounded-xl border border-border-color">
                {[1, 2, 3, 6].map(num => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setMeses(num)}
                    className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${meses === num ? 'bg-primary text-bg-primary shadow-md' : 'text-text-muted hover:text-white'}`}
                  >
                    {num} {num === 1 ? 'Mês' : 'Meses'}
                  </button>
                ))}
              </div>
              {meses > 1 && (
                <div className="text-xs text-green-400 text-left mt-1">
                  Vencimento será estendido em {meses * 30} dias.
                </div>
              )}
            </div>

            <button
              onClick={handleCheckout}
              disabled={loading}
              className="w-full bg-primary hover:bg-primary-hover text-bg-primary font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_15px_rgba(212,175,55,0.4)] flex items-center justify-center"
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-primary border-t-white rounded-full animate-spin"></span>
              ) : (
                `💠 Pagar via PIX (R$ ${valorTotal})`
              )}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center mt-4 w-full">
            <h3 className="text-lg font-bold text-primary mb-2">Escaneie o QR Code</h3>
            <img 
              src={`data:image/png;base64,${pixData.qr_code_base64}`} 
              alt="QR Code PIX" 
              className="w-48 h-48 rounded-lg border-2 border-border-color mb-4 bg-white"
            />
            
            <p className="text-text-muted text-sm mb-2">Ou copie o código abaixo:</p>
            <div className="flex w-full gap-2 mb-6">
              <input 
                type="text" 
                value={pixData.qr_code} 
                readOnly 
                className="flex-1 bg-bg-primary border border-border-color text-white rounded-lg px-3 py-2 text-sm outline-none w-full"
              />
              <button 
                onClick={handleCopy}
                className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap"
              >
                {copied ? '✅ Copiado!' : 'Copiar'}
              </button>
            </div>
            
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-green-500/20"
            >
              ✅ Já paguei
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
