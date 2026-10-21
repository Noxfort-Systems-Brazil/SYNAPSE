// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/duckdns/useDuckDnsSettings.ts
// Description: Custom hook encapsulating DuckDNS state, API communication and validation.

import { useState, useEffect } from 'react';
import { duckDnsService, DuckDnsConfig } from '../../../../services/api';

export function useDuckDnsSettings() {
  const [config, setConfig] = useState<DuckDnsConfig>({
    status: 'DISCONNECTED',
    enabled: false,
    domain: '',
    token: '',
    caddy_enabled: true,
    port: 8081,
    https_port: 443,
    public_url: '',
    caddy_running: false,
  });

  const [domainInput, setDomainInput] = useState('');
  const [tokenInput, setTokenInput] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [caddyEnabled, setCaddyEnabled] = useState(true);

  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; msg: string } | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await duckDnsService.getConfig();
        if (mounted && data) {
          setConfig(data);
          setDomainInput(data.domain || '');
          setTokenInput(data.token || '');
          setCaddyEnabled(data.caddy_enabled ?? true);
        }
      } catch (err) {
        console.warn('Erro ao carregar configurações do DuckDNS:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const cleanDomain = (d: string) => {
    let clean = d.trim().toLowerCase().replace('https://', '').replace('http://', '').replace(/\/$/, '');
    if (clean.endsWith('.duckdns.org')) {
      clean = clean.slice(0, -'.duckdns.org'.length);
    }
    return clean.trim();
  };

  const previewDomain = cleanDomain(domainInput);
  const previewUrl = previewDomain
    ? config.https_port === 443
      ? `https://${previewDomain}.duckdns.org`
      : `https://${previewDomain}.duckdns.org:${config.https_port}`
    : '';

  const handleCopy = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTest = async () => {
    const d = cleanDomain(domainInput);
    const t = tokenInput.trim();
    if (!d || !t) {
      setFeedback({
        ok: false,
        msg: 'Preencha o Subdomínio e o Token antes de testar a conexão.',
      });
      return;
    }

    setTesting(true);
    setFeedback(null);
    try {
      const res = await duckDnsService.testConnection(d, t);
      if (res.status === 'ok') {
        setFeedback({
          ok: true,
          msg: res.message || `Conexão bem-sucedida com DuckDNS (${res.latency_ms ?? 0} ms)!`,
        });
      } else {
        setFeedback({
          ok: false,
          msg: res.error || 'Falha ao validar credenciais do DuckDNS.',
        });
      }
    } catch (err: any) {
      setFeedback({
        ok: false,
        msg: `Erro no teste de conexão: ${err.message || err}`,
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveAndApply = async (enableState: boolean) => {
    const d = cleanDomain(domainInput);
    const t = tokenInput.trim();

    if (enableState && (!d || !t)) {
      setFeedback({
        ok: false,
        msg: 'Informe o Subdomínio e o Token para ativar o serviço.',
      });
      return;
    }

    setSaving(true);
    setFeedback(null);
    try {
      const res = await duckDnsService.saveConfig({
        domain: d,
        token: t,
        enabled: enableState,
        caddy_enabled: caddyEnabled,
        port: config.port || 8081,
        https_port: config.https_port || 443,
      });

      if (res.status === 'ok') {
        const fresh = await duckDnsService.getConfig();
        setConfig(fresh);
        setFeedback({
          ok: true,
          msg: enableState
            ? '✅ DuckDNS ativado com sucesso! Gateway e Caddy SSL estão operacionais.'
            : 'Serviço DuckDNS desativado.',
        });
      } else {
        setFeedback({
          ok: false,
          msg: 'Erro ao salvar configurações do DuckDNS.',
        });
      }
    } catch (err: any) {
      setFeedback({
        ok: false,
        msg: `Falha ao salvar: ${err.message || err}`,
      });
    } finally {
      setSaving(false);
    }
  };

  const isOnline = config.enabled && config.status === 'ONLINE';

  return {
    config,
    domainInput,
    setDomainInput,
    tokenInput,
    setTokenInput,
    showToken,
    setShowToken,
    caddyEnabled,
    setCaddyEnabled,
    loading,
    testing,
    saving,
    copied,
    feedback,
    cleanDomain,
    previewUrl,
    handleCopy,
    handleTest,
    handleSaveAndApply,
    isOnline,
  };
}
