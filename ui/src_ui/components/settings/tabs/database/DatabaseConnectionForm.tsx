// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

interface DatabaseConnectionFormProps {
  dbHost: string;
  setDbHost: (val: string) => void;
  dbPort: number;
  setDbPort: (val: number) => void;
  dbName: string;
  setDbName: (val: string) => void;
  dbSchema: string;
  setDbSchema: (val: string) => void;
  dbUser: string;
  setDbUser: (val: string) => void;
  dbPass: string;
  setDbPass: (val: string) => void;
  dbRootPass: string;
  setDbRootPass: (val: string) => void;
  onFieldChange: (setter: (val: any) => void) => (val: any) => void;
}

export const DatabaseConnectionForm: React.FC<DatabaseConnectionFormProps> = ({
  dbHost,
  setDbHost,
  dbPort,
  setDbPort,
  dbName,
  setDbName,
  dbSchema,
  setDbSchema,
  dbUser,
  setDbUser,
  dbPass,
  setDbPass,
  dbRootPass,
  setDbRootPass,
  onFieldChange,
}) => {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">Host:</label>
        <input
          type="text"
          value={dbHost}
          onChange={(e) => onFieldChange(setDbHost)(e.target.value)}
          className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>
      <div className="space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">Porta:</label>
        <input
          type="number"
          value={dbPort}
          onChange={(e) => onFieldChange(setDbPort)(Number(e.target.value))}
          className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>
      <div className="space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">Nome do Banco:</label>
        <input
          type="text"
          value={dbName}
          onChange={(e) => onFieldChange(setDbName)(e.target.value)}
          placeholder="Ex: synapse_db"
          className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>
      <div className="space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">Schema do SYNAPSE:</label>
        <input
          type="text"
          value={dbSchema}
          onChange={(e) => onFieldChange(setDbSchema)(e.target.value)}
          placeholder="schema_synapse"
          className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>
      <div className="space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">Usuário:</label>
        <input
          type="text"
          value={dbUser}
          onChange={(e) => onFieldChange(setDbUser)(e.target.value)}
          placeholder="Ex: user_synapse ou postgres"
          className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>
      <div className="space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">Senha:</label>
        <input
          type="password"
          value={dbPass}
          onChange={(e) => onFieldChange(setDbPass)(e.target.value)}
          placeholder="••••••••"
          className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>
      <div className="col-span-2 space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">
          Senha do Usuário Root / Postgres (necessária apenas para criar usuário e schema):
        </label>
        <input
          type="password"
          value={dbRootPass}
          placeholder="Digite a senha master se for criar novo usuário/schema"
          onChange={(e) => setDbRootPass(e.target.value)}
          className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>
    </div>
  );
};
