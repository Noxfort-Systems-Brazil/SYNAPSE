// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export interface PasswordCriteria {
  minLength: boolean;
  hasUpper: boolean;
  hasLower: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
  noWhitespace: boolean;
}

export type PasswordStrength = 'weak' | 'medium' | 'strong' | 'veryStrong';

export interface PasswordValidationResult {
  criteria: PasswordCriteria;
  isValid: boolean;
  strengthScore: number; // 0 to 4
  strength: PasswordStrength;
}

export const SPECIAL_CHAR_REGEX = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?~`]/;

export function validatePassword(password: string): PasswordValidationResult {
  const minLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = SPECIAL_CHAR_REGEX.test(password);
  const noWhitespace = password.length === 0 || (!password.startsWith(' ') && !password.endsWith(' '));

  const criteria: PasswordCriteria = {
    minLength,
    hasUpper,
    hasLower,
    hasNumber,
    hasSpecial,
    noWhitespace,
  };

  const allCriteriaMet =
    minLength && hasUpper && hasLower && hasNumber && hasSpecial && noWhitespace;

  let strengthScore = 0;
  if (password.length > 0) {
    if (minLength) strengthScore++;
    if (hasUpper && hasLower) strengthScore++;
    if (hasNumber) strengthScore++;
    if (hasSpecial) strengthScore++;
    if (password.length >= 12 && allCriteriaMet) strengthScore = 4;
  }

  let strength: PasswordStrength = 'weak';
  if (strengthScore <= 1) {
    strength = 'weak';
  } else if (strengthScore === 2) {
    strength = 'medium';
  } else if (strengthScore === 3) {
    strength = 'strong';
  } else {
    strength = 'veryStrong';
  }

  return {
    criteria,
    isValid: allCriteriaMet,
    strengthScore,
    strength,
  };
}

export interface PasswordRequirement {
  id: string;
  labelKey: string;
  fallbackLabel: string;
  isMet: boolean;
}

export function getPasswordRequirements(
  validation: PasswordValidationResult,
  passwordsMatch: boolean
): PasswordRequirement[] {
  return [
    {
      id: 'min_length',
      labelKey: 'security.reqMinLength',
      fallbackLabel: 'Mínimo de 8 caracteres',
      isMet: validation.criteria.minLength,
    },
    {
      id: 'has_upper',
      labelKey: 'security.reqUppercase',
      fallbackLabel: 'Letra maiúscula (A-Z)',
      isMet: validation.criteria.hasUpper,
    },
    {
      id: 'has_lower',
      labelKey: 'security.reqLowercase',
      fallbackLabel: 'Letra minúscula (a-z)',
      isMet: validation.criteria.hasLower,
    },
    {
      id: 'has_number',
      labelKey: 'security.reqNumber',
      fallbackLabel: 'Número (0-9)',
      isMet: validation.criteria.hasNumber,
    },
    {
      id: 'has_special',
      labelKey: 'security.reqSpecial',
      fallbackLabel: 'Caractere especial (!@#$...)',
      isMet: validation.criteria.hasSpecial,
    },
    {
      id: 'passwords_match',
      labelKey: 'security.reqMatch',
      fallbackLabel: 'Senhas coincidem',
      isMet: passwordsMatch,
    },
  ];
}

