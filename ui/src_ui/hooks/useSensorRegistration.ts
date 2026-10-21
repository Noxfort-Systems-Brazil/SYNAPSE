// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/hooks/useSensorRegistration.ts
// Description: Pure custom hook orchestrating sensor registration state and actions.

import { useState, useEffect, useCallback } from 'react';
import { useSensorsStore, useSecurityStore, useTopologyStore } from '../stores';
import { sensorService, systemService } from '../services/api';
import { DataSourceItem } from '../types/sensors';
import { MapEdgeData, MapNodeData } from '../types/topology';
import {
  getNextLocalId,
  resolveElementLocation,
  filterRegisteredSensors,
} from './sensorRegistrationUtils';

export interface UseSensorRegistrationReturn {
  sensorType: 'LOCAL' | 'GLOBAL';
  setSensorType: (type: 'LOCAL' | 'GLOBAL') => void;
  sensorName: string;
  setSensorName: (name: string) => void;
  selectedLocation: string;
  setSelectedLocation: (loc: string) => void;
  globalUrl: string;
  setGlobalUrl: (url: string) => void;
  localIp: string;
  gatewayPort: number;
  sensorId: string;
  copiedField: string | null;
  successMsg: string | null;
  isBatchModalOpen: boolean;
  setIsBatchModalOpen: (open: boolean) => void;
  isPickingElement: boolean;
  isDuckDnsActive: boolean;
  unifiedEndpoint: string;
  ingressUrl: string;
  edges: MapEdgeData[];
  nodes: MapNodeData[];
  registeredSensors: DataSourceItem[];
  handleCopy: (text: string, field: string) => void;
  handleRegisterSensor: () => Promise<void>;
  handleRemoveSensor: (sourceId: string) => void;
  handlePickOnMap: () => void;
}

export function useSensorRegistration(): UseSensorRegistrationReturn {
  const { sources, setSources, associateSourceToElement } = useSensorsStore();
  const edges = useTopologyStore((s) => s.edges);
  const nodes = useTopologyStore((s) => s.nodes);
  const isPickingElement = useTopologyStore((s) => s.isPickingElement);
  const startPickingElement = useTopologyStore((s) => s.startPickingElement);
  const requestAuth = useSecurityStore((s) => s.requestAuth);

  const [sensorType, setSensorType] = useState<'LOCAL' | 'GLOBAL'>('LOCAL');
  const [sensorName, setSensorName] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [globalUrl, setGlobalUrl] = useState('');
  const [localIp, setLocalIp] = useState('127.0.0.1');
  const [gatewayPort, setGatewayPort] = useState(8081);
  const [unifiedEndpoint, setUnifiedEndpoint] = useState<string>('');
  const [isDuckDnsActive, setIsDuckDnsActive] = useState<boolean>(false);
  const [sensorId, setSensorId] = useState('');
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isBatchModalOpen, setIsBatchModalOpen] = useState<boolean>(false);

  useEffect(() => {
    if (sensorType === 'LOCAL') {
      setSensorId(getNextLocalId(sources));
    } else {
      setSensorId(`api_global_${Math.random().toString(36).substring(2, 7)}`);
    }
  }, [sources, sensorType]);

  useEffect(() => {
    systemService
      .getNetworkInfo()
      .then((res: any) => {
        if (res?.local_ip) setLocalIp(res.local_ip);
        if (res?.gateway_port) setGatewayPort(res.gateway_port);
        if (res?.unified_endpoint) setUnifiedEndpoint(res.unified_endpoint);
        if (typeof res?.duckdns_enabled === 'boolean') {
          setIsDuckDnsActive(res.duckdns_enabled);
          if (!res.duckdns_enabled && sensorType === 'LOCAL') {
            setSensorType('GLOBAL');
          }
        }
      })
      .catch(() => {});
  }, [sensorType]);

  const handleCopy = useCallback((text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  }, []);

  const handleRegisterSensor = useCallback(async () => {
    const finalName =
      sensorName.trim() ||
      (sensorType === 'LOCAL' ? `Fonte Local (${sensorId})` : `Fonte Global (${sensorId})`);
    const trimmedLocation = selectedLocation.trim();

    if (sensorType === 'GLOBAL') {
      await sensorService.addSource({
        id: sensorId,
        name: finalName,
        is_local: false,
        connection: globalUrl.trim(),
      });
      setSuccessMsg(`Sensor Global "${finalName}" registrado!`);
      setGlobalUrl('');
      setSensorName('');
    } else {
      if (!isDuckDnsActive) {
        alert('DuckDNS Obrigatório: Não é permitido cadastrar ou conectar sensores locais sem o DuckDNS configurado e ativo. Acesse Configurações > Acesso Remoto.');
        return;
      }
      const endpoint = unifiedEndpoint
        ? `${unifiedEndpoint}/${sensorId}`
        : `http://${localIp}:${gatewayPort}/${sensorId}`;

      const { resolvedLocation, displayLocationName } = resolveElementLocation(
        trimmedLocation,
        edges,
        nodes
      );

      await sensorService.addSource({
        id: sensorId,
        name: finalName,
        is_local: true,
        connection: endpoint,
        source_type: 'HTTP',
        location: resolvedLocation || undefined,
        associated_element: resolvedLocation || undefined,
      });

      if (resolvedLocation) {
        await sensorService.associateSource(sensorId, resolvedLocation).catch(() => {});
        associateSourceToElement(sensorId, resolvedLocation);
      }

      setSuccessMsg(
        `Sensor "${finalName}" registrado com sucesso${
          displayLocationName ? ` vinculado à via '${displayLocationName}'!` : '!'
        }`
      );
      setSensorName('');
      setSelectedLocation('');
    }

    const fresh = await sensorService.getSources().catch(() => []);
    if (fresh && fresh.length > 0) {
      setSources(fresh);
    }
    setTimeout(() => setSuccessMsg(null), 3500);
  }, [
    sensorName,
    sensorType,
    sensorId,
    selectedLocation,
    globalUrl,
    localIp,
    gatewayPort,
    unifiedEndpoint,
    isDuckDnsActive,
    edges,
    nodes,
    associateSourceToElement,
    setSources,
  ]);

  const handleRemoveSensor = useCallback((sourceId: string) => {
    requestAuth(async () => {
      await sensorService.removeSource(sourceId);
      const fresh = await sensorService.getSources().catch(() => []);
      if (fresh) setSources(fresh);
    });
  }, [requestAuth, setSources]);

  const handlePickOnMap = useCallback(() => {
    const targetLabel = sensorName.trim() || sensorId || 'sensor local';
    startPickingElement({
      prompt: `Clique na via ou cruzamento no mapa para vincular ao sensor "${targetLabel}".`,
      onPicked: (elementId) => {
        setSelectedLocation(elementId);
        setSuccessMsg(`Via "${elementId}" selecionada no mapa com sucesso!`);
        setTimeout(() => setSuccessMsg(null), 3500);
      },
    });
  }, [startPickingElement, sensorName, sensorId]);

  useEffect(() => {
    return () => {
      if (useTopologyStore.getState().isPickingElement) {
        useTopologyStore.getState().cancelPickingElement();
      }
    };
  }, []);

  return {
    sensorType,
    setSensorType,
    sensorName,
    setSensorName,
    selectedLocation,
    setSelectedLocation,
    globalUrl,
    setGlobalUrl,
    localIp,
    gatewayPort,
    unifiedEndpoint,
    isDuckDnsActive,
    ingressUrl: unifiedEndpoint ? `${unifiedEndpoint}/${sensorId}` : `http://${localIp}:${gatewayPort}/${sensorId}`,
    sensorId,
    copiedField,
    successMsg,
    isBatchModalOpen,
    setIsBatchModalOpen,
    isPickingElement,
    edges,
    nodes,
    registeredSensors: filterRegisteredSensors(sources),
    handleCopy,
    handleRegisterSensor,
    handleRemoveSensor,
    handlePickOnMap,
  };
}
