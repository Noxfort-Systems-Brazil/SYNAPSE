// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useRef, useState } from 'react';
import { useTopologyStore, useSensorsStore } from '../../stores';
import { sensorService } from '../../services/api';
import { useMapRenderer } from './hooks/useMapRenderer';
import { useMapInteraction } from './hooks/useMapInteraction';
import { MapOverlays } from './MapOverlays';

export const SumoMapCanvas: React.FC = () => {
  const {
    nodes,
    edges,
    mapLoaded,
    selectedNodeId,
    selectedEdgeId,
    isAssociatingSourceId,
    isPickingElement,
    pickingPrompt,
    cancelPickingElement,
    confirmElementPicked,
    setSelectedNodeId,
    setSelectedEdgeId,
    setAssociatingSourceId,
  } = useTopologyStore();

  const { sources, latestEngineData, associateSourceToElement } = useSensorsStore();

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [associationNotice, setAssociationNotice] = useState<string | null>(null);

  const handleElementClicked = async (elementId: string, type: 'node' | 'edge') => {
    let displayName = elementId;
    if (type === 'edge') {
      const edge = edges.find((e) => e.id === elementId);
      displayName = edge?.name || elementId;
    } else {
      const node = nodes.find((n) => n.id === elementId);
      displayName = node?.name || elementId;
    }

    // 1. Element Picker Mode (from Ingestion Wizard or modal)
    if (isPickingElement) {
      const label = type === 'node' ? `cruzamento '${displayName}'` : `via '${displayName}'`;
      setAssociationNotice(`✓ ${label} selecionada! Retornando ao assistente...`);
      confirmElementPicked(elementId, type);
      if (type === 'edge') {
        setSelectedEdgeId(elementId);
      } else {
        setSelectedNodeId(elementId);
      }
      setTimeout(() => setAssociationNotice(null), 3500);
      return;
    }

    // 2. Direct Source Association Mode
    if (isAssociatingSourceId) {
      associateSourceToElement(isAssociatingSourceId, elementId);
      await sensorService.associateSource(isAssociatingSourceId, elementId);
      const label = type === 'node' ? `cruzamento '${displayName}'` : `via '${displayName}'`;
      setAssociationNotice(`Sensor '${isAssociatingSourceId}' vinculado com sucesso a ${label}`);
      setAssociatingSourceId(null);
      if (type === 'edge') {
        setSelectedEdgeId(elementId);
      } else {
        setSelectedNodeId(elementId);
      }
      setTimeout(() => setAssociationNotice(null), 4000);
    }
  };

  const {
    zoom,
    setZoom,
    pan,
    hoveredInfo,
    resetView,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleWheel,
    handleClick,
    handleAuxClick,
  } = useMapInteraction({
    canvasRef,
    nodes,
    edges,
    sources,
    latestEngineData,
    onSelectNode: setSelectedNodeId,
    onSelectEdge: setSelectedEdgeId,
    onElementClicked: handleElementClicked,
  });

  useMapRenderer({
    canvasRef,
    nodes,
    edges,
    sources,
    pan,
    zoom,
    selectedNodeId,
    selectedEdgeId,
    latestEngineData,
  });

  return (
    <div
      className={`relative w-full h-[calc(100vh-4rem-2rem)] overflow-hidden bg-background select-none flex items-center justify-center ${
        isAssociatingSourceId || isPickingElement ? 'cursor-crosshair' : 'cursor-default'
      }`}
    >
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={handleClick}
        onAuxClick={handleAuxClick}
        onContextMenu={(e) => e.preventDefault()}
        onWheel={handleWheel}
        className="w-full h-full"
      />

      <MapOverlays
        mapLoaded={mapLoaded}
        isAssociatingSourceId={isAssociatingSourceId}
        isPickingElement={isPickingElement}
        pickingPrompt={pickingPrompt}
        onCancelPicking={cancelPickingElement}
        associationNotice={associationNotice}
        hoveredInfo={hoveredInfo}
        selectedEdgeId={selectedEdgeId}
        selectedNodeId={selectedNodeId}
        nodes={nodes}
        edges={edges}
        sources={sources}
        latestEngineData={latestEngineData}
        onCancelAssociation={() => setAssociatingSourceId(null)}
        onSelectEdge={setSelectedEdgeId}
        onSelectNode={setSelectedNodeId}
        onZoomIn={() => setZoom((z) => Math.min(z * 1.25, 80))}
        onZoomOut={() => setZoom((z) => Math.max(z * 0.8, 0.05))}
        onResetView={resetView}
      />
    </div>
  );
};

