// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { UserCheck } from 'lucide-react';
import { useSecurityStore, UserSession } from '../../../stores';

interface HeaderUserBadgeProps {
  user?: UserSession | null;
}

/**
 * Atomic subcomponent for displaying the authenticated user session and profile (SRP).
 */
export const HeaderUserBadge: React.FC<HeaderUserBadgeProps> = ({ user: propUser }) => {
  const storeUser = useSecurityStore((s) => s.currentUser);
  const user = propUser !== undefined ? propUser : storeUser;

  if (!user) return null;

  const isOperator = user.role === 'OPERATOR';

  return (
    <div
      title={`Sessão autenticada: ${user.username} (${user.role})`}
      className="hidden md:flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg bg-surface border border-border text-slate-700 dark:text-slate-300 shadow-sm shrink-0 whitespace-nowrap"
    >
      <UserCheck className={`w-3.5 h-3.5 shrink-0 ${isOperator ? 'text-accent-cyan' : 'text-amber-500'}`} />
      <span className="truncate max-w-[100px] lg:max-w-[140px]">{user.username}</span>
      <span className="text-[10px] px-1 py-0.2 rounded bg-primary-500/10 text-primary-500 font-bold shrink-0">
        {user.role}
      </span>
    </div>
  );
};
