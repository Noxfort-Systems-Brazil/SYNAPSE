// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { TFunction } from 'i18next';

/**
 * Translates backend canonical semantic types ("Vehicle Count", "Traffic Flow", etc.)
 * into the localized presentation string.
 */
export function formatSemanticType(semanticType: string | null | undefined, t: TFunction): string {
  if (!semanticType) {
    return t('sensors.semantics.scanning');
  }

  const normalized = semanticType.toLowerCase().trim();

  if (normalized.includes('count') || normalized.includes('contagem')) {
    return t('sensors.semantics.vehicleCount');
  }
  if (normalized.includes('speed') || normalized.includes('velocidade')) {
    return t('sensors.semantics.vehicleSpeed');
  }
  if (normalized.includes('flow') || normalized.includes('fluxo')) {
    return t('sensors.semantics.trafficFlow');
  }
  if (normalized.includes('density') || normalized.includes('densidade') || normalized.includes('occ')) {
    return t('sensors.semantics.trafficDensity');
  }
  if (normalized.includes('state') || normalized.includes('estado')) {
    return t('sensors.semantics.trafficState');
  }
  if (normalized.includes('scanning') || normalized.includes('analis') || normalized.includes('identif')) {
    return t('sensors.semantics.scanning');
  }

  return semanticType;
}

/**
 * Returns the localized text for a sensor status.
 */
export function formatSensorStatus(status: string | null | undefined, t: TFunction): string {
  if (!status) return t('sensors.status.offline');

  const lower = status.toLowerCase();
  switch (lower) {
    case 'active':
      return t('sensors.status.active');
    case 'quarantine':
      return t('sensors.status.quarantine');
    case 'validating':
      return t('sensors.status.validating');
    case 'rejected':
      return t('sensors.status.rejected');
    case 'offline':
    case 'fallback':
    default:
      return t('sensors.status.offline');
  }
}

/**
 * Returns the localized text for a user role.
 */
export function formatUserRole(role: string | null | undefined, t: TFunction): string {
  if (!role) return '';
  switch (role.toUpperCase()) {
    case 'OPERATOR':
      return t('roles.OPERATOR');
    case 'SUPERUSER':
      return t('roles.SUPERUSER');
    case 'MASTER':
      return t('roles.MASTER');
    default:
      return role;
  }
}
