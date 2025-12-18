import React, { useState, useEffect } from 'react'
import { Button, message, Progress, Space, Typography, Input } from 'antd'
import { InboxOutlined, VideoCameraOutlined, FileTextOutlined, SubnodeOutlined } from '@ant-design/icons'
import { useDropzone } from 'react-dropzone'
import { useTranslation } from 'react-i18next'
import { projectApi, VideoCategory } from '../services/api'
import { useProjectStore } from '../store/useProjectStore'

const { Text } = Typography

interface FileUploadProps {
  onUploadSuccess?: (projectId: string) => void
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const { t } = useTranslation()
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [projectName, setProjectName] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [categories, setCategories] = useState<VideoCategory[]>([])
  const [files, setFiles] = useState<{
    video?: File
    srt?: File
  }>({})
  
  const { addProject } = useProjectStore()

  // 加载视频分类配置
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await projectApi.getVideoCategories()
        setCategories(response.categories)
        if (response.default_category) {
          setSelectedCategory(response.default_category)
        } else if (response.categories.length > 0) {
          setSelectedCategory(response.categories[0].value)
        }
      } catch (error) {
        console.error('Failed to load video categories:', error)
        message.error(t('upload.cat_error'))
      }
    }

    loadCategories()
  }, [t])

  const onDrop = (acceptedFiles: File[]) => {
    const newFiles = { ...files }
    
    acceptedFiles.forEach(file => {
      const extension = file.name.split('.').pop()?.toLowerCase()
      
      if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(extension || '')) {
        newFiles.video = file
        setProjectName(file.name.replace(/\.[^/.]+$/, ''))
      } else if (extension === 'srt') {
        newFiles.srt = file
      }
    })
    
    setFiles(newFiles)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
      'application/x-subrip': ['.srt']
    },
    multiple: true
  })

  const handleUpload = async () => {
    if (!files.video) {
      message.error(t('upload.video_required'))
      return
    }

    if (!projectName.trim()) {
      message.error(t('upload.project_name_required'))
      return
    }

    setUploading(true)
    setUploadProgress(0)
    
    try {
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 85) {
            clearInterval(progressInterval)
            return prev
          }
          const increment = Math.max(1, Math.floor((90 - prev) / 10))
          return prev + increment
        })
      }, 300)

      const newProject = await projectApi.uploadFiles({
        video_file: files.video,
        srt_file: files.srt,
        project_name: projectName.trim(),
        video_category: selectedCategory
      })
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      
      addProject(newProject)
      message.success(t('upload.success'))
      
      setFiles({})
      setProjectName('')
      setUploadProgress(0)
      setUploading(false)
      
      if (categories.length > 0) {
        setSelectedCategory(categories[0].value)
      }
      
      if (onUploadSuccess) {
        onUploadSuccess(newProject.id)
      }
      
    } catch (error: any) {
      console.error('Upload error:', error)
      
      let errorMessage = t('upload.failed')
      
      if (error.response?.status === 413) {
        errorMessage = t('upload.error_file_too_large')
      } else if (error.response?.status === 415) {
        errorMessage = t('upload.error_unsupported_format')
      } else if (error.response?.status === 400) {
        errorMessage = error.response?.data?.detail || t('upload.error_bad_format_content')
      } else if (error.response?.status === 500) {
        errorMessage = t('upload.error_server_processing')
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = t('upload.error_timeout')
      }
      
      message.error(errorMessage)
      
      if (error.code === 'ECONNABORTED' || error.response?.status >= 500) {
        message.info(t('upload.error_network_suggest'), 5)
      }
    } finally {
      setUploading(false)
    }
  }

  const removeFile = (type: 'video' | 'srt') => {
    setFiles(prev => {
      const newFiles = { ...prev }
      delete newFiles[type]
      return newFiles
    })
  }

  return (
    <div style={{
      borderRadius: '16px',
      padding: '0',
      transition: 'all 0.3s ease',
      position: 'relative',
      overflow: 'hidden',
      width: '100%',
      margin: '0 auto'
    }}>
      <div style={{
        position: 'absolute',
        top: '-50%',
        right: '-50%',
        width: '200%',
        height: '200%',
        background: 'radial-gradient(circle, rgba(79, 172, 254, 0.08) 0%, transparent 70%)',
        pointerEvents: 'none'
      }} />
      
      <div 
        {...getRootProps()} 
        style={{
          padding: '24px 16px',
          textAlign: 'center',
          marginBottom: '16px',
          background: isDragActive ? 'rgba(79, 172, 254, 0.15)' : 'rgba(38, 38, 38, 0.6)',
          border: `2px dashed ${isDragActive ? '#4facfe' : 'rgba(79, 172, 254, 0.3)'}`,
          borderRadius: '16px',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          position: 'relative',
          backdropFilter: 'blur(10px)'
        }}
      >
        <input {...getInputProps()} />
        <div style={{
          width: '48px',
          height: '48px',
          margin: '0 auto 12px',
          background: isDragActive ? 'rgba(79, 172, 254, 0.3)' : 'rgba(79, 172, 254, 0.1)',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s ease',
          border: '1px solid rgba(79, 172, 254, 0.2)'
        }}>
          <InboxOutlined style={{ 
            fontSize: '20px', 
            color: '#4facfe'
          }} />
        </div>
        <div>
          <Text strong style={{ 
            color: '#ffffff',
            fontSize: '16px',
            display: 'block',
            marginBottom: '8px',
            fontWeight: 600
          }}>
            {isDragActive ? t('upload.area_active') : t('upload.area_idle')}
          </Text>
          <Text style={{ color: '#cccccc', fontSize: '14px', lineHeight: '1.5' }}>
            {t('upload.support_formats')}，<Text style={{ color: '#52c41a', fontWeight: 600 }}>{t('upload.subtitle_hint')}</Text>
          </Text>
        </div>
      </div>

      {files.video && (
        <div style={{ marginBottom: '16px' }}>
          <Text strong style={{ color: '#ffffff', fontSize: '14px', marginBottom: '8px', display: 'block' }}>
            {t('upload.project_name')}
          </Text>
          <Input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder={t('upload.project_name_placeholder')}
            style={{ 
              height: '40px',
              borderRadius: '12px',
              fontSize: '14px',
              background: 'rgba(38, 38, 38, 0.8)',
              border: '1px solid rgba(79, 172, 254, 0.3)',
              color: '#ffffff'
            }}
          />
        </div>
      )}

      {files.video && (
        <div style={{ marginBottom: '16px' }}>
          <Text strong style={{ color: '#ffffff', fontSize: '14px', marginBottom: '8px', display: 'block' }}>
            {t('upload.video_category')}
          </Text>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px'
          }}>
            {categories.map(category => {
              const isSelected = selectedCategory === category.value
              return (
                <div
                  key={category.value}
                  onClick={() => setSelectedCategory(category.value)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: isSelected 
                      ? `2px solid ${category.color}` 
                      : '2px solid rgba(255, 255, 255, 0.1)',
                    background: isSelected 
                      ? `${category.color}25` 
                      : 'rgba(255, 255, 255, 0.05)',
                    color: isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.8)',
                    boxShadow: isSelected 
                      ? `0 0 12px ${category.color}40` 
                      : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    fontSize: '13px',
                    fontWeight: isSelected ? 600 : 400,
                    userSelect: 'none'
                  }}
                >
                  <span style={{ fontSize: '14px' }}>{category.icon}</span>
                  <span>{category.name}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {Object.keys(files).length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <Text strong style={{ color: '#ffffff', fontSize: '14px', marginBottom: '12px', display: 'block' }}>
            {t('upload.selected_files')}
          </Text>
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            {files.video && (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                padding: '16px',
                background: 'rgba(38, 38, 38, 0.8)',
                borderRadius: '12px',
                border: '1px solid rgba(79, 172, 254, 0.2)',
                backdropFilter: 'blur(10px)'
              }}>
                <Space size="middle">
                  <div style={{
                    width: '36px',
                    height: '36px',
                    background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 12px rgba(79, 172, 254, 0.3)'
                  }}>
                    <VideoCameraOutlined style={{ color: '#ffffff', fontSize: '16px' }} />
                  </div>
                  <div>
                    <Text style={{ color: '#ffffff', fontWeight: 600, display: 'block', fontSize: '14px' }}>
                      {files.video.name}
                    </Text>
                    <Text style={{ color: '#cccccc', fontSize: '13px' }}>
                      {(files.video.size / 1024 / 1024).toFixed(2)} MB
                    </Text>
                  </div>
                </Space>
                <Button 
                  size="small" 
                  type="text" 
                  onClick={() => removeFile('video')}
                  style={{ 
                    color: '#ff6b6b',
                    borderRadius: '8px',
                    padding: '4px 12px',
                    fontSize: '12px'
                  }}
                >
                  {t('upload.remove_button')}
                </Button>
              </div>
            )}
            {files.srt && (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                padding: '16px',
                background: 'rgba(38, 38, 38, 0.8)',
                borderRadius: '12px',
                border: '1px solid rgba(82, 196, 26, 0.3)',
                backdropFilter: 'blur(10px)'
              }}>
                <Space size="middle">
                  <div style={{
                    width: '36px',
                    height: '36px',
                    background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 12px rgba(82, 196, 26, 0.3)'
                  }}>
                    <FileTextOutlined style={{ color: '#ffffff', fontSize: '16px' }} />
                  </div>
                  <div>
                    <Text style={{ color: '#ffffff', fontWeight: 600, display: 'block', fontSize: '14px' }}>
                      {files.srt.name}
                    </Text>
                    <Text style={{ color: '#cccccc', fontSize: '13px' }}>
                      {t('upload.subtitle_file_label')}
                    </Text>
                  </div>
                </Space>
                <Button 
                  size="small" 
                  type="text" 
                  onClick={() => removeFile('srt')}
                  style={{ 
                    color: '#ff6b6b',
                    borderRadius: '8px',
                    padding: '4px 12px',
                    fontSize: '12px'
                  }}
                >
                  {t('upload.remove_button')}
                </Button>
              </div>
            )}
          </Space>
          
          {files.video && !files.srt && (
            <div style={{
              marginTop: '12px',
              padding: '12px 16px',
              background: 'rgba(82, 196, 26, 0.1)',
              border: '1px solid rgba(82, 196, 26, 0.3)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <SubnodeOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
              <Text style={{ color: '#52c41a', fontSize: '14px', fontWeight: 500 }}>
                {t('upload.ai_subtitle_gen')}
              </Text>
            </div>
          )}
        </div>
      )}

      {uploading && (
        <div style={{ 
          marginBottom: '16px',
          padding: '20px',
          background: 'rgba(38, 38, 38, 0.8)',
          borderRadius: '16px',
          border: '1px solid rgba(79, 172, 254, 0.3)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ marginBottom: '12px' }}>
            <Text style={{ color: '#ffffff', fontWeight: 600, fontSize: '14px' }}>{t('upload.import_progress')}</Text>
            <Text style={{ color: '#4facfe', float: 'right', fontWeight: 600, fontSize: '14px' }}>
              {uploadProgress}%
            </Text>
          </div>
          <Progress 
            percent={uploadProgress} 
            status="active"
            strokeColor={{
              '0%': '#4facfe',
              '100%': '#00f2fe',
            }}
            trailColor="#404040"
            strokeWidth={6}
            showInfo={false}
            style={{ marginBottom: '8px' }}
          />
          <Text style={{ color: '#cccccc', fontSize: '13px', marginTop: '8px', display: 'block', textAlign: 'center' }}>
            {t('upload.importing_hint')}
          </Text>
        </div>
      )}

      {files.video && (
        <div style={{ textAlign: 'center', marginTop: '8px' }}>
          <Button 
            type="primary" 
            size="large"
            loading={uploading}
            disabled={!files.video || !projectName.trim()}
            onClick={handleUpload}
            style={{
              height: '48px',
              padding: '0 32px',
              borderRadius: '24px',
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              border: 'none',
              fontSize: '16px',
              fontWeight: 600,
              boxShadow: '0 4px 20px rgba(79, 172, 254, 0.4)',
              transition: 'all 0.3s ease'
            }}
          >
            {uploading ? t('upload.importing_button') : t('upload.start_button')}
          </Button>
        </div>
      )}
    </div>
  )
}

export default FileUpload