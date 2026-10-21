// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import ptBR from './locales/pt_BR.json';
import enUS from './locales/en_US.json';
import esES from './locales/es_ES.json';
import frFR from './locales/fr_FR.json';
import ruRU from './locales/ru_RU.json';
import zhCN from './locales/zh_CN.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      pt_BR: { translation: ptBR },
      pt: { translation: ptBR },
      en_US: { translation: enUS },
      en: { translation: enUS },
      es_ES: { translation: esES },
      es: { translation: esES },
      fr_FR: { translation: frFR },
      fr: { translation: frFR },
      ru_RU: { translation: ruRU },
      ru: { translation: ruRU },
      zh_CN: { translation: zhCN },
      zh: { translation: zhCN },
    },
    fallbackLng: 'pt_BR',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
