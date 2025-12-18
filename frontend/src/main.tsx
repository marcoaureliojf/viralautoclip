import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import enUS from 'antd/locale/en_US'
import ptBR from 'antd/locale/pt_BR'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import 'dayjs/locale/pt-br'
import 'dayjs/locale/en'
import relativeTime from 'dayjs/plugin/relativeTime'
import timezone from 'dayjs/plugin/timezone'
import utc from 'dayjs/plugin/utc'
import App from './App.tsx'
import './index.css'
import { useTranslation } from 'react-i18next'
import './config/i18n'

// 配置dayjs插件
dayjs.extend(relativeTime)
dayjs.extend(timezone)
dayjs.extend(utc)

// 设置时区
dayjs.tz.setDefault('Asia/Shanghai')

const RootWrapper = () => {
  const { i18n } = useTranslation()
  
  const getAntdLocale = () => {
    switch (i18n.language) {
      case 'zh': return zhCN
      case 'pt': return ptBR
      default: return enUS
    }
  }

  const getDayjsLocale = () => {
    switch (i18n.language) {
      case 'zh': return 'zh-cn'
      case 'pt': return 'pt-br'
      default: return 'en'
    }
  }

  // 更新 dayjs 语言
  dayjs.locale(getDayjsLocale())

  return (
    <ConfigProvider locale={getAntdLocale()}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RootWrapper />
  </React.StrictMode>
)