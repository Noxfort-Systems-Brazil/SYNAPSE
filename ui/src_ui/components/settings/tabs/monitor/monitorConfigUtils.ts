// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export const MONITOR_STORAGE_KEY = 'synapse_monitor_settings_v1';

export const getSavedMonitorSettings = () => {
  try {
    const raw = localStorage.getItem(MONITOR_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error('Error loading monitor settings from localStorage:', e);
  }
  return null;
};

export const parseTargetConfig = (rawTarget: string) => {
  const clean = rawTarget.trim();
  const isHttp = clean.startsWith('http://') || clean.startsWith('https://') || clean.includes('/api');

  if (isHttp) {
    const fullUrl = clean.startsWith('http://') || clean.startsWith('https://') ? clean : `https://${clean}`;
    try {
      const url = new URL(fullUrl);
      return {
        isHttp: true,
        host: url.hostname,
        port: url.port ? Number(url.port) : url.protocol === 'https:' ? 443 : 80,
        protocol: url.protocol.replace(':', '').toUpperCase(),
        cleanTarget: fullUrl,
      };
    } catch {
      return {
        isHttp: true,
        host: clean,
        port: clean.startsWith('https://') ? 443 : 80,
        protocol: 'HTTP',
        cleanTarget: fullUrl,
      };
    }
  }

  // Remove tcp:// or mqtt:// prefix if typed
  let withoutScheme = clean;
  if (withoutScheme.startsWith('tcp://')) {
    withoutScheme = withoutScheme.slice(6);
  } else if (withoutScheme.startsWith('mqtt://')) {
    withoutScheme = withoutScheme.slice(7);
  }

  if (withoutScheme.includes(':')) {
    const lastColon = withoutScheme.lastIndexOf(':');
    const host = withoutScheme.substring(0, lastColon).trim();
    const portStr = withoutScheme.substring(lastColon + 1).trim();
    const port = Number(portStr);
    return {
      isHttp: false,
      host: host || 'localhost',
      port: isNaN(port) ? 1883 : port,
      protocol: 'MQTT',
      cleanTarget: withoutScheme,
    };
  }

  return {
    isHttp: false,
    host: withoutScheme || 'localhost',
    port: 1883,
    protocol: 'MQTT',
    cleanTarget: withoutScheme || 'localhost',
  };
};
