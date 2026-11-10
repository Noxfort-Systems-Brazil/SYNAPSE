// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

interface MonitorConnectionFormProps {
  telemetryIp: string;
  onIpChange: (val: string) => void;
  isHttp: boolean;
}

export const MonitorConnectionForm: React.FC<MonitorConnectionFormProps> = ({
  telemetryIp,
  onIpChange,
  isHttp,
}) => {
  return (
    <div className="space-y-1.5">
      <label className="text-slate-700 dark:text-slate-300 font-semibold">
        Endereço do Servidor / Endpoint ou Broker:
      </label>
      <input
        type="text"
        value={telemetryIp}
        onChange={(e) => onIpChange(e.target.value)}
        placeholder="Ex: https://seu-ngrok.ngrok-free.dev/api/telemetry ou 192.168.1.50:1883"
        className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl font-mono text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
      />
      <span className="text-[11px] text-slate-500 dark:text-slate-400 block">
        {isHttp ? (
          <span className="text-primary-600 dark:text-primary-400 font-medium">
            ✓ URL HTTP/HTTPS detectada (ngrok / Web API). Envio via <code>HTTP POST</code> com payload JSON.
          </span>
        ) : (
          <span>
            Endereço MQTT detectado. A porta padrão <code>1883</code> é atribuída automaticamente se omitida.
          </span>
        )}
      </span>
    </div>
  );
};
