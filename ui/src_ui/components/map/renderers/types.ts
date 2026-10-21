// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { MapNodeData, MapEdgeData, Point2D } from '../../../types/topology';
import { EngineDataPayload, DataSourceItem } from '../../../types/sensors';
import { DesignTokens } from '../../../theme';

export type CanvasColors = DesignTokens['themes']['dark']['colors']['canvas'];

export interface MapRenderContext {
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  pan: Point2D;
  zoom: number;
  isDark: boolean;
  canvasColors: CanvasColors;
  nodes: MapNodeData[];
  edges: MapEdgeData[];
  nodeMap: Map<string, MapNodeData>;
  edgeMap: Map<string, MapEdgeData>;
  opposingEdgeMap: Map<string, MapEdgeData>;
  sources: DataSourceItem[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  latestEngineData: EngineDataPayload | null;
  isElementAssociated: (elementId: string) => boolean;
}

export interface MapLayerRenderer {
  render(context: MapRenderContext): void;
}
