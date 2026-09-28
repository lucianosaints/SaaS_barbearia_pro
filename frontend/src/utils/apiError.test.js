import { describe, expect, it } from 'vitest';
import { formatApiError } from './apiError';

describe('formatApiError', () => {
  it('mostra erros de validação associados a campos', () => {
    expect(formatApiError({ response: { data: { cliente: ['Informe o cliente.'] } } }))
      .toBe('Cliente: Informe o cliente.');
  });

  it('orienta a conferir a agenda quando o navegador expira', () => {
    expect(formatApiError({ code: 'ECONNABORTED' }))
      .toContain('Confira “Minha Agenda”');
  });
});
