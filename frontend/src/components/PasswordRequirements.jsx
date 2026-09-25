import React from 'react';
import { FiCheck, FiX } from 'react-icons/fi';

export const passwordChecks = (password = '') => [
  { label: 'Pelo menos 8 caracteres', valid: password.length >= 8 },
  { label: 'Uma letra maiúscula', valid: /[A-Z]/.test(password) },
  { label: 'Uma letra minúscula', valid: /[a-z]/.test(password) },
  { label: 'Um número', valid: /\d/.test(password) },
  { label: 'Um caractere especial', valid: /[^A-Za-z0-9]/.test(password) },
];

export const isPasswordReady = (password) => passwordChecks(password).every((item) => item.valid);

export default function PasswordRequirements({ password, confirmation }) {
  const checks = passwordChecks(password);
  if (confirmation !== undefined) {
    checks.push({ label: 'As duas senhas são iguais', valid: Boolean(password) && password === confirmation });
  }

  return (
    <div className="mt-2 grid gap-1 sm:grid-cols-2" aria-live="polite">
      {checks.map(({ label, valid }) => (
        <span key={label} className={`flex items-center gap-1.5 text-xs ${valid ? 'text-emerald-400' : 'text-text-muted'}`}>
          {valid ? <FiCheck aria-hidden="true" /> : <FiX aria-hidden="true" />}
          {label}
        </span>
      ))}
    </div>
  );
}
