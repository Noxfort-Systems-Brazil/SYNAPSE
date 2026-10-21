// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/wizard/add_source/useAddSourceForm.ts
// Author: Gabriel Moraes
// Date: 2026-09-14

import { useState, useEffect } from 'react';
import { sensorService, systemService } from '../../../services/api';
import { useSensorsStore, useTopologyStore } from '../../../stores';

export function useAddSourceForm(isOpen: boolean, onClose: () => void) {
  const { sources, setSources, associateSourceToElement } = useSensorsStore();
  const edges = useTopologyStore((s) => s.edges);
  const nodes = useTopologyStore((s) => s.nodes);

  const resolveLocationId = (loc: string): string => {
    const trimmed = loc.trim();
    if (!trimmed) return '';
    const matchEdge = edges.find(
      (e) =>
        e.id === trimmed ||
        (e.name && e.name.toLowerCase() === trimmed.toLowerCase())
    );
    if (matchEdge) return matchEdge.id;
    const matchNode = nodes.find(
      (n) =>
        n.id === trimmed ||
        (n.name && n.name.toLowerCase() === trimmed.toLowerCase())
    );
    if (matchNode) return matchNode.id;
    return trimmed;
  };

  const [step, setStep] = useState<1 | 2>(1);
  const [sourceType, setSourceType] = useState<'LOCAL' | 'GLOBAL'>('LOCAL');
  const [sourceName, setSourceName] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [globalUrl, setGlobalUrl] = useState('');
  const [isBatchModalOpen, setIsBatchModalOpen] = useState<boolean>(false);

  // Local Edge generated info
  const [localIp, setLocalIp] = useState('127.0.0.1');
  const [gatewayPort, setGatewayPort] = useState(8081);
  const [unifiedEndpoint, setUnifiedEndpoint] = useState<string>('');
  const [isDuckDnsActive, setIsDuckDnsActive] = useState<boolean>(false);
  const [sourceId, setSourceId] = useState('');
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const getNextLocalId = (currentSources: typeof sources) => {
    const existingNums = currentSources
      .map((s) => {
        const m = s.id.match(/^src_(\d+)$/i);
        return m ? parseInt(m[1], 10) : 0;
      })
      .filter((n) => n > 0);

    let nextNum = 1;
    while (existingNums.includes(nextNum)) {
      nextNum++;
    }
    return `src_${nextNum}`;
  };

  useEffect(() => {
    if (isOpen) {
      if (sourceType === 'LOCAL') {
        setSourceId(getNextLocalId(sources));
      } else {
        setSourceId(`api_global_${Math.random().toString(36).substring(2, 7)}`);
      }
      systemService
        .getNetworkInfo()
        .then((res: any) => {
          if (res?.local_ip) setLocalIp(res.local_ip);
          if (res?.gateway_port) setGatewayPort(res.gateway_port);
          if (res?.unified_endpoint) setUnifiedEndpoint(res.unified_endpoint);
          if (typeof res?.duckdns_enabled === 'boolean') {
            setIsDuckDnsActive(res.duckdns_enabled);
            if (!res.duckdns_enabled && sourceType === 'LOCAL') {
              setSourceType('GLOBAL');
            }
          }
        })
        .catch(() => {});
    }
  }, [isOpen, sourceType, sources]);

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleRegister = async () => {
    const finalName =
      sourceName.trim() ||
      (sourceType === 'LOCAL' ? `Fonte Local (${sourceId})` : `Fonte Global (${sourceId})`);
    const trimmedLocation = selectedLocation.trim();

    const finalIngressUrl = unifiedEndpoint
      ? `${unifiedEndpoint}/${sourceId}`
      : `http://${localIp}:${gatewayPort}/${sourceId}`;

    if (sourceType === 'GLOBAL') {
      await sensorService.addSource({
        id: sourceId,
        name: finalName,
        is_local: false,
        connection: globalUrl.trim(),
      });
    } else {
      if (!isDuckDnsActive) {
        alert('DuckDNS Obrigatório: Não é permitido cadastrar ou conectar sensores locais sem o DuckDNS configurado e ativo. Acesse Configurações > Acesso Remoto.');
        return;
      }
      const resolvedLocation = resolveLocationId(trimmedLocation);
      await sensorService.addSource({
        id: sourceId,
        name: finalName,
        is_local: true,
        connection: finalIngressUrl,
        location: resolvedLocation || undefined,
        associated_element: resolvedLocation || undefined,
      });

      if (resolvedLocation) {
        await sensorService.associateSource(sourceId, resolvedLocation).catch(() => {});
        associateSourceToElement(sourceId, resolvedLocation);
      }
    }

    const fresh = await sensorService.getSources().catch(() => []);
    if (fresh && fresh.length > 0) {
      setSources(fresh);
    }

    onClose();
    setStep(1);
    setSourceName('');
    setSelectedLocation('');
    setGlobalUrl('');
  };

  const finalIngressUrl = unifiedEndpoint
    ? `${unifiedEndpoint}/${sourceId}`
    : `http://${localIp}:${gatewayPort}/${sourceId}`;

  const handleClose = () => {
    onClose();
    setStep(1);
    setSourceName('');
    setSelectedLocation('');
    setGlobalUrl('');
  };

  return {
    step,
    setStep,
    sourceType,
    setSourceType,
    sourceName,
    setSourceName,
    selectedLocation,
    setSelectedLocation,
    globalUrl,
    setGlobalUrl,
    isBatchModalOpen,
    setIsBatchModalOpen,
    localIp,
    gatewayPort,
    unifiedEndpoint,
    isDuckDnsActive,
    ingressUrl: finalIngressUrl,
    sourceId,
    copiedField,
    handleCopy,
    handleRegister,
    handleClose,
  };
}
