import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      "Welcome": "Welcome to Smart Contract Analyzer"
    }
  },
  zh: {
    translation: {
      "Welcome": "欢迎使用智能合约安全审计平台"
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "zh",
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
