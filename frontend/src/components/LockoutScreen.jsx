import React from 'react';
import { motion } from 'framer-motion';

export default function LockoutScreen() {
  const handleCheckout = () => {
    // Redireciona para a rota ou tela de checkout da assinatura.
    // Como a API já foi criada (api/assinaturas/checkout/), pode ser uma chamada API ou redirect
    window.location.href = '/api/assinaturas/checkout/'; // Ou roteamento React, dependendo do design
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

        <button
          onClick={handleCheckout}
          className="w-full bg-primary hover:bg-primary-hover text-bg-primary font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_15px_rgba(212,175,55,0.4)]"
        >
          Regularizar Assinatura
        </button>
      </motion.div>
    </div>
  );
}
