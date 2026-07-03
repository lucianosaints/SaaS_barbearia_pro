import React, { useEffect } from 'react';
import useAgendamentoStore from '../store/useAgendamentoStore';

/**
 * Componente ProtectedRoute.
 * Protege abas/rotas verificando token e perfil de acesso do usuário.
 * 
 * @param {object} props
 * @param {React.ReactNode} props.children - Componente protegido
 * @param {string[]} props.allowedRoles - Perfis autorizados a acessar
 * @param {function} props.onDenied - Ação executada ao negar acesso (ex: redirecionar aba)
 */
export default function ProtectedRoute({ children, allowedRoles, onDenied }) {
  const { userToken, userTipo } = useAgendamentoStore();

  useEffect(() => {
    // Caso não esteja logado
    if (!userToken) {
      onDenied();
      return;
    }

    // Caso o tipo do usuário não esteja autorizado
    if (allowedRoles && !allowedRoles.includes(userTipo)) {
      onDenied();
    }
  }, [userToken, userTipo, allowedRoles, onDenied]);

  if (!userToken || (allowedRoles && !allowedRoles.includes(userTipo))) {
    return null;
  }

  return children;
}
