// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { CheckCircle2, AlertTriangle, Plug, Unplug, Wrench } from 'lucide-react';

interface DatabaseActionButtonsProps {
  isConnected: boolean;
  isSetupDone: boolean;
  dbLoading: boolean;
  dbFeedback: { ok: boolean; msg: string } | null;
  onConnect: () => void;
  onDisconnect: () => void;
  onInitializeDb: () => void;
}

export const DatabaseActionButtons: React.FC<DatabaseActionButtonsProps> = ({
  isConnected,
  isSetupDone,
  dbLoading,
  dbFeedback,
  onConnect,
  onDisconnect,
  onInitializeDb,
}) => {
  return (
    <>
      {/* Feedback alert */}
      {dbFeedback && (
        <div
          className={`p-3 rounded-xl flex items-center gap-2 border ${
            dbFeedback.ok
              ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-300'
              : 'bg-rose-50 dark:bg-rose-950/60 border-rose-200 dark:border-rose-500/40 text-rose-700 dark:text-rose-300'
          }`}
        >
          {dbFeedback.ok ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400" />
          )}
          <span>{dbFeedback.msg}</span>
        </div>
      )}

      {/* DB Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-border/80">
        {isConnected ? (
          <button
            onClick={onDisconnect}
            disabled={dbLoading}
            className="px-4 py-2 rounded-xl font-semibold flex items-center gap-2 transition-all bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-700/60 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-900/60 shadow-xs cursor-pointer"
          >
            <Unplug className="w-4 h-4 text-rose-500" />
            Desconectar
          </button>
        ) : (
          <button
            onClick={onConnect}
            disabled={dbLoading}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-xl font-bold shadow-md shadow-primary-600/20 flex items-center gap-2 transition-all cursor-pointer"
          >
            {dbLoading ? (
              'Conectando...'
            ) : (
              <>
                <Plug className="w-4 h-4" />
                Conectar ao Banco
              </>
            )}
          </button>
        )}

        <button
          onClick={onInitializeDb}
          disabled={dbLoading || isSetupDone}
          className={`px-4 py-2 rounded-xl font-bold shadow-md flex items-center gap-2 transition-all ${
            isSetupDone
              ? 'bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-400 dark:border-emerald-500/60 text-emerald-700 dark:text-emerald-300 shadow-none cursor-default'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20 cursor-pointer'
          }`}
        >
          {dbLoading ? (
            'Processando...'
          ) : isSetupDone ? (
            <>
              <CheckCircle2 className="w-4 h-4" /> Configurado ✓
            </>
          ) : (
            <>
              <Wrench className="w-4 h-4" /> Criar Usuário, Schema e Tabelas
            </>
          )}
        </button>
      </div>
    </>
  );
};
