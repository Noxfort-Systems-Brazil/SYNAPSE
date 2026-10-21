// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useEffect, useMemo, RefObject } from 'react';
import { MapNodeData, MapEdgeData, Point2D } from '../../../types/topology';
import { EngineDataPayload, DataSourceItem } from '../../../types/sensors';
import { useSystemStore } from '../../../stores';
import { getThemeTokens } from '../../../theme';
import {
  ViewportManager,
  RoadLayerRenderer,
  OverlayLayerRenderer,
  NodeLayerRenderer,
  MapRenderContext,
  MapLayerRenderer,
} from '../renderers';

interface MapRendererProps {
  canvasRef: RefObject<HTMLCanvasElement | null>;
  nodes: MapNodeData[];
  edges: MapEdgeData[];
  sources?: DataSourceItem[];
  pan: Point2D;
  zoom: number;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  latestEngineData: EngineDataPayload | null;
  theme?: 'dark' | 'light';
}

export function useMapRenderer({
  canvasRef,
  nodes,
  edges,
  sources = [],
  pan,
  zoom,
  selectedNodeId,
  selectedEdgeId,
  latestEngineData,
  theme: customTheme,
}: MapRendererProps) {
  const systemTheme = useSystemStore((s) => s.theme);
  const theme = customTheme || systemTheme || 'dark';
  const isDark = theme === 'dark';

  // Instantiate decoupled layer renderers
  const pipeline: MapLayerRenderer[] = useMemo(
    () => [new RoadLayerRenderer(), new OverlayLayerRenderer(), new NodeLayerRenderer()],
    []
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const themeTokens = getThemeTokens(theme);
    const { canvas: canvasColors } = themeTokens.colors;

    const viewport = ViewportManager.prepareCanvas(canvas, canvasColors.background);
    if (!viewport) return;
    const { ctx, width, height } = viewport;

    // Fast lookups
    const nodeMap = new Map<string, MapNodeData>();
    nodes.forEach((n) => nodeMap.set(n.id, n));

    const edgeMap = new Map<string, MapEdgeData>();
    edges.forEach((e) => edgeMap.set(e.id, e));

    const opposingEdgeMap = new Map<string, MapEdgeData>();
    edges.forEach((e) => {
      const oppId1 = e.id.startsWith('-') ? e.id.slice(1) : `-${e.id}`;
      if (edgeMap.has(oppId1)) {
        opposingEdgeMap.set(e.id, edgeMap.get(oppId1)!);
        return;
      }
      const oppByEndpoints = edges.find(
        (other) => other.id !== e.id && other.from === e.to && other.to === e.from
      );
      if (oppByEndpoints) {
        opposingEdgeMap.set(e.id, oppByEndpoints);
      }
    });

    const isElementAssociated = (elementId: string) => {
      const opp = opposingEdgeMap.get(elementId);
      return sources.some(
        (s) =>
          s.is_local && (
            s.associated_element === elementId ||
            s.associated_element === `-${elementId}` ||
            s.associated_element === elementId.replace(/^-/, '') ||
            (opp !== undefined && (
              s.associated_element === opp.id ||
              s.associated_element === `-${opp.id}` ||
              s.associated_element === opp.id.replace(/^-/, '')
            ))
          )
      );
    };

    const renderContext: MapRenderContext = {
      ctx,
      width,
      height,
      pan,
      zoom,
      isDark,
      canvasColors,
      nodes,
      edges,
      nodeMap,
      edgeMap,
      opposingEdgeMap,
      sources,
      selectedNodeId,
      selectedEdgeId,
      latestEngineData,
      isElementAssociated,
    };

    // Execute render pipeline
    ViewportManager.applyTransform(ctx, pan, zoom);
    pipeline.forEach((layer) => layer.render(renderContext));
    ViewportManager.restoreTransform(ctx);
  }, [
    nodes,
    edges,
    sources,
    pan,
    zoom,
    latestEngineData,
    selectedNodeId,
    selectedEdgeId,
    canvasRef,
    isDark,
    theme,
    pipeline,
  ]);
}


