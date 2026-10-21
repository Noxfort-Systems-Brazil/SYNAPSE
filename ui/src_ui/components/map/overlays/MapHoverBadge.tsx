// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { MapPin } from 'lucide-react';

interface MapHoverBadgeProps {
  hoveredInfo: string | null;
}

export const MapHoverBadge: React.FC<MapHoverBadgeProps> = ({ hoveredInfo }) => {
  if (!hoveredInfo) return null;

  return (
    <div className="absolute bottom-4 left-6 z-20 glass-panel px-4 py-2 rounded-xl text-xs font-mono text-slate-800 dark:text-slate-200 border border-border flex items-center gap-2 shadow-xl animate-in fade-in select-none">
      <MapPin className="w-3.5 h-3.5 text-accent-amber" />
      <span>{hoveredInfo}</span>
    </div>
  );
};
