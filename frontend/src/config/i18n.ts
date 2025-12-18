import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import translationEN from '../locales/en/translation.json';
import translationZH from '../locales/zh/translation.json';
import translationPT from '../locales/pt/translation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: translationEN },
      zh: { translation: translationZH },
      pt: { translation: translationPT },
    },
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
      caches: ['cookie'],
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
