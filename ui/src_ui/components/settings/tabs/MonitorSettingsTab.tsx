// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import {
  useMonitorSettings,
  MonitorStatusHeader,
  MonitorConnectionForm,
  MonitorActionButtons,
} from './monitor';

export const MonitorSettingsTab: React.FC = () => {
  const mon = useMonitorSettings();

  return (
    <div className="space-y-4 text-xs">
      <MonitorStatusHeader
        isConnected={mon.isConnected}
        protocol={mon.parsedConfig.protocol}
        isHttp={mon.parsedConfig.isHttp}
      />

      <MonitorConnectionForm
        telemetryIp={mon.telemetryIp}
        onIpChange={mon.handleIpChange}
        isHttp={mon.parsedConfig.isHttp}
      />

      <MonitorActionButtons
        isConnected={mon.isConnected}
        testing={mon.testing}
        feedback={mon.feedback}
        onConnect={mon.handleConnect}
        onDisconnect={mon.handleDisconnect}
      />
    </div>
  );
};
