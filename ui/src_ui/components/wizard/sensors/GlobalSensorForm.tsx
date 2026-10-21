// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

export interface GlobalSensorFormProps {
  globalUrl: string;
  onChangeGlobalUrl: (url: string) => void;
}

export const GlobalSensorForm: React.FC<GlobalSensorFormProps> = ({
  globalUrl,
  onChangeGlobalUrl,
}) => {
  return (
    <div className="space-y-1.5">
      <label className="text-slate-700 dark:text-slate-300 font-semibold text-xs">
        Endpoint URL (REST / Stream):
      </label>
      <input
        type="text"
        placeholder="https://api.provedor.com/v1/traffic"
        value={globalUrl}
        onChange={(e) => onChangeGlobalUrl(e.target.value)}
        className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs"
      />
    </div>
  );
};
