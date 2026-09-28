import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const nginx = readFileSync(new URL('./nginx.conf', import.meta.url), 'utf8');

describe('cabecalhos de seguranca do frontend', () => {
  it.each([
    'Content-Security-Policy',
    'Permissions-Policy',
    'Referrer-Policy',
    'X-Content-Type-Options',
    'X-Frame-Options',
    'Cross-Origin-Opener-Policy',
    'Cross-Origin-Resource-Policy',
  ])('envia %s inclusive em respostas de erro', (header) => {
    expect(nginx).toMatch(new RegExp(`add_header\\s+${header}\\s+.+\\s+always;`));
  });

  it('restringe scripts, objetos, formularios e enquadramento', () => {
    expect(nginx).toContain("script-src 'self'");
    expect(nginx).toContain("object-src 'none'");
    expect(nginx).toContain("form-action 'self'");
    expect(nginx).toContain("frame-ancestors 'none'");
  });
});
