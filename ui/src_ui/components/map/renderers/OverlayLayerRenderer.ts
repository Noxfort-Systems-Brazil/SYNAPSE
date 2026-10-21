// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { MapLayerRenderer, MapRenderContext } from './types';
import { computeCenterline } from '../../../utils/geometry';

export class OverlayLayerRenderer implements MapLayerRenderer {
  public render(context: MapRenderContext): void {
    const {
      ctx,
      edges,
      opposingEdgeMap,
      nodeMap,
      selectedEdgeId,
      isElementAssociated,
      canvasColors,
      isDark,
      zoom,
    } = context;

    const renderedRoadKeys = new Set<string>();

    edges.forEach((edge) => {
      const opp = opposingEdgeMap.get(edge.id);
      const roadKey = opp ? [edge.id, opp.id].sort().join('::') : edge.id;

      if (renderedRoadKeys.has(roadKey)) {
        return;
      }
      renderedRoadKeys.add(roadKey);

      const isSelected =
        selectedEdgeId === edge.id ||
        selectedEdgeId === `-${edge.id}` ||
        `-${selectedEdgeId}` === edge.id ||
        (opp !== undefined && (
          selectedEdgeId === opp.id ||
          selectedEdgeId === `-${opp.id}` ||
          `-${selectedEdgeId}` === opp.id
        ));

      const hasSensor =
        isElementAssociated(edge.id) ||
        (opp !== undefined && isElementAssociated(opp.id));

      if (!isSelected && !hasSensor) return;

      const fromNode = nodeMap.get(edge.from);
      const toNode = nodeMap.get(edge.to);

      let polyline: number[][] = [];
      if (opp && opp.shape && edge.shape && edge.shape.length > 0 && opp.shape.length > 0) {
        polyline = computeCenterline(edge.shape, opp.shape);
      } else if (edge.shape && edge.shape.length > 0) {
        polyline = edge.shape;
      } else if (fromNode && toNode) {
        polyline = [[fromNode.x, fromNode.y], [toNode.x, toNode.y]];
      }

      if (polyline.length === 0) return;

      // 1. Draw Street Path Line
      if (isSelected) {
        const color = hasSensor
          ? (isDark ? '#00f2fe' : '#0284c7')
          : canvasColors.roadActive;
        ctx.strokeStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = isDark ? 20 : 12;
        ctx.lineWidth = 10.0 / zoom;
      } else if (hasSensor) {
        // Distinctive Local Sensor Monitored Road (Neon Cyan / High Contrast)
        const sensorColor = isDark ? '#00f2fe' : '#0284c7';
        ctx.strokeStyle = sensorColor;
        ctx.shadowColor = sensorColor;
        ctx.shadowBlur = isDark ? 14 : 8;
        ctx.lineWidth = 9.2 / zoom;
      }

      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      const connectFrom =
        fromNode &&
        Math.hypot(fromNode.x - polyline[0][0], fromNode.y - polyline[0][1]) < 30.0;
      const lastIdx = polyline.length - 1;
      const connectTo =
        toNode &&
        Math.hypot(toNode.x - polyline[lastIdx][0], toNode.y - polyline[lastIdx][1]) < 30.0;

      if (connectFrom && fromNode) {
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(polyline[0][0], polyline[0][1]);
      } else {
        ctx.moveTo(polyline[0][0], polyline[0][1]);
      }

      for (let i = 1; i < polyline.length; i++) {
        ctx.lineTo(polyline[i][0], polyline[i][1]);
      }

      if (connectTo && toNode) {
        ctx.lineTo(toNode.x, toNode.y);
      }
      ctx.stroke();

      // 2. Local Sensor Beacon / Marker on the Street
      if (hasSensor && polyline.length >= 2) {
        const midIdx = Math.floor(polyline.length / 2);
        const midPoint = polyline[midIdx];
        const beaconRadius = 5.2 / zoom;

        ctx.save();
        // Outer halo
        ctx.beginPath();
        ctx.arc(midPoint[0], midPoint[1], beaconRadius + (3.2 / zoom), 0, Math.PI * 2);
        ctx.fillStyle = isDark ? 'rgba(0, 242, 254, 0.28)' : 'rgba(2, 132, 199, 0.22)';
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.fill();

        // Core cyan dot
        ctx.beginPath();
        ctx.arc(midPoint[0], midPoint[1], beaconRadius, 0, Math.PI * 2);
        const coreColor = isDark ? '#00f2fe' : '#0284c7';
        ctx.fillStyle = coreColor;
        ctx.shadowColor = coreColor;
        ctx.shadowBlur = isDark ? 10 : 6;
        ctx.fill();

        // White inner beacon center
        ctx.beginPath();
        ctx.arc(midPoint[0], midPoint[1], beaconRadius * 0.45, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.fill();

        ctx.restore();
      }
    });
  }
}
