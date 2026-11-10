// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { DataSourceItem } from '../types/sensors';
import { MapEdgeData, MapNodeData } from '../types/topology';

export function getNextLocalId(currentSources: DataSourceItem[]): string {
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
}

export function resolveElementLocation(
  trimmedLocation: string,
  edges: MapEdgeData[],
  nodes: MapNodeData[]
): { resolvedLocation: string; displayLocationName: string } {
  if (!trimmedLocation) {
    return { resolvedLocation: '', displayLocationName: '' };
  }

  const matchEdge = edges.find(
    (e) =>
      e.id === trimmedLocation ||
      (e.name && e.name.toLowerCase() === trimmedLocation.toLowerCase())
  );
  if (matchEdge) {
    return {
      resolvedLocation: matchEdge.id,
      displayLocationName: matchEdge.name || matchEdge.id,
    };
  }

  const matchNode = nodes.find(
    (n) =>
      n.id === trimmedLocation ||
      (n.name && n.name.toLowerCase() === trimmedLocation.toLowerCase())
  );
  if (matchNode) {
    return {
      resolvedLocation: matchNode.id,
      displayLocationName: matchNode.name || matchNode.id,
    };
  }

  return { resolvedLocation: trimmedLocation, displayLocationName: trimmedLocation };
}

export function filterRegisteredSensors(sources: DataSourceItem[]): DataSourceItem[] {
  return sources.filter(
    (s) =>
      s.source_type !== 'Parquet' &&
      s.id !== 'historical_base' &&
      !s.connection_string?.toLowerCase().endsWith('.parquet') &&
      s.id !== 'map_main' &&
      s.source_type !== 'SUMO Network'
  );
}
