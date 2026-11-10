// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useEffect } from 'react';
import { systemService } from '../../../../services/api';
import { useSystemStore } from '../../../../stores';
import {
  MONITOR_STORAGE_KEY,
  getSavedMonitorSettings,
  parseTargetConfig,
} from './monitorConfigUtils';

export function useMonitorSettings() {
  const saved = getSavedMonitorSettings();
  const { setMonitorStatus } = useSystemStore();

  const [telemetryIp, setTelemetryIp] = useState<string>(
    saved?.ip ??
      (saved?.host
        ? saved?.port && saved.port !== 1883
          ? `${saved.host}:${saved.port}`
          : saved.host
        : 'localhost')
  );
  const [isConnected, setIsConnected] = useState<boolean>(saved?.connected ?? false);
  const [testing, setTesting] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; msg: string } | null>(null);

  const parsedConfig = parseTargetConfig(telemetryIp);

  // Load persistent telemetry settings from backend settings.ini on mount
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const backendCfg = await systemService.getTelemetryConfig();
        if (mounted && backendCfg) {
          const loadedIp =
            backendCfg.ip ||
            (backendCfg.host
              ? backendCfg.port && backendCfg.port !== 1883
                ? `${backendCfg.host}:${backendCfg.port}`
                : backendCfg.host
              : 'localhost');
          setTelemetryIp(loadedIp);
          if (typeof backendCfg.connected === 'boolean') {
            setIsConnected(backendCfg.connected);
            setMonitorStatus({
              connected: backendCfg.connected,
              ip: loadedIp,
              host: backendCfg.host || 'localhost',
              port: backendCfg.port || 1883,
              message: backendCfg.connected ? `Conectado em ${loadedIp}` : 'Desconectado',
            });
          }
        }
      } catch (e) {
        console.warn('Could not load telemetry settings from backend:', e);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [setMonitorStatus]);

  // Persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(
        MONITOR_STORAGE_KEY,
        JSON.stringify({
          ip: telemetryIp,
          host: parsedConfig.host,
          port: parsedConfig.port,
          protocol: parsedConfig.protocol,
          connected: isConnected,
        })
      );
    } catch (e) {
      console.error('Error saving monitor settings to localStorage:', e);
    }
  }, [telemetryIp, isConnected, parsedConfig]);

  const handleIpChange = (newIp: string) => {
    setTelemetryIp(newIp);
    setIsConnected(false);
    setFeedback(null);
    setMonitorStatus({ connected: false, message: 'Configurações alteradas' });
  };

  const handleConnect = async () => {
    setTesting(true);
    setFeedback(null);
    try {
      const target = parseTargetConfig(telemetryIp);

      // Real reachability test via backend
      const testRes = await systemService.testTelemetryConnection({
        ip: target.cleanTarget,
        host: target.host,
        port: target.port,
      });

      if (testRes && testRes.success) {
        setIsConnected(true);
        setMonitorStatus({
          connected: true,
          ip: target.cleanTarget,
          host: target.host,
          port: target.port,
          message: `Conectado via ${target.protocol} em ${target.cleanTarget}`,
        });
        setFeedback({
          ok: true,
          msg:
            testRes.message ||
            `Conectado com sucesso via ${target.protocol} (${target.cleanTarget})! Transmissão ativada.`,
        });
        await systemService.saveTelemetryConfig({
          ip: target.cleanTarget,
          host: target.host,
          port: target.port,
          connected: true,
        });
      } else {
        setIsConnected(false);
        setMonitorStatus({ connected: false, message: 'Falha na conexão' });
        setFeedback({
          ok: false,
          msg:
            testRes?.message ||
            `Não foi possível conectar ao servidor (${target.cleanTarget}).`,
        });
      }
    } catch (err: any) {
      setIsConnected(false);
      setMonitorStatus({ connected: false, message: 'Falha na conexão' });
      setFeedback({
        ok: false,
        msg: err?.message || 'Falha ao testar conexão com o servidor de telemetria.',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = async () => {
    setIsConnected(false);
    setMonitorStatus({ connected: false, message: 'Desconectado pelo usuário' });
    setFeedback({ ok: true, msg: 'Telemetria externa desconectada com sucesso.' });
    try {
      const target = parseTargetConfig(telemetryIp);
      await systemService.saveTelemetryConfig({
        ip: target.cleanTarget,
        host: target.host,
        port: target.port,
        connected: false,
      });
    } catch {}
  };

  return {
    telemetryIp,
    isConnected,
    testing,
    feedback,
    parsedConfig,
    handleIpChange,
    handleConnect,
    handleDisconnect,
  };
}
