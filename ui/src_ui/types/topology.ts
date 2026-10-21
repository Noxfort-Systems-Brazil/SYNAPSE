// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export interface Point2D {
  x: number;
  y: number;
}

export interface BoundingBox {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}

export interface MapNodeData {
  id: string;
  x: number;
  y: number;
  name?: string | null;
  is_tls?: boolean;
}

export interface MapEdgeData {
  id: string;
  from: string;
  to: string;
  name?: string | null;
  length?: number;
  shape?: number[][];
}

export interface TopologyPayload {
  nodes: MapNodeData[];
  edges: MapEdgeData[];
  loaded: boolean;
}
