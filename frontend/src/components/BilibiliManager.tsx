import React, { useState, useEffect } from 'react'
import { Button, Modal, Form, Input, Table, Tag, Space, message, Popconfirm, Tabs, Alert, Typography, Select, Row, Col, Tooltip, Progress, Descriptions, Statistic, Card } from 'antd'
import { useTranslation } from 'react-i18next'
import { PlusOutlined, DeleteOutlined, UserOutlined, CheckCircleOutlined, CloseCircleOutlined, UploadOutlined, QuestionCircleOutlined, ReloadOutlined, EyeOutlined, RedoOutlined, StopOutlined, ExclamationCircleOutlined, ClockCircleOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { uploadApi, BilibiliAccount, BILIBILI_PARTITIONS, UploadRecord } from '../services/uploadApi'
import './BilibiliManager.css'

const { TextArea } = Input
const { Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

interface BilibiliManagerProps {
  visible: boolean
  onClose: () => void
  projectId?: string
  clipIds?: string[]
  clipTitles?: string[]
  onUploadSuccess?: () => void
}

const BilibiliManager: React.FC<BilibiliManagerProps> = ({
  visible,
  onClose,
  projectId,
  clipIds = [],
  clipTitles = [],
  onUploadSuccess
}) => {
  const { t, i18n } = useTranslation()
  const [activeTab, setActiveTab] = useState('upload')
  const [accounts, setAccounts] = useState<BilibiliAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [showAddAccount, setShowAddAccount] = useState(false)
  const [cookieForm] = Form.useForm()
  const [uploadForm] = Form.useForm()
  
  // 投稿状态相关状态
  const [uploadRecords, setUploadRecords] = useState<UploadRecord[]>([])
  const [recordsLoading, setRecordsLoading] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<UploadRecord | null>(null)
  const [detailModalVisible, setDetailModalVisible] = useState(false)

  // 获取账号列表
  const fetchAccounts = async () => {
    try {
      setLoading(true)
      const data = await uploadApi.getAccounts()
      setAccounts(data)
    } catch (error: any) {
      message.error(`${t('settings.form.test_failed', { error: '' })} ${error.message || t('common.error')}`)
    } finally {
      setLoading(false)
    }
  }

  // 获取投稿记录
  const fetchUploadRecords = async () => {
    try {
      setRecordsLoading(true)
      const data = await uploadApi.getUploadRecords()
      setUploadRecords(data)
    } catch (error: any) {
      message.error(`${t('common.error')}: ${error.message || t('common.error')}`)
    } finally {
      setRecordsLoading(false)
    }
  }

  // 重试投稿
  const handleRetry = async (recordId: string | number) => {
    try {
      await uploadApi.retryUpload(recordId)
      message.success(t('bili.retry_pushed'))
      fetchUploadRecords()
    } catch (error: any) {
      message.error(`${t('common.error')}: ${error.message || t('common.error')}`)
    }
  }

  // 取消投稿
  const handleCancel = async (recordId: string | number) => {
    try {
      await uploadApi.cancelUpload(recordId)
      message.success(t('common.success'))
      fetchUploadRecords()
    } catch (error: any) {
      message.error(t('common.error') + ': ' + (error.message || t('common.error')))
    }
  }

  // 删除投稿
  const handleDelete = async (recordId: string | number) => {
    try {
      await uploadApi.deleteUpload(recordId)
      message.success(t('common.success'))
      fetchUploadRecords()
    } catch (error: any) {
      message.error(t('common.error') + ': ' + (error.message || t('common.error')))
    }
  }

  // 查看详情
  const handleViewDetail = (record: UploadRecord) => {
    setSelectedRecord(record)
    setDetailModalVisible(true)
  }

  useEffect(() => {
    if (visible) {
      fetchAccounts()
      fetchUploadRecords()
      // 如果有切片数据，默认显示上传标签页
      if (clipIds.length > 0) {
        setActiveTab('upload')
      } else {
        setActiveTab('accounts')
      }
    }
  }, [visible, clipIds])

  // Cookie导入登录
  const handleCookieLogin = async (values: any) => {
    try {
      setLoading(true)
      
      // 解析Cookie字符串
      const cookieStr = values.cookies.trim()
      const cookies: Record<string, string> = {}
      
      cookieStr.split(';').forEach((cookie: string) => {
        const trimmedCookie = cookie.trim()
        const equalIndex = trimmedCookie.indexOf('=')
        if (equalIndex > 0) {
          const key = trimmedCookie.substring(0, equalIndex).trim()
          const value = trimmedCookie.substring(equalIndex + 1).trim()
          if (key && value) {
            cookies[key] = value
          }
        }
      })
      
      if (Object.keys(cookies).length === 0) {
        message.error(t('bili.cookie_format_error'))
        return
      }
      
      await uploadApi.cookieLogin(cookies, values.nickname)
      message.success(t('bili.add_success'))
      setShowAddAccount(false)
      cookieForm.resetFields()
      fetchAccounts()
    } catch (error: any) {
      message.error(t('common.error') + ': ' + (error.message || t('common.error')))
    } finally {
      setLoading(false)
    }
  }

  // 删除账号
  const handleDeleteAccount = async (accountId: string) => {
    try {
      await uploadApi.deleteAccount(accountId)
      message.success(t('bili.delete_account_success'))
      fetchAccounts()
    } catch (error: any) {
      message.error(t('common.error') + ': ' + (error.message || t('common.error')))
    }
  }

  // 提交上传
  const handleUpload = async (values: any) => {
    // 显示开发中提示
    message.info(t('clip.dev_hint'), 3)
    return
    
    // 原有代码已禁用
    if (!projectId || clipIds.length === 0) {
      message.error('没有选择要上传的切片')
      return
    }

    try {
      setLoading(true)
      
      const uploadData = {
        account_id: values.account_id,
        clip_ids: clipIds,
        title: values.title,
        description: values.description || '',
        tags: values.tags ? values.tags.split(',').map((tag: string) => tag.trim()) : [],
        partition_id: values.partition_id
      }

      // 调用上传API
      const response = await fetch(`/api/v1/upload/projects/${projectId}/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(uploadData)
      })

      if (response.ok) {
        message.success(t('bili.upload_pushed'))
        onUploadSuccess?.()
        onClose()
      } else {
        const error = await response.json()
        message.error(t('bili.upload_failed') + ': ' + (error.detail || t('common.error')))
      }
    } catch (error: any) {
      message.error(t('bili.upload_failed') + ': ' + (error.message || t('common.error')))
    } finally {
      setLoading(false)
    }
  }

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: t('status.pending') },
      processing: { color: 'processing', icon: <PlayCircleOutlined />, text: t('status.processing') },
      success: { color: 'success', icon: <CheckCircleOutlined />, text: t('status.success') },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: t('status.completed') },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: t('status.failed') },
      cancelled: { color: 'default', icon: <StopOutlined />, text: t('status.cancelled') }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    )
  }

  // 获取分区名称
  const getPartitionName = (partitionId: number) => {
    const partition = BILIBILI_PARTITIONS.find(p => p.id === partitionId)
    return partition ? partition.name : `${t('bili.video_partition')}${partitionId}`
  }

  // 格式化文件大小
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-'
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
  }

  // 格式化时长
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}${t('common.hour')}${minutes}${t('common.minute')}`
    } else if (minutes > 0) {
      return `${minutes}${t('common.minute')}${secs}${t('common.second')}`
    } else {
      return `${secs}${t('common.second')}`
    }
  }

  // 获取统计信息
  const getStatistics = () => {
    const total = uploadRecords.length
    const success = uploadRecords.filter(r => r.status === 'success' || r.status === 'completed').length
    const failed = uploadRecords.filter(r => r.status === 'failed').length
    const processing = uploadRecords.filter(r => r.status === 'processing').length
    const pending = uploadRecords.filter(r => r.status === 'pending').length
    
    return { total, success, failed, processing, pending }
  }

  // Cookie获取指南内容
  const cookieGuideContent = (
    <div style={{ maxWidth: 300 }}>
      <div style={{ marginBottom: 8, fontWeight: 'bold' }}>{t('bili.cookie_guide_steps')}</div>
      <ol style={{ margin: 0, paddingLeft: 16 }}>
        <li>{t('bili.cookie_step1')}</li>
        <li>{t('bili.cookie_step2')}</li>
        <li>{t('bili.cookie_step3')}</li>
        <li>{t('bili.cookie_step4')}</li>
        <li>{t('bili.cookie_step5')}</li>
        <li>{t('bili.cookie_step6')}</li>
        <li>{t('bili.cookie_step7')}</li>
      </ol>
    </div>
  )

  // 账号管理表格列
  const accountColumns = [
    {
      title: t('bili.nickname'),
      dataIndex: 'nickname',
      key: 'nickname',
      render: (nickname: string, record: BilibiliAccount) => (
        <Space>
          <UserOutlined />
          <span>{nickname || record.username}</span>
        </Space>
      ),
    },
    {
      title: t('bili.username'),
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: t('status.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'} icon={status === 'active' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {status === 'active' ? t('bili.status_active') : t('bili.status_error')}
        </Tag>
      ),
    },
    {
      title: t('bili.action_label'),
      key: 'action',
      render: (_: any, record: BilibiliAccount) => (
        <Popconfirm
          title={t('bili.confirm_delete_account')}
          description={t('bili.delete_account_desc')}
          onConfirm={() => handleDeleteAccount(record.id)}
          okText={t('common.ok')}
          cancelText={t('common.cancel')}
        >
          <Button type="text" danger icon={<DeleteOutlined />} size="small">
            {t('common.delete')}
          </Button>
        </Popconfirm>
      ),
    },
  ]

  // 投稿状态表格列
  const uploadStatusColumns = [
    {
      title: t('bili.task_id'),
      dataIndex: 'id',
      key: 'id',
      width: 80,
      render: (id: string | number) => <Text code>{id}</Text>
    },
    {
      title: t('bili.title_label'),
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title: string) => (
        <Tooltip title={title}>
          <Text>{title}</Text>
        </Tooltip>
      )
    },
    {
      title: t('bili.account_label'),
      dataIndex: 'account_nickname',
      key: 'account_nickname',
      width: 120,
      render: (nickname: string, record: UploadRecord) => (
        <div>
          <div>{nickname || record.account_username}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.account_username}
          </Text>
        </div>
      )
    },
    {
      title: t('bili.video_partition'),
      dataIndex: 'partition_id',
      key: 'partition_id',
      width: 100,
      render: (partitionId: number) => (
        <Tag>{getPartitionName(partitionId)}</Tag>
      )
    },
    {
      title: t('status.status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status)
    },
    {
      title: t('status.progress'),
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress: number, record: UploadRecord) => {
        if (record.status === 'success' || record.status === 'completed') {
          return <Progress percent={100} size="small" status="success" />
        } else if (record.status === 'failed') {
          return <Progress percent={progress} size="small" status="exception" />
        } else if (record.status === 'processing') {
          return <Progress percent={progress} size="small" status="active" />
        } else {
          return <Progress percent={progress} size="small" />
        }
      }
    },
    {
      title: t('bili.file_size'),
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (fileSize: number) => <span>{formatFileSize(fileSize)}</span>
    },
    {
      title: t('common.created_at'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => <span>{new Date(date).toLocaleString()}</span>
    },
    {
      title: t('bili.action_label'),
      key: 'actions',
      width: 200,
      render: (_: any, record: UploadRecord) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => handleViewDetail(record)}
            size="small"
          >
            {t('common.view_details')}
          </Button>
          {record.status === 'failed' && (
            <Popconfirm
              title={t('bili.confirm_retry')}
              onConfirm={() => handleRetry(record.id)}
              okText={t('common.ok')}
              cancelText={t('common.cancel')}
            >
              <Button 
                type="link" 
                icon={<RedoOutlined />} 
                size="small"
              >
                {t('common.retry')}
              </Button>
            </Popconfirm>
          )}
          {(record.status === 'pending' || record.status === 'processing') && (
            <Popconfirm
              title={t('bili.confirm_cancel')}
              onConfirm={() => handleCancel(record.id)}
              okText={t('common.ok')}
              cancelText={t('common.cancel')}
            >
              <Button 
                type="link" 
                icon={<StopOutlined />} 
                danger
                size="small"
              >
                {t('common.cancel')}
              </Button>
            </Popconfirm>
          )}
          {(record.status === 'success' || record.status === 'completed' || record.status === 'failed' || record.status === 'cancelled') && (
            <Popconfirm
              title={t('bili.confirm_delete_task')}
              onConfirm={() => handleDelete(record.id)}
              okText={t('common.ok')}
              cancelText={t('common.cancel')}
            >
              <Button 
                type="link" 
                icon={<DeleteOutlined />} 
                danger
                size="small"
              >
                {t('common.delete')}
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ]

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      destroyOnClose
      className="bilibili-manager-modal"
    >
      {/* 自定义标题栏 */}
      <div className="bilibili-manager-header">
        <div className="bilibili-manager-header-icon">
          <UploadOutlined />
        </div>
        <div className="bilibili-manager-header-content">
          <h2 className="bilibili-manager-header-title">{t('bili.manager_title')}</h2>
          <p className="bilibili-manager-header-subtitle">
            {clipIds.length > 0 
              ? t('bili.prepare_upload', { count: clipIds.length }) 
              : t('bili.manage_accounts_subtitle')
            }
          </p>
        </div>
      </div>

      <div className="bilibili-manager-tabs">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 上传标签页 */}
        {clipIds.length > 0 && (
          <TabPane 
            tab={
              <span>
                <UploadOutlined />
                {t('bili.upload_tab')}
              </span>
            } 
            key="upload"
          >
            <div className="bilibili-manager-content">
              <Alert
                message={t('bili.upload_info')}
                description={t('bili.prepare_upload', { count: clipIds.length })}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form
              form={uploadForm}
              onFinish={handleUpload}
              layout="vertical"
              initialValues={{
                title: clipTitles.length === 1 ? clipTitles[0] : t('bili.batch_title_placeholder', { title: clipTitles[0], count: clipIds.length }),
                partition_id: 4 // 默认游戏分区
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label={t('bili.select_account')}
                    name="account_id"
                    rules={[{ required: true, message: t('bili.select_account_placeholder') }]}
                  >
                    <Select 
                      placeholder={t('bili.select_account_placeholder')}
                      notFoundContent={
                        <div style={{ textAlign: 'center', padding: '20px' }}>
                          <p>{t('bili.no_accounts')}</p>
                          <Button 
                            type="link" 
                            icon={<PlusOutlined />}
                            onClick={() => setShowAddAccount(true)}
                          >
                            {t('bili.add_account')}
                          </Button>
                        </div>
                      }
                    >
                      {accounts.filter(acc => acc.status === 'active').map(account => (
                        <Option key={account.id} value={account.id}>
                          {account.nickname || account.username}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label={t('bili.video_partition')}
                    name="partition_id"
                    rules={[{ required: true, message: t('bili.video_partition_placeholder') }]}
                  >
                    <Select placeholder={t('bili.video_partition_placeholder')} showSearch>
                      {BILIBILI_PARTITIONS.map(partition => (
                        <Option key={partition.id} value={partition.id}>
                          {partition.name}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label={t('bili.title_label')}
                name="title"
                rules={[{ required: true, message: t('bili.title_placeholder') }]}
              >
                <Input placeholder={t('bili.title_placeholder')} maxLength={80} showCount />
              </Form.Item>

              <Form.Item
                label={t('bili.desc_label')}
                name="description"
              >
                <TextArea
                  placeholder={t('bili.desc_placeholder')}
                  rows={3}
                  maxLength={2000}
                  showCount
                />
              </Form.Item>

              <Form.Item
                label={t('bili.tags_label')}
                name="tags"
              >
                <Input placeholder={t('bili.tags_placeholder')} />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    onClick={() => message.info(t('clip.dev_hint'), 3)}
                    icon={<UploadOutlined />}
                  >
                    {t('bili.start_upload')}
                  </Button>
                  <Button onClick={onClose}>
                    {t('common.cancel')}
                  </Button>
                </Space>
              </Form.Item>
              </Form>
            </div>
          </TabPane>
        )}

        {/* 账号管理标签页 */}
        <TabPane 
          tab={
            <span>
              <UserOutlined />
              账号管理
            </span>
          } 
          key="accounts"
        >
          <div className="bilibili-manager-content">
            <div style={{ marginBottom: 16 }}>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setShowAddAccount(true)}
              >
                添加账号
              </Button>
            </div>

            <Table
              columns={accountColumns}
              dataSource={accounts}
              rowKey="id"
              loading={loading}
              pagination={false}
              size="small"
            />
          </div>
        </TabPane>

        {/* 投稿状态标签页 */}
        <TabPane 
          tab={
            <span>
              <ReloadOutlined />
              投稿状态
            </span>
          } 
          key="status"
        >
          <div className="bilibili-manager-content">
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#ffffff' }}>投稿任务状态</h3>
              <Button 
                type="primary" 
                icon={<ReloadOutlined />} 
                onClick={fetchUploadRecords}
                loading={recordsLoading}
              >
                刷新
              </Button>
            </div>

            {/* 统计信息 */}
            {(() => {
              const stats = getStatistics()
              return (
                <Row gutter={16} style={{ marginBottom: 24 }}>
                  <Col span={6}>
                    <Card style={{ background: '#262626', border: '1px solid #404040' }}>
                      <Statistic 
                        title={<span style={{ color: '#ffffff' }}>总任务数</span>} 
                        value={stats.total} 
                        valueStyle={{ color: '#ffffff' }} 
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card style={{ background: '#262626', border: '1px solid #404040' }}>
                      <Statistic 
                        title={<span style={{ color: '#ffffff' }}>成功</span>} 
                        value={stats.success} 
                        valueStyle={{ color: '#52c41a' }}
                        prefix={<CheckCircleOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card style={{ background: '#262626', border: '1px solid #404040' }}>
                      <Statistic 
                        title={<span style={{ color: '#ffffff' }}>失败</span>} 
                        value={stats.failed} 
                        valueStyle={{ color: '#ff4d4f' }}
                        prefix={<ExclamationCircleOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card style={{ background: '#262626', border: '1px solid #404040' }}>
                      <Statistic 
                        title={<span style={{ color: '#ffffff' }}>进行中</span>} 
                        value={stats.processing + stats.pending} 
                        valueStyle={{ color: '#1890ff' }}
                        prefix={<PlayCircleOutlined />}
                      />
                    </Card>
                  </Col>
                </Row>
              )
            })()}

            {/* 任务列表 */}
            <Table
              columns={uploadStatusColumns}
              dataSource={uploadRecords}
              rowKey="id"
              loading={recordsLoading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
              scroll={{ x: 1200 }}
              size="small"
            />
          </div>
        </TabPane>
      </Tabs>
      </div>

      {/* 添加账号弹窗 */}
      <Modal
        title="添加B站账号"
        open={showAddAccount}
        onCancel={() => {
          setShowAddAccount(false)
          cookieForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Alert
          message="推荐使用Cookie导入"
          description="Cookie导入是最安全、最稳定的登录方式，不会触发B站风控。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form form={cookieForm} onFinish={handleCookieLogin} layout="vertical">
          <Form.Item
            name="nickname"
            label="账号昵称"
            rules={[{ required: true, message: '请输入账号昵称' }]}
          >
            <Input placeholder="请输入账号昵称，用于识别" />
          </Form.Item>
          
          <Form.Item
            name="cookies"
            label={
              <Space>
                <span>Cookie</span>
                <Tooltip title={cookieGuideContent} placement="topLeft">
                  <Button 
                    type="link" 
                    size="small" 
                    icon={<QuestionCircleOutlined />}
                  >
                    {t('bili.cookie_guide')}
                  </Button>
                </Tooltip>
              </Space>
            }
            rules={[
              { required: true, message: t('bili.cookie_required') },
              { min: 10, message: t('bili.cookie_min_length') }
            ]}
          >
            <TextArea
              rows={4}
              placeholder={t('bili.cookie_placeholder')}
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                {t('bili.add_account')}
              </Button>
              <Button onClick={() => setShowAddAccount(false)}>
                {t('common.cancel')}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 投稿状态详情模态框 */}
      <Modal
        title={t('bili.upload_detail_title')}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
        className="bilibili-manager-modal"
      >
        {selectedRecord && (
          <div>
            <Descriptions 
              column={2} 
              bordered
              labelStyle={{ 
                background: '#1f1f1f', 
                color: '#ffffff',
                fontWeight: 'bold',
                borderRight: '1px solid #303030'
              }}
              contentStyle={{ 
                background: '#262626', 
                color: '#ffffff',
                borderLeft: '1px solid #303030'
              }}
              style={{ 
                background: '#262626',
                border: '1px solid #303030'
              }}
            >
              <Descriptions.Item label={t('bili.task_id')} span={1}>
                <Text code>{selectedRecord.id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('status.status')} span={1}>
                {getStatusTag(selectedRecord.status)}
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.title_label')} span={2}>
                <Text>{selectedRecord.title}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.account_label')} span={1}>
                <Text>{selectedRecord.account_nickname || selectedRecord.account_username}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.video_partition')} span={1}>
                <Tag>{getPartitionName(selectedRecord.partition_id)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('project.project_name')} span={1}>
                <Text>{selectedRecord.project_name || '-'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.clip_id')} span={1}>
                <Text code>{selectedRecord.clip_id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('status.progress')} span={2}>
                <Progress 
                  percent={selectedRecord.progress} 
                  status={
                    selectedRecord.status === 'failed' ? 'exception' :
                    selectedRecord.status === 'success' || selectedRecord.status === 'completed' ? 'success' :
                    selectedRecord.status === 'processing' ? 'active' : 'normal'
                  }
                />
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.file_size')} span={1}>
                <Text>{formatFileSize(selectedRecord.file_size)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.upload_duration')} span={1}>
                <Text>{formatDuration(selectedRecord.upload_duration)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.bv_id')} span={1}>
                {selectedRecord.bv_id ? <Text code>{selectedRecord.bv_id}</Text> : <Text>-</Text>}
              </Descriptions.Item>
              <Descriptions.Item label={t('bili.av_id')} span={1}>
                {selectedRecord.av_id ? <Text code>{selectedRecord.av_id}</Text> : <Text>-</Text>}
              </Descriptions.Item>
              <Descriptions.Item label={t('common.created_at')} span={1}>
                <Text>{new Date(selectedRecord.created_at).toLocaleString()}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('common.updated_at')} span={1}>
                <Text>{new Date(selectedRecord.updated_at).toLocaleString()}</Text>
              </Descriptions.Item>
            </Descriptions>

            {selectedRecord.description && (
              <div style={{ marginTop: '16px' }}>
                <h4 style={{ color: '#ffffff' }}>{t('bili.desc_label')}</h4>
                <Text>{selectedRecord.description}</Text>
              </div>
            )}

            {selectedRecord.tags && (
              <div style={{ marginTop: '16px' }}>
                <h4 style={{ color: '#ffffff' }}>{t('bili.tags_label')}</h4>
                <Text>{selectedRecord.tags}</Text>
              </div>
            )}

            {selectedRecord.error_message && (
              <div style={{ marginTop: '16px' }}>
                <h4 style={{ color: '#ffffff' }}>{t('common.error_info')}</h4>
                <Alert
                  message={t('bili.upload_failed')}
                  description={selectedRecord.error_message}
                  type="error"
                  showIcon
                />
              </div>
            )}

            <div style={{ marginTop: '24px', textAlign: 'right' }}>
              <Space>
                {selectedRecord.status === 'failed' && (
                  <Popconfirm
                    title={t('bili.confirm_retry')}
                    onConfirm={() => {
                      handleRetry(selectedRecord.id)
                      setDetailModalVisible(false)
                    }}
                    okText={t('common.ok')}
                    cancelText={t('common.cancel')}
                  >
                    <Button type="primary" icon={<RedoOutlined />}>
                      {t('common.retry')}
                    </Button>
                  </Popconfirm>
                )}
                <Button onClick={() => setDetailModalVisible(false)}>
                  {t('common.close')}
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </Modal>
  )
}

export default BilibiliManager
