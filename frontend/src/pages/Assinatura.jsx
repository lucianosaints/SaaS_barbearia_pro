import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../services/api';
import { motion } from 'framer-motion';

function Assinatura() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const paymentStatus = searchParams.get('status');

  const handlePagar = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/assinaturas/criar-assinatura/');
      if (response.data.init_point) {
        window.location.href = response.data.init_point;
      } else {
        setError('Erro ao gerar o link de pagamento.');
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

        <button
          onClick={handlePagar}
          disabled={loading}
          className="w-full bg-accent-primary hover:bg-accent-hover text-white font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 transform active:scale-95 shadow-lg shadow-accent-primary/20"
        >
          {loading ? (
            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          ) : (
            <>
              💳 Pagar Mensalidade (R$ 49,99)
            </>
          )}
        </button>
      </motion.div>
    </div>
  );
}

export default Assinatura;
