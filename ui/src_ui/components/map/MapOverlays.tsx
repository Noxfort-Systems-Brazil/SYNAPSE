// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { DataSourceItem, EngineDataPayload } from '../../types/sensors';
import { MapEdgeData, MapNodeData } from '../../types/topology';
import { sensorService } from '../../services/api';
import { useSensorsStore } from '../../stores';
import {
  MapAssociationBanner,
  MapFluidEdgeInspector,
  MapNodeInspector,
  MapHoverBadge,
  MapZoomControls,
  MapEmptyState,
} from './overlays';

interface MapOverlaysProps {
  mapLoaded: boolean;
  isAssociatingSourceId: string | null;
  associationNotice: string | null;
  hoveredInfo: string | null;
  isPickingElement?: boolean;
  pickingPrompt?: string | null;
  onCancelPicking?: () => void;
  selectedEdgeId?: string | null;
  selectedNodeId?: string | null;
  nodes?: MapNodeData[];
  edges?: MapEdgeData[];
  sources?: DataSourceItem[];
  latestEngineData?: EngineDataPayload | null;
  onCancelAssociation: () => void;
  onSelectEdge?: (id: string | null) => void;
  onSelectNode?: (id: string | null) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView?: () => void;
}

export const MapOverlays: React.FC<MapOverlaysProps> = ({
  mapLoaded,
  isAssociatingSourceId,
  associationNotice,
  hoveredInfo,
  isPickingElement,
  pickingPrompt,
  onCancelPicking,
  selectedEdgeId,
  selectedNodeId,
  nodes = [],
  edges = [],
  sources = [],
  latestEngineData,
  onCancelAssociation,
  onSelectEdge,
  onSelectNode,
  onZoomIn,
  onZoomOut,
  onResetView,
}) => {
  const disassociateSource = useSensorsStore((s) => s.disassociateSource);

  const selectedElementId = selectedEdgeId || selectedNodeId;
  const currentEdge = selectedEdgeId ? edges.find((e) => e.id === selectedEdgeId) : null;
  const currentNode = selectedNodeId ? nodes.find((n) => n.id === selectedNodeId) : null;
  const oppEdge = currentEdge
    ? edges.find(
        (o) =>
          o.id === (currentEdge.id.startsWith('-') ? currentEdge.id.slice(1) : `-${currentEdge.id}`) ||
          (o.from === currentEdge.to && o.to === currentEdge.from)
      )
    : null;

  const associatedSensor = selectedElementId
    ? sources.find(
        (s) =>
          s.is_local && (
            s.associated_element === selectedElementId ||
            s.associated_element === `-${selectedElementId}` ||
            s.associated_element === selectedElementId.replace(/^-/, '') ||
            (oppEdge ? (
              s.associated_element === oppEdge.id ||
              s.associated_element === `-${oppEdge.id}` ||
              s.associated_element === oppEdge.id.replace(/^-/, '')
            ) : false)
          )
      )
    : null;

  const liveEdge = selectedEdgeId
    ? latestEngineData?.edge_data?.[selectedEdgeId] ||
      latestEngineData?.edge_data?.[selectedEdgeId.replace(/^-/, '')] ||
      latestEngineData?.edge_data?.[`-${selectedEdgeId}`] ||
      (oppEdge
        ? latestEngineData?.edge_data?.[oppEdge.id] ||
          latestEngineData?.edge_data?.[oppEdge.id.replace(/^-/, '')] ||
          latestEngineData?.edge_data?.[`-${oppEdge.id}`]
        : null)
    : null;

  const handleDisassociate = async (sensorId: string) => {
    disassociateSource(sensorId);
    await sensorService.associateSource(sensorId, '');
  };

  return (
    <>
      {/* Association Crosshair Mode & Notifications */}
      <MapAssociationBanner
        isAssociatingSourceId={isAssociatingSourceId}
        associationNotice={associationNotice}
        onCancelAssociation={onCancelAssociation}
        isPickingElement={isPickingElement}
        pickingPrompt={pickingPrompt}
        onCancelPicking={onCancelPicking}
      />

      {/* Selected Edge: Comprehensive Fluid Dynamics Inspector */}
      {selectedEdgeId && !isPickingElement && (
        <MapFluidEdgeInspector
          edgeId={selectedEdgeId}
          currentEdge={currentEdge}
          liveEdgeData={liveEdge}
          associatedSensor={associatedSensor}
          onClose={() => onSelectEdge?.(null)}
          onDisassociate={handleDisassociate}
        />
      )}

      {/* Selected Node: Intersection Inspector */}
      {!selectedEdgeId && selectedNodeId && !isPickingElement && (
        <MapNodeInspector
          nodeId={selectedNodeId}
          nodeName={currentNode?.name}
          infoText={hoveredInfo}
          onClose={() => onSelectNode?.(null)}
        />
      )}

      {/* Hover Information Badge */}
      {!selectedEdgeId && !selectedNodeId && (
        <MapHoverBadge hoveredInfo={hoveredInfo} />
      )}

      {/* Canvas Zoom Controls */}
      <MapZoomControls onZoomIn={onZoomIn} onZoomOut={onZoomOut} onResetView={onResetView} />

      {/* Empty State Banner */}
      <MapEmptyState mapLoaded={mapLoaded} />
    </>
  );
};


