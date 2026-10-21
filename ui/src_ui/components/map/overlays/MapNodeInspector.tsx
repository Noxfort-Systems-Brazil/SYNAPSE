// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { MapPin, X } from 'lucide-react';

interface MapNodeInspectorProps {
  nodeId: string;
  nodeName?: string | null;
  infoText?: string | null;
  onClose: () => void;
}

export const MapNodeInspector: React.FC<MapNodeInspectorProps> = ({
  nodeId,
  nodeName,
  infoText,
  onClose,
}) => {
  return (
    <div className="absolute bottom-4 left-6 z-20 glass-panel p-3.5 rounded-xl border border-primary-500/40 bg-surface/95 shadow-2xl space-y-2 min-w-[280px] animate-in fade-in select-none">
      <div className="flex items-center justify-between gap-2 border-b border-border/80 pb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-2.5 h-2.5 rounded-full bg-primary-500 flex-shrink-0" />
          <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1 truncate" title={nodeName || undefined}>
            <MapPin className="w-3.5 h-3.5 text-primary-400 flex-shrink-0" />
            <span className="truncate">{nodeName || 'Cruzamento / Nó'}</span>
          </span>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary-500/10 text-primary-400 border border-primary-500/30 font-bold" title={`ID: ${nodeId}`}>
            {nodeName ? `ID: ${nodeId}` : nodeId}
          </span>
          <button
            onClick={onClose}
            className="p-0.5 text-slate-400 hover:text-slate-200 rounded hover:bg-surfaceHover transition-colors cursor-pointer"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </div>
      {infoText && (
        <p className="text-xs font-mono text-slate-700 dark:text-slate-300">{infoText}</p>
      )}
    </div>
  );
};
