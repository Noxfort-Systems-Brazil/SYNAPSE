// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';
import {
  useAccountSettings,
  AccountCreateForm,
  AccountUserTable,
} from './account';

export const AccountSettingsTab: React.FC = () => {
  const {
    username,
    setUsername,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    role,
    setRole,
    passwordValidation,
    requirements,
    passwordsMatch,
    canSubmit,
    isSubmitting,
    feedback,
    setFeedback,
    registeredUsers,
    isLoadingUsers,
    fetchUsers,
    handleAddUser,
    handleRemoveUser,
  } = useAccountSettings();

  return (
    <div className="space-y-6 text-xs select-none">
      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`p-3 rounded-xl border flex items-center justify-between gap-2 animate-in fade-in ${
            feedback.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/20 text-rose-600 dark:text-rose-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 shrink-0" />
            )}
            <span className="font-medium">{feedback.message}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-[10px] uppercase font-bold opacity-60 hover:opacity-100"
          >
            Fechar
          </button>
        </div>
      )}

      {/* Add User Section */}
      <AccountCreateForm
        username={username}
        setUsername={setUsername}
        password={password}
        setPassword={setPassword}
        confirmPassword={confirmPassword}
        setConfirmPassword={setConfirmPassword}
        role={role}
        setRole={setRole}
        validation={passwordValidation}
        requirements={requirements}
        passwordsMatch={passwordsMatch}
        canSubmit={canSubmit}
        isSubmitting={isSubmitting}
        onSubmit={handleAddUser}
      />



      {/* Registered Accounts List */}
      <AccountUserTable
        users={registeredUsers}
        isLoading={isLoadingUsers}
        onRefresh={() => fetchUsers()}
        onRemove={handleRemoveUser}
      />
    </div>
  );
};
