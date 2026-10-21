// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { Point2D } from '../../../types/topology';

export class ViewportManager {
  /**
   * Configures canvas for high-DPI displays and clears the background.
   */
  public static prepareCanvas(
    canvas: HTMLCanvasElement,
    backgroundColor: string
  ): { ctx: CanvasRenderingContext2D; width: number; height: number } | null {
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, rect.width, rect.height);

    return { ctx, width: rect.width, height: rect.height };
  }

  /**
   * Applies the SUMO Cartesian coordinate transformation (with inverted Y-axis).
   */
  public static applyTransform(ctx: CanvasRenderingContext2D, pan: Point2D, zoom: number): void {
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, -zoom);
  }

  /**
   * Restores the canvas coordinate state.
   */
  public static restoreTransform(ctx: CanvasRenderingContext2D): void {
    ctx.restore();
  }
}
