// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useEffect } from 'react';
import { DataSourceItem } from '../../../types/sensors';
import { MapEdgeData, MapNodeData } from '../../../types/topology';
import { useSensorsStore, useTopologyStore, SensorsState, TopologyState } from '../../../stores';
import { sensorService, systemService } from '../../../services/api';

export interface UseEditSensorFormReturn {
  name: string;
  setName: (v: string) => void;
  isLocal: boolean;
  setIsLocal: (v: boolean) => void;
  sourceType: string;
  setSourceType: (v: string) => void;
  connectionString: string;
  setConnectionString: (v: string) => void;
  location: string;
  setLocation: (v: string) => void;
  isSaving: boolean;
  errorMsg: string | null;
  isDuckDnsActive: boolean;
  isPickingElement: boolean;
  edges: MapEdgeData[];
  nodes: MapNodeData[];
  handlePickOnMap: () => void;
  handleSave: (e: React.FormEvent) => Promise<void>;
}

/**
 * Controller / Application Hook (SOLID: Single Responsibility & Dependency Inversion)
 * Encapsulates form state lifecycle, domain validation rules (DuckDNS check),
 * topological element selection, and IPC transport persistence.
 */
export function useEditSensorForm(
  isOpen: boolean,
  sensor: DataSourceItem | null,
  onClose: () => void,
  onSaved?: () => void
): UseEditSensorFormReturn {
  const setSources = useSensorsStore((s: SensorsState) => s.setSources);
  const edges = useTopologyStore((s: TopologyState) => s.edges);
  const nodes = useTopologyStore((s: TopologyState) => s.nodes);
  const isPickingElement = useTopologyStore((s: TopologyState) => s.isPickingElement);
  const startPickingElement = useTopologyStore((s: TopologyState) => s.startPickingElement);

  const [name, setName] = useState('');
  const [isLocal, setIsLocal] = useState(true);
  const [sourceType, setSourceType] = useState('HTTP');
  const [connectionString, setConnectionString] = useState('');
  const [location, setLocation] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDuckDnsActive, setIsDuckDnsActive] = useState<boolean>(true);

  // Sync state whenever the opened sensor changes
  useEffect(() => {
    if (sensor) {
      setName(sensor.name || '');
      setIsLocal(sensor.is_local ?? true);
      setSourceType(sensor.source_type || (sensor.is_local ? 'HTTP' : 'REST API'));
      setConnectionString(
        sensor.connection_string || (sensor as any).endpoint_url || ''
      );
      setLocation(sensor.associated_element || '');
      setErrorMsg(null);
    }
  }, [sensor]);

  // Query network info to check DuckDNS status
  useEffect(() => {
    if (isOpen) {
      systemService
        .getNetworkInfo()
        .then((res: any) => {
          if (typeof res?.duckdns_enabled === 'boolean') {
            setIsDuckDnsActive(res.duckdns_enabled);
          }
        })
        .catch(() => {});
    }
  }, [isOpen]);

  const handlePickOnMap = () => {
    if (!sensor) return;
    startPickingElement({
      prompt: `Clique na via ou cruzamento no mapa para vincular ao sensor "${
        name.trim() || sensor.id
      }".`,
      onPicked: (elementId: string) => {
        setLocation(elementId);
      },
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sensor) return;

    if (!name.trim()) {
      setErrorMsg('O nome do sensor não pode ficar em branco.');
      return;
    }

    if (isLocal && !isDuckDnsActive) {
      setErrorMsg(
        'DuckDNS Obrigatório: Configure e ative o DuckDNS em Configurações > Acesso Remoto antes de manter ou ativar sensores locais.'
      );
      return;
    }

    setIsSaving(true);
    setErrorMsg(null);

    const trimmedLoc = location.trim();
    let resolvedElementId = trimmedLoc;
    if (trimmedLoc) {
      const matchEdge = edges.find(
        (e) =>
          e.id === trimmedLoc ||
          (e.name && e.name.toLowerCase() === trimmedLoc.toLowerCase())
      );
      if (matchEdge) {
        resolvedElementId = matchEdge.id;
      } else {
        const matchNode = nodes.find(
          (n) =>
            n.id === trimmedLoc ||
            (n.name && n.name.toLowerCase() === trimmedLoc.toLowerCase())
        );
        if (matchNode) {
          resolvedElementId = matchNode.id;
        }
      }
    }

    try {
      await sensorService.updateSource({
        id: sensor.id,
        name: name.trim(),
        is_local: isLocal,
        source_type: sourceType,
        connection: connectionString.trim(),
        location: resolvedElementId,
      });

      // Synchronize refreshed sources from backend to store
      const fresh = await sensorService.getSources().catch(() => []);
      if (fresh && fresh.length > 0) {
        setSources(fresh);
      }

      if (onSaved) onSaved();
      onClose();
    } catch (err: any) {
      const msg = err?.message || err?.error || 'Erro ao atualizar dados do sensor.';
      setErrorMsg(msg);
    } finally {
      setIsSaving(false);
    }
  };

  return {
    name,
    setName,
    isLocal,
    setIsLocal,
    sourceType,
    setSourceType,
    connectionString,
    setConnectionString,
    location,
    setLocation,
    isSaving,
    errorMsg,
    isDuckDnsActive,
    isPickingElement,
    edges,
    nodes,
    handlePickOnMap,
    handleSave,
  };
}
