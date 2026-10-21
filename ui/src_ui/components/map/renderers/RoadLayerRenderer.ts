// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { MapLayerRenderer, MapRenderContext } from './types';
import { computeCenterline } from '../../../utils/geometry';

export class RoadLayerRenderer implements MapLayerRenderer {
  public render(context: MapRenderContext): void {
    const { ctx, edges, opposingEdgeMap, nodeMap, canvasColors, zoom } = context;
    const renderedRoadKeys = new Set<string>();

    edges.forEach((edge) => {
      const opp = opposingEdgeMap.get(edge.id);
      const roadKey = opp ? [edge.id, opp.id].sort().join('::') : edge.id;

      if (renderedRoadKeys.has(roadKey)) {
        return;
      }
      renderedRoadKeys.add(roadKey);

      const fromNode = nodeMap.get(edge.from);
      const toNode = nodeMap.get(edge.to);

      let centerline: number[][] = [];
      if (opp && opp.shape && edge.shape && edge.shape.length > 0 && opp.shape.length > 0) {
        centerline = computeCenterline(edge.shape, opp.shape);
      } else if (edge.shape && edge.shape.length > 0) {
        centerline = edge.shape;
      } else if (fromNode && toNode) {
        centerline = [[fromNode.x, fromNode.y], [toNode.x, toNode.y]];
      }

      if (centerline.length === 0) return;

      const connectFrom =
        fromNode &&
        Math.hypot(fromNode.x - centerline[0][0], fromNode.y - centerline[0][1]) < 30.0;
      const lastIdx = centerline.length - 1;
      const connectTo =
        toNode &&
        Math.hypot(toNode.x - centerline[lastIdx][0], toNode.y - centerline[lastIdx][1]) < 30.0;

      ctx.beginPath();
      if (connectFrom && fromNode) {
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(centerline[0][0], centerline[0][1]);
      } else {
        ctx.moveTo(centerline[0][0], centerline[0][1]);
      }

      for (let i = 1; i < centerline.length; i++) {
        ctx.lineTo(centerline[i][0], centerline[i][1]);
      }

      if (connectTo && toNode) {
        ctx.lineTo(toNode.x, toNode.y);
      }

      ctx.strokeStyle = canvasColors.roadDefault;
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
      ctx.lineWidth = 6.5 / zoom;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.stroke();
    });
  }
}
