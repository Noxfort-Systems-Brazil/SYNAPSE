// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useEffect, useMemo } from 'react';
import { useSecurityStore } from '../../../../stores';
import {
  validatePassword,
  getPasswordRequirements,
  PasswordRequirement,
  PasswordValidationResult,
} from '../../../../utils/passwordPolicy';

export interface AccountFeedback {
  type: 'success' | 'error';
  message: string;
}

export function useAccountSettings() {
  const {
    registeredUsers,
    isLoadingUsers,
    fetchUsers,
    addUser,
    removeUser,
  } = useSecurityStore();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'OPERATOR' | 'SUPERUSER'>('OPERATOR');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<AccountFeedback | null>(null);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const passwordValidation = useMemo(() => validatePassword(password), [password]);
  const passwordsMatch = password.length > 0 && password === confirmPassword;
  const requirements: PasswordRequirement[] = useMemo(
    () => getPasswordRequirements(passwordValidation, passwordsMatch),
    [passwordValidation, passwordsMatch]
  );
  const canSubmit =
    username.trim().length > 0 &&
    passwordValidation.isValid &&
    passwordsMatch &&
    !isSubmitting;


  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) return;

    if (!passwordValidation.isValid) {
      setFeedback({
        type: 'error',
        message: 'A senha informada não atende aos requisitos modernos de segurança.',
      });
      return;
    }

    if (password !== confirmPassword) {
      setFeedback({
        type: 'error',
        message: 'A confirmação de senha não coincide com a senha digitada.',
      });
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);

    const res = await addUser(username.trim(), password, role);
    setIsSubmitting(false);

    if (res.success) {
      setFeedback({
        type: 'success',
        message: `Usuário '${username.trim()}' adicionado com sucesso (${role}).`,
      });
      setUsername('');
      setPassword('');
      setConfirmPassword('');
      setRole('OPERATOR');
    } else {
      setFeedback({
        type: 'error',
        message: res.error || 'Falha ao adicionar usuário. Verifique se o usuário já existe.',
      });
    }
  };

  const handleRemoveUser = async (targetUser: string) => {
    if (targetUser === 'admin') return;
    if (!window.confirm(`Tem certeza que deseja remover o usuário '${targetUser}'?`)) return;

    setFeedback(null);
    const success = await removeUser(targetUser);
    if (success) {
      setFeedback({
        type: 'success',
        message: `Usuário '${targetUser}' removido com sucesso.`,
      });
    } else {
      setFeedback({
        type: 'error',
        message: `Erro ao remover usuário '${targetUser}'.`,
      });
    }
  };

  return {
    username,
    setUsername,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    role,
    setRole,
    isSubmitting,
    feedback,
    setFeedback,
    registeredUsers,
    isLoadingUsers,
    fetchUsers,
    passwordValidation,
    passwordsMatch,
    requirements,
    canSubmit,
    handleAddUser,
    handleRemoveUser,
  };
}


