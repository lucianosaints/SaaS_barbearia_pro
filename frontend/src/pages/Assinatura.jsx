import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../services/api';
import { motion } from 'framer-motion';

function Assinatura() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pixData, setPixData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [meses, setMeses] = useState(1);

  const valorBase = 49.99;
  const valorTotal = (valorBase * meses).toFixed(2).replace('.', ',');

  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const paymentStatus = searchParams.get('status');

  const handlePagarPix = async () => {
    setLoading(true);
    setError(null);
    setPixData(null);
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
        setError('Erro do servidor: ' + err.response.data.error);
      } else {
        setError('Ocorreu um erro de comunicação com o servidor. Verifique o console.');
      }
      console.error("Erro ao gerar link MP:", err);
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
    <div className="flex flex-col items-center justify-center min-h-[80vh] bg-bg-primary text-text-primary p-6">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-bg-secondary p-8 rounded-2xl shadow-xl max-w-md w-full border border-bg-tertiary text-center"
      >
        <div className="w-16 h-16 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">
          🔒
        </div>
        <h1 className="text-2xl font-bold text-accent-primary mb-4">Acesso Bloqueado</h1>
        <p className="text-text-secondary mb-6 text-sm leading-relaxed">
          Sua barbearia encontra-se com pendências financeiras ou o período de testes expirou. 
          Renove agora sua assinatura para continuar utilizando nosso sistema!
        </p>

        {paymentStatus === 'success' && (
          <div className="bg-green-500/10 border border-green-500/20 text-green-400 p-4 rounded-lg mb-6 text-sm text-left">
            <strong>✅ Pagamento aprovado com sucesso!</strong>
            <p className="mt-1 opacity-80">Se o sistema ainda não liberou o seu acesso, aguarde alguns minutinhos e recarregue a página.</p>
          </div>
        )}
        {paymentStatus === 'failure' && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg mb-6 text-sm">
            Houve um problema com o seu pagamento. Por favor, tente novamente.
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {!pixData ? (
          <div className="w-full flex flex-col gap-4">
            <div className="flex flex-col gap-2 mb-2">
              <label className="text-left text-sm text-text-secondary font-semibold">Quantos meses deseja renovar?</label>
              <div className="flex bg-bg-primary p-1 rounded-xl border border-bg-tertiary">
                {[1, 2, 3, 6].map(num => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setMeses(num)}
                    className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${meses === num ? 'bg-accent-primary text-white shadow-md' : 'text-text-secondary hover:text-white'}`}
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
              onClick={handlePagarPix}
              disabled={loading}
              className="w-full bg-accent-primary hover:bg-accent-hover text-white font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 transform active:scale-95 shadow-lg shadow-accent-primary/20"
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              ) : (
                `💠 Pagar via PIX (R$ ${valorTotal})`
              )}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center mt-4 w-full">
            <h3 className="text-lg font-bold text-accent-primary mb-2">Escaneie o QR Code</h3>
            <img 
              src={`data:image/png;base64,${pixData.qr_code_base64}`} 
              alt="QR Code PIX" 
              className="w-48 h-48 rounded-lg border-2 border-bg-tertiary mb-4"
            />
            
            <p className="text-text-secondary text-sm mb-2">Ou copie o código abaixo:</p>
            <div className="flex w-full gap-2 mb-6">
              <input 
                type="text" 
                value={pixData.qr_code} 
                readOnly 
                className="flex-1 bg-bg-primary border border-bg-tertiary text-text-primary rounded-lg px-3 py-2 text-sm outline-none w-full"
              />
              <button 
                onClick={handleCopy}
                className="bg-bg-tertiary hover:bg-opacity-80 text-text-primary px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap"
              >
                {copied ? '✅ Copiado!' : 'Copiar'}
              </button>
            </div>
            
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-green-500/20"
            >
              ✅ Já fiz o pagamento
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}

export default Assinatura;
