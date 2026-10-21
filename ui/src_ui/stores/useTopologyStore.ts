// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { create } from 'zustand';
import { MapNodeData, MapEdgeData } from '../types/topology';

export interface TopologyState {
  nodes: MapNodeData[];
  edges: MapEdgeData[];
  mapLoaded: boolean;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  isAssociatingSourceId: string | null;

  // Road / Element Picker Mode (e.g. for wizard sensor location selection)
  isPickingElement: boolean;
  pickingPrompt: string | null;
  onElementPicked: ((elementId: string, type: 'node' | 'edge') => void) | null;

  // Actions
  setTopology: (nodes: MapNodeData[], edges: MapEdgeData[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  setSelectedEdgeId: (id: string | null) => void;
  setAssociatingSourceId: (id: string | null) => void;
  startPickingElement: (options?: {
    prompt?: string;
    onPicked?: (elementId: string, type: 'node' | 'edge') => void;
  }) => void;
  cancelPickingElement: () => void;
  confirmElementPicked: (elementId: string, type: 'node' | 'edge') => void;
  clearTopology: () => void;
}

export const useTopologyStore = create<TopologyState>((set, get) => ({
  nodes: [],
  edges: [],
  mapLoaded: false,
  selectedNodeId: null,
  selectedEdgeId: null,
  isAssociatingSourceId: null,

  isPickingElement: false,
  pickingPrompt: null,
  onElementPicked: null,

  setTopology: (nodes, edges) => set({ nodes, edges, mapLoaded: nodes.length > 0 }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id, selectedEdgeId: null }),
  setSelectedEdgeId: (id) => set({ selectedEdgeId: id, selectedNodeId: null }),
  setAssociatingSourceId: (id) => set({ isAssociatingSourceId: id }),

  startPickingElement: (options) =>
    set({
      isPickingElement: true,
      pickingPrompt: options?.prompt || null,
      onElementPicked: options?.onPicked || null,
    }),

  cancelPickingElement: () =>
    set({
      isPickingElement: false,
      pickingPrompt: null,
      onElementPicked: null,
    }),

  confirmElementPicked: (elementId, type) => {
    const cb = get().onElementPicked;
    if (cb) {
      cb(elementId, type);
    }
    set({
      isPickingElement: false,
      pickingPrompt: null,
      onElementPicked: null,
    });
  },

  clearTopology: () =>
    set({
      nodes: [],
      edges: [],
      mapLoaded: false,
      selectedNodeId: null,
      selectedEdgeId: null,
      isAssociatingSourceId: null,
      isPickingElement: false,
      pickingPrompt: null,
      onElementPicked: null,
    }),
}));
