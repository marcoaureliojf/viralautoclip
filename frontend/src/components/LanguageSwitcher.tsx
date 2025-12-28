import React from 'react';
import { useTranslation } from 'react-i18next';
import { Select } from 'antd';

const { Option } = Select;

const LanguageSwitcher: React.FC = () => {
  const { t, i18n } = useTranslation();
  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };
  return (
    <Select
      defaultValue={i18n.language}
      style={{ width: 150 }}
      onChange={changeLanguage}
    >
      <Option value="en">{t('languages.en')}</Option>
      <Option value="zh">{t('languages.zh')}</Option>
      <Option value="pt">{t('languages.pt')}</Option>
    </Select>
  );
};

export default LanguageSwitcher;
