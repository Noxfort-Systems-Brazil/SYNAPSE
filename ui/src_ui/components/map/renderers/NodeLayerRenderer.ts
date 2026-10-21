// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { MapLayerRenderer, MapRenderContext } from './types';

export class NodeLayerRenderer implements MapLayerRenderer {
  public render(context: MapRenderContext): void {
    const { ctx, nodes, selectedNodeId, isElementAssociated, canvasColors, isDark, zoom } =
      context;

    nodes.forEach((node) => {
      const isSelected = selectedNodeId === node.id;
      const hasSensor = isElementAssociated(node.id);

      ctx.beginPath();

      if (isSelected) {
        const radius = 9.0 / zoom;
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        const color = hasSensor ? canvasColors.roadSelected : canvasColors.roadActive;
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = isDark ? 16 : 10;
        ctx.fill();

        ctx.lineWidth = 2.4 / zoom;
        ctx.strokeStyle = '#ffffff';
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.stroke();
      } else if (hasSensor) {
        const radius = 7.5 / zoom;
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = canvasColors.roadMonitored;
        ctx.shadowColor = canvasColors.roadMonitored;
        ctx.shadowBlur = 12;
        ctx.fill();

        ctx.lineWidth = 2.0 / zoom;
        ctx.strokeStyle = '#ffffff';
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.stroke();
      } else {
        // Standard Intersection - Bright white/silver dot with dark ring
        const radius = 5.5 / zoom;
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = isDark ? '#e2e8f0' : '#ffffff';
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.fill();

        // High-definition outline ring for crisp street visibility
        ctx.lineWidth = 2.0 / zoom;
        ctx.strokeStyle = isDark ? '#020617' : '#0f172a';
        ctx.stroke();
      }
    });
  }
}
