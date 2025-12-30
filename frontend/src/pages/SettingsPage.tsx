import React, { useState, useEffect } from 'react'
import { Layout, Card, Form, Input, Button, Typography, Space, Alert, Divider, Row, Col, Tabs, message, Select, Tag } from 'antd'
import { KeyOutlined, SaveOutlined, ApiOutlined, SettingOutlined, InfoCircleOutlined, UserOutlined, RobotOutlined } from '@ant-design/icons'
import { settingsApi } from '../services/api'
import BilibiliManager from '../components/BilibiliManager'
import { useTranslation } from 'react-i18next'
import './SettingsPage.css'

const { Content } = Layout
const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

const SettingsPage: React.FC = () => {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [showBilibiliManager, setShowBilibiliManager] = useState(false)
  const [availableModels, setAvailableModels] = useState<any>({})
  const [currentProvider, setCurrentProvider] = useState<any>({})
  const [selectedProvider, setSelectedProvider] = useState('dashscope')

  // 提供商配置
  const providerConfig = {
    dashscope: {
      name: 'DashScope',
      icon: <RobotOutlined />,
      color: '#1890ff',
      description: t('settings.providers.dashscope'),
      apiKeyField: 'dashscope_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    openai: {
      name: 'OpenAI',
      icon: <RobotOutlined />,
      color: '#52c41a',
      description: t('settings.providers.openai'),
      apiKeyField: 'openai_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    gemini: {
      name: 'Google Gemini',
      icon: <RobotOutlined />,
      color: '#faad14',
      description: t('settings.providers.gemini'),
      apiKeyField: 'gemini_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    siliconflow: {
      name: 'SiliconFlow',
      icon: <RobotOutlined />,
      color: '#722ed1',
      description: t('settings.providers.siliconflow'),
      apiKeyField: 'siliconflow_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    groq: {
      name: 'Groq',
      icon: <RobotOutlined />,
      color: '#f5222d',
      description: t('settings.providers.groq'),
      apiKeyField: 'groq_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    together: {
      name: 'Together AI',
      icon: <RobotOutlined />,
      color: '#eb2f96',
      description: t('settings.providers.together'),
      apiKeyField: 'together_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    openrouter: {
      name: 'OpenRouter',
      icon: <RobotOutlined />,
      color: '#2f54eb',
      description: t('settings.providers.openrouter'),
      apiKeyField: 'openrouter_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    g4f: {
      name: 'GPT4Free',
      icon: <RobotOutlined />,
      color: '#fa541c',
      description: t('settings.providers.g4f'),
      apiKeyField: 'g4f_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    },
    cerebras: {
      name: 'Cerebras',
      icon: <RobotOutlined />,
      color: '#34d399',
      description: t('settings.providers.cerebras'),
      apiKeyField: 'cerebras_api_key',
      placeholder: t('settings.form.api_key_placeholder')
    }
  }

  // 加载数据
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [settings, models, provider] = await Promise.all([
        settingsApi.getSettings(),
        settingsApi.getAvailableModels(),
        settingsApi.getCurrentProvider()
      ])
      
      setAvailableModels(models)
      setCurrentProvider(provider)
      setSelectedProvider(settings.llm_provider || 'dashscope')
      
      // 设置表单初始值
      form.setFieldsValue(settings)
    } catch (error) {
      console.error('加载数据失败:', error)
    }
  }

  // 保存配置
  const handleSave = async (values: any) => {
    try {
      setLoading(true)
      await settingsApi.updateSettings(values)
      message.success(t('settings.form.save_success'))
      await loadData() // 重新加载数据
    } catch (error: any) {
      message.error(t('settings.form.save_failed', { error: error.message || t('common.error') }))
    } finally {
      setLoading(false)
    }
  }

  // 测试API密钥
  const handleTestApiKey = async () => {
    const apiKey = form.getFieldValue(providerConfig[selectedProvider as keyof typeof providerConfig].apiKeyField)
    const modelName = form.getFieldValue('model_name')
    
    if (!apiKey) {
      message.error(t('settings.form.api_key_error'))
      return
    }

    if (!modelName) {
      message.error(t('settings.form.model_error'))
      return
    }

    try {
      setLoading(true)
      const result = await settingsApi.testApiKey(selectedProvider, apiKey, modelName)
      if (result.status === 'success') {
        message.success(t('settings.form.test_success'))
      } else {
        message.error(t('settings.form.test_failed', { error: result.message || t('common.error') }))
      }
    } catch (error: any) {
      message.error(t('settings.form.test_failed', { error: error.message || t('common.error') }))
    } finally {
      setLoading(false)
    }
  }

  // 提供商切换
  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider)
    form.setFieldsValue({ llm_provider: provider })
  }

  return (
    <Content className="settings-page">
      <div className="settings-container">
        <Title level={2} className="settings-title">
          <SettingOutlined /> {t('settings.title')}
        </Title>
        
        <Tabs defaultActiveKey="api" className="settings-tabs">
          <TabPane tab={t('settings.tabs.api')} key="api">
            <Card title={t('settings.card.api_title')} className="settings-card">
              <Alert
                message={t('settings.alert.multi_provider')}
                description={t('settings.alert.multi_provider_desc')}
                type="info"
                showIcon
                className="settings-alert"
              />
              
              <Form
                form={form}
                layout="vertical"
                className="settings-form"
                onFinish={handleSave}
                initialValues={{
                  llm_provider: 'dashscope',
                  model_name: 'qwen-plus',
                  chunk_size: 1500,
                  min_score_threshold: 0.3,
                  max_clips_per_collection: 5
                }}
              >
                {/* 当前提供商状态 */}
                {currentProvider.available && (
                  <Alert
                    message={t('settings.form.current_usage', { provider: currentProvider.display_name, model: currentProvider.model })}
                    type="success"
                    showIcon
                    style={{ marginBottom: 24 }}
                  />
                )}

                {/* 提供商选择 */}
                <Form.Item
                  label={t('settings.form.provider_label')}
                  name="llm_provider"
                  className="form-item"
                  rules={[{ required: true, message: t('settings.form.provider_placeholder') }]}
                >
                  <Select
                    value={selectedProvider}
                    onChange={handleProviderChange}
                    className="settings-input"
                    placeholder={t('settings.form.provider_placeholder')}
                  >
                    {Object.entries(providerConfig).map(([key, config]) => (
                      <Select.Option key={key} value={key}>
                        <Space>
                          <span style={{ color: config.color }}>{config.icon}</span>
                          <span>{config.name}</span>
                          <Tag color={config.color}>{config.description}</Tag>
                        </Space>
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>

                {/* 动态API密钥输入 */}
                <Form.Item
                  label={t('settings.form.api_key_label', { provider: providerConfig[selectedProvider as keyof typeof providerConfig].name })}
                  name={providerConfig[selectedProvider as keyof typeof providerConfig].apiKeyField}
                  className="form-item"
                  rules={[
                    { required: true, message: t('settings.form.api_key_required') },
                    { min: 10, message: t('settings.form.api_key_min') }
                  ]}
                >
                  <Input.Password
                    placeholder={providerConfig[selectedProvider as keyof typeof providerConfig].placeholder}
                    prefix={<KeyOutlined />}
                    className="settings-input"
                  />
                </Form.Item>

                {/* 模型选择 */}
                <Form.Item
                  label={t('settings.form.model_label')}
                  name="model_name"
                  className="form-item"
                  rules={[{ required: true, message: t('settings.form.model_required') }]}
                >
                  <Select
                    className="settings-input"
                    placeholder={t('settings.form.model_placeholder')}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                    }
                  >
                    {availableModels[selectedProvider]?.map((model: any) => (
                      <Select.Option key={model.name} value={model.name}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                          <Space>
                            <span style={{ fontWeight: 500 }}>{model.display_name}</span>
                            {model.is_free && <Tag color="green" style={{ borderRadius: '4px', margin: 0 }}>FREE</Tag>}
                          </Space>
                          <Tag style={{ border: 'none', background: 'rgba(255,255,255,0.1)', color: '#aaa', margin: 0 }}>
                            {model.max_tokens >= 1000 ? `${model.max_tokens/1000}k` : model.max_tokens} tokens
                          </Tag>
                        </div>
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item className="form-item">
                  <Space>
                    <Button
                      type="default"
                      icon={<ApiOutlined />}
                      className="test-button"
                      onClick={handleTestApiKey}
                      loading={loading}
                    >
                      {t('settings.form.test_connection')}
                    </Button>
                  </Space>
                </Form.Item>

                <Divider className="settings-divider" />

                <Title level={4} className="section-title">{t('settings.form.section_model_config')}</Title>
                
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      label={t('settings.form.model_name_label')}
                      name="model_name"
                      className="form-item"
                    >
                      <Input placeholder="qwen-plus" className="settings-input" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label={t('settings.form.chunk_size_label')}
                      name="chunk_size"
                      className="form-item"
                    >
                      <Input 
                        type="number" 
                        placeholder="1500" 
                        addonAfter={t('settings.form.chunk_size_unit')} 
                        className="settings-input"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      label={t('settings.form.min_score_label')}
                      name="min_score_threshold"
                      className="form-item"
                    >
                      <Input 
                        type="number" 
                        step="0.1" 
                        min="0" 
                        max="1" 
                        placeholder="0.3" 
                        className="settings-input"
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label={t('settings.form.max_clips_label')}
                      name="max_clips_per_collection"
                      className="form-item"
                    >
                      <Input 
                        type="number" 
                        placeholder="5" 
                        addonAfter={t('settings.form.max_clips_unit')} 
                        className="settings-input"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item className="form-item">
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<SaveOutlined />}
                    size="large"
                    className="save-button"
                    loading={loading}
                  >
                    {t('settings.form.save_button')}
                  </Button>
                </Form.Item>
              </Form>
            </Card>

            <Card title={t('settings.instructions.title')} className="settings-card">
              <Space direction="vertical" size="large" className="instructions-space">
                <div className="instruction-item">
                  <Title level={5} className="instruction-title">
                    <InfoCircleOutlined /> {t('settings.instructions.step1_title')}
                  </Title>
                  <Paragraph className="instruction-text">
                    {t('settings.instructions.step1_desc')}
                    <br />• <Text strong>DashScope</Text>：访问 dashscope.console.aliyun.com 获取API密钥
                    <br />• <Text strong>OpenAI</Text>：访问 platform.openai.com 获取API密钥
                    <br />• <Text strong>Google Gemini</Text>：访问 ai.google.dev 获取API密钥
                    <br />• <Text strong>SiliconFlow</Text>：访问 docs.siliconflow.cn 获取API密钥
                    <br />• <Text strong>Groq</Text>：访问 console.groq.com 获取API密钥
                    <br />• <Text strong>OpenRouter</Text>：访问 openrouter.ai 获取API密钥
                    <br />• <Text strong>GPT4Free</Text>：无需密钥，直接使用
                    <br />• <Text strong>Cerebras</Text>：{t('settings.instructions.cerebras_info')}
                  </Paragraph>
                </div>
                
                <div className="instruction-item">
                  <Title level={5} className="instruction-title">
                    <InfoCircleOutlined /> {t('settings.instructions.step2_title')}
                  </Title>
                  <Paragraph className="instruction-text">
                    <div dangerouslySetInnerHTML={{ __html: t('settings.instructions.step2_desc') }} />
                  </Paragraph>
                </div>
                
                <div className="instruction-item">
                  <Title level={5} className="instruction-title">
                    <InfoCircleOutlined /> {t('settings.instructions.step3_title')}
                  </Title>
                  <Paragraph className="instruction-text">
                    {t('settings.instructions.step3_desc')}
                  </Paragraph>
                </div>
              </Space>
            </Card>
          </TabPane>

          <TabPane tab={t('settings.tabs.bilibili')} key="bilibili">
            <Card title={t('settings.bilibili.title')} className="settings-card">
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <div style={{ marginBottom: '24px' }}>
                  <UserOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
                  <Title level={3} style={{ color: '#ffffff', margin: '0 0 8px 0' }}>
                    {t('settings.bilibili.title')}
                  </Title>
                  <Text type="secondary" style={{ color: '#b0b0b0', fontSize: '16px' }}>
                    {t('settings.bilibili.desc')}
                  </Text>
                </div>
                
                <Space size="large">
                  <Button
                    type="primary"
                    size="large"
                    icon={<UserOutlined />}
                    onClick={() => message.info(t('clip.dev_hint'), 3)}
                    style={{
                      borderRadius: '8px',
                      background: 'linear-gradient(45deg, #1890ff, #36cfc9)',
                      border: 'none',
                      fontWeight: 500,
                      height: '48px',
                      padding: '0 32px',
                      fontSize: '16px'
                    }}
                  >
                    {t('settings.bilibili.manage_button')}
                  </Button>
                </Space>
                
                <div style={{ marginTop: '32px', textAlign: 'left', maxWidth: '600px', margin: '32px auto 0' }}>
                  <Title level={4} style={{ color: '#ffffff', marginBottom: '16px' }}>
                    {t('settings.bilibili.features_title')}
                  </Title>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
                    <div style={{ 
                      padding: '16px', 
                      background: 'rgba(255,255,255,0.05)', 
                      borderRadius: '8px',
                      border: '1px solid #404040'
                    }}>
                      <Text strong style={{ color: '#1890ff' }}>{t('settings.bilibili.feature_multi_account')}</Text>
                      <br />
                      <Text type="secondary" style={{ color: '#b0b0b0' }}>
                        {t('settings.bilibili.feature_multi_account_desc')}
                      </Text>
                    </div>
                    <div style={{ 
                      padding: '16px', 
                      background: 'rgba(255,255,255,0.05)', 
                      borderRadius: '8px',
                      border: '1px solid #404040'
                    }}>
                      <Text strong style={{ color: '#52c41a' }}>{t('settings.bilibili.feature_secure_login')}</Text>
                      <br />
                      <Text type="secondary" style={{ color: '#b0b0b0' }}>
                        {t('settings.bilibili.feature_secure_login_desc')}
                      </Text>
                    </div>
                    <div style={{ 
                      padding: '16px', 
                      background: 'rgba(255,255,255,0.05)', 
                      borderRadius: '8px',
                      border: '1px solid #404040'
                    }}>
                      <Text strong style={{ color: '#faad14' }}>{t('settings.bilibili.feature_fast_post')}</Text>
                      <br />
                      <Text type="secondary" style={{ color: '#b0b0b0' }}>
                        {t('settings.bilibili.feature_fast_post_desc')}
                      </Text>
                    </div>
                    <div style={{ 
                      padding: '16px', 
                      background: 'rgba(255,255,255,0.05)', 
                      borderRadius: '8px',
                      border: '1px solid #404040'
                    }}>
                      <Text strong style={{ color: '#722ed1' }}>{t('settings.bilibili.feature_batch_manage')}</Text>
                      <br />
                      <Text type="secondary" style={{ color: '#b0b0b0' }}>
                        {t('settings.bilibili.feature_batch_manage_desc')}
                      </Text>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </TabPane>
        </Tabs>

        {/* B站管理弹窗 */}
        <BilibiliManager
          visible={showBilibiliManager}
          onClose={() => setShowBilibiliManager(false)}
          onUploadSuccess={() => {
            message.success(t('common.success'))
          }}
        />
      </div>
    </Content>
  )
}

export default SettingsPage