import { describe, expect, it } from 'vitest';
import { isPasswordReady, passwordChecks } from './PasswordRequirements';

describe('password requirements', () => {
  it('rejects passwords missing any displayed requirement', () => {
    expect(isPasswordReady('apenasletras')).toBe(false);
    expect(isPasswordReady('SEM-MINUSCULA1!')).toBe(false);
    expect(isPasswordReady('SemNumero!')).toBe(false);
    expect(isPasswordReady('SemEspecial1')).toBe(false);
    expect(isPasswordReady('Aa1!')).toBe(false);
  });

  it('accepts a password when every displayed requirement is met', () => {
    expect(isPasswordReady('SenhaForte!2026')).toBe(true);
    expect(passwordChecks('SenhaForte!2026').every((item) => item.valid)).toBe(true);
  });
});
