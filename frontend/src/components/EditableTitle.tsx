import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, Space, message, Tooltip, Modal } from 'antd'
import { EditOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { projectApi } from '../services/api'
import MagicWandIcon from './icons/MagicWandIcon'

interface EditableTitleProps {
  title: string
  clipId: string
  onTitleUpdate?: (newTitle: string) => void
  maxLength?: number
  style?: React.CSSProperties
  className?: string
}

const EditableTitle: React.FC<EditableTitleProps> = ({
  title,
  clipId,
  onTitleUpdate,
  maxLength = 200,
  style,
  className
}) => {
  const { t } = useTranslation()
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(title)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const inputRef = useRef<any>(null)

  // 当外部title变化时，同步内部状态
  useEffect(() => {
    setEditValue(title)
  }, [title])

  // 当title变化时，如果不在编辑模式，确保显示最新值
  useEffect(() => {
    if (!isEditing) {
      setEditValue(title)
    }
  }, [title, isEditing])

  // 进入编辑模式时聚焦输入框
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      // TextArea组件没有select方法，使用setSelectionRange代替
      if (inputRef.current.setSelectionRange) {
        inputRef.current.setSelectionRange(0, inputRef.current.value.length)
      }
    }
  }, [isEditing])

  const handleStartEdit = () => {
    setEditValue(title)
    setIsEditing(true)
  }

  const handleCancel = () => {
    setEditValue(title)
    setIsEditing(false)
  }

  const handleSave = async () => {
    const trimmedValue = editValue.trim()
    
    if (!trimmedValue) {
      message.error(t('edit.empty_error'))
      return
    }
    
    if (trimmedValue.length > maxLength) {
      message.error(t('edit.length_error', { max: maxLength }))
      return
    }
    
    if (trimmedValue === title) {
      setIsEditing(false)
      return
    }

    try {
      await projectApi.updateClipTitle(clipId, trimmedValue)
      message.success(t('edit.update_success'))
      setIsEditing(false)
      // 先更新本地状态，再调用回调
      onTitleUpdate?.(trimmedValue)
    } catch (error: any) {
      console.error('更新标题失败:', error)
      message.error(error.userMessage || error.message || t('edit.update_failed'))
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateTitle = async () => {
    console.log('开始生成标题，clipId:', clipId)
    setGenerating(true)
    try {
      const result = await projectApi.generateClipTitle(clipId)
      if (result.success && result.generated_title) {
        setEditValue(result.generated_title)
        message.success(t('edit.gen_success'))
      } else {
        message.error(t('edit.gen_failed'))
      }
    } catch (error: any) {
      console.error('生成标题失败:', error)
      message.error(error.userMessage || error.message || t('edit.gen_failed'))
    } finally {
      setGenerating(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  if (isEditing) {
    return (
      <Modal
        title={t('edit.title')}
        open={isEditing}
        onCancel={handleCancel}
        footer={null}
        width={600}
        destroyOnClose
        maskClosable={false}
      >
        <div style={{ marginBottom: '16px' }}>
          <Input.TextArea
            ref={inputRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyPress}
            maxLength={maxLength}
            placeholder={t('edit.placeholder')}
            autoSize={{ minRows: 3, maxRows: 8 }}
            style={{ 
              resize: 'none',
              fontSize: '14px',
              lineHeight: '1.5'
            }}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {t('edit.char_count', { count: editValue.length, max: maxLength })}
          </div>
          <Space>
            <Tooltip title={t('edit.ai_gen_tooltip')}>
              <Button
                icon={<MagicWandIcon />}
                loading={generating}
                onClick={() => {
                  console.log('AI生成标题按钮被点击');
                  handleGenerateTitle();
                }}
                disabled={loading}
              >
                {t('edit.ai_gen')}
              </Button>
            </Tooltip>
            <Button onClick={handleCancel} disabled={loading || generating}>
              {t('common.cancel')}
            </Button>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              loading={loading}
              onClick={handleSave}
              disabled={generating}
            >
              {t('common.success')}
            </Button>
          </Space>
        </div>
      </Modal>
    )
  }

  return (
    <div
      style={{
        cursor: 'pointer',
        padding: '4px 0',
        ...style
      }}
      className={className}
      onClick={handleStartEdit}
      title={t('edit.click_to_edit')}
    >
      <span style={{ 
        wordBreak: 'break-word',
        lineHeight: '1.5',
        fontSize: '14px',
        minHeight: '20px',
        display: 'inline'
      }}>
        {title}
        <EditOutlined 
          style={{ 
            color: '#1890ff', 
            fontSize: '12px',
            opacity: 0.7,
            transition: 'opacity 0.2s',
            marginLeft: '6px',
            display: 'inline'
          }}
        />
      </span>
    </div>
  )
}

export default EditableTitle
