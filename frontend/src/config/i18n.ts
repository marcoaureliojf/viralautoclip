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
      'zh-CN': { translation: translationZH },
      pt: { translation: translationPT },
      'pt-BR': { translation: translationPT },
    },
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
      caches: ['cookie'],
      lookupQuerystring: 'lng',
      lookupCookie: 'i18next',
      lookupLocalStorage: 'i18nextLng',
      convertDetectedLanguage: (lng) => {
        if (lng.startsWith('pt')) return 'pt-BR';
        if (lng.startsWith('zh')) return 'zh-CN';
        return lng;
      }
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
