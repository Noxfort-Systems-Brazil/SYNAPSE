// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Shield, User, Trash2, RefreshCw } from 'lucide-react';
import { UserAccount } from '../../../../services/api';

interface AccountUserTableProps {
  users: UserAccount[];
  isLoading: boolean;
  onRefresh: () => void;
  onRemove: (username: string) => Promise<void>;
}

export const AccountUserTable: React.FC<AccountUserTableProps> = ({
  users,
  isLoading,
  onRefresh,
  onRemove,
}) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Shield className="w-4 h-4 text-accent-cyan" />
          <span>
            {t('accounts.registeredAccounts', 'Contas Cadastradas:')} ({users.length})
          </span>
        </h3>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          title={t('accounts.refreshList', 'Atualizar Lista')}
          className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="border border-border rounded-xl bg-background/50 divide-y divide-border/60 max-h-56 overflow-y-auto">
        {users.length === 0 ? (
          <div className="p-4 text-center text-slate-400">
            {isLoading ? 'Carregando contas...' : 'Nenhuma conta cadastrada.'}
          </div>
        ) : (
          users.map((user: UserAccount) => {
            const isSuper = user.role === 'SUPERUSER';
            return (
              <div
                key={user.username}
                className="p-3 flex items-center justify-between hover:bg-surfaceHover/50 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                      isSuper
                        ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                        : 'bg-primary-500/10 text-primary-500 border border-primary-500/20'
                    }`}
                  >
                    {isSuper ? <Shield className="w-3.5 h-3.5" /> : <User className="w-3.5 h-3.5" />}
                  </div>
                  <div>
                    <span className="font-bold text-slate-900 dark:text-white">
                      {user.username}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                      isSuper
                        ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30'
                        : 'bg-primary-500/15 text-primary-600 dark:text-primary-400 border-primary-500/30'
                    }`}
                  >
                    {user.role}
                  </span>

                  <button
                    onClick={() => onRemove(user.username)}
                    title={`Remover ${user.username}`}
                    className="p-1 rounded text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
