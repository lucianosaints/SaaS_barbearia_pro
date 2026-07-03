import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function OnboardingModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="bg-bg-secondary w-full max-w-lg rounded-2xl shadow-premium border border-border-color overflow-hidden flex flex-col"
          >
            <div className="p-6 border-b border-border-color flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-white">Criar Conta SaaS</h2>
                <p className="text-sm text-text-muted mt-1">Crie sua barbearia e teste grátis por 7 dias</p>
              </div>
              <button onClick={onClose} className="text-text-muted hover:text-white transition-colors">
                ✕
              </button>
            </div>
            
            <div className="p-6">
              {/* O formulário chamará a RegistroSaaSView posteriormente */}
              <form className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Nome da Barbearia</label>
                  <input type="text" className="input-premium w-full" placeholder="Ex: Golden Barber" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Seu Nome</label>
                  <input type="text" className="input-premium w-full" placeholder="Ex: João Silva" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">E-mail Administrativo</label>
                  <input type="email" className="input-premium w-full" placeholder="seu@email.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Senha</label>
                  <input type="password" className="input-premium w-full" placeholder="••••••••" />
                </div>
                
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full mt-6 bg-primary hover:bg-primary-hover text-bg-primary font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_15px_rgba(212,175,55,0.4)]"
                >
                  Criar Conta e Iniciar Teste Grátis
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
