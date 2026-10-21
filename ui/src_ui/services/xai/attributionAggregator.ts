// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

/**
 * XAI Attribution Aggregator (Clean Architecture & SOLID: SRP).
 *
 * Encapsulates analytical domain calculations for Explainable AI (Captum Integrated Gradients):
 * - Normalizes sensor attribution weights and feature names
 * - Collapses temporal lags [t-X] into canonical sensor identities
 * - Aggregates minor contributions into a consolidated remainder category
 */

export interface AggregatedFeatureItem {
  name: string;
  weight: number;
  percentage: number;
}

export function aggregateTopSensorAttributions(
  attributions: number[],
  featureNames?: string[],
  topN: number = 6,
  otherLabel: string = 'Demais Sensores (Agregados)'
): AggregatedFeatureItem[] {
  if (!attributions || attributions.length === 0) {
    return [];
  }

  // If no featureNames or length mismatch, format pure indices
  if (!featureNames || featureNames.length !== attributions.length) {
    const total = attributions.reduce((acc, v) => acc + Math.abs(v), 0) || 1;
    return attributions.slice(0, topN).map((v, i) => ({
      name: `Janela t-${attributions.length - 1 - i}`,
      weight: Math.abs(v),
      percentage: Math.round((Math.abs(v) / total) * 1000) / 10,
    }));
  }

  // Group by base sensor name (removing [t-X] or (t-X) suffixes)
  const sensorMap = new Map<string, number>();

  for (let i = 0; i < attributions.length; i++) {
    const rawName = featureNames[i] || `Sensor_${i}`;
    const weight = Math.abs(attributions[i]);

    let baseName = rawName.replace(/\s*\[t-\d+\]$/i, '').replace(/\s*\(t-\d+\)$/i, '').trim();
    baseName = baseName.replace(/^\[SENSOR\]\s*/i, 'Sensor ');

    const current = sensorMap.get(baseName) || 0;
    sensorMap.set(baseName, current + weight);
  }

  // If all features collapsed into just 1 sensor or it's a temporal-only breakdown of 1 sensor:
  if (sensorMap.size === 1 && attributions.length > 1) {
    const total = attributions.reduce((acc, v) => acc + Math.abs(v), 0) || 1;
    const sortedIndices = attributions
      .map((v, i) => ({ index: i, weight: Math.abs(v), rawName: featureNames[i] }))
      .sort((a, b) => b.weight - a.weight);

    const topIndices = sortedIndices.slice(0, topN);
    const otherWeight = sortedIndices.slice(topN).reduce((acc, cur) => acc + cur.weight, 0);

    const result: AggregatedFeatureItem[] = topIndices.map((item) => ({
      name: item.rawName.replace(/^\[SENSOR\]\s*/i, 'Sensor '),
      weight: Math.round(item.weight * 100) / 100,
      percentage: Math.round((item.weight / total) * 1000) / 10,
    }));

    if (otherWeight > 0) {
      result.push({
        name: otherLabel,
        weight: Math.round(otherWeight * 100) / 100,
        percentage: Math.round((otherWeight / total) * 1000) / 10,
      });
    }
    return result;
  }

  const sortedSensors = Array.from(sensorMap.entries())
    .map(([name, weight]) => ({ name, weight }))
    .sort((a, b) => b.weight - a.weight);

  const totalSum = sortedSensors.reduce((acc, s) => acc + s.weight, 0) || 1;

  const topSensors = sortedSensors.slice(0, topN);
  const remainingSensors = sortedSensors.slice(topN);
  const remainingWeight = remainingSensors.reduce((acc, s) => acc + s.weight, 0);

  const result: AggregatedFeatureItem[] = topSensors.map((s) => ({
    name: s.name,
    weight: Math.round(s.weight * 100) / 100,
    percentage: Math.round((s.weight / totalSum) * 1000) / 10,
  }));

  if (remainingSensors.length > 0 && remainingWeight > 0) {
    result.push({
      name: `${otherLabel} (${remainingSensors.length} vias)`,
      weight: Math.round(remainingWeight * 100) / 100,
      percentage: Math.round((remainingWeight / totalSum) * 1000) / 10,
    });
  }

  return result;
}
