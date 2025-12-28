import React, { useState, useEffect } from 'react';
import { Progress, Card, Typography, Tag, Space, Button, message } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTaskProgress, TaskProgressState } from '../hooks/useTaskProgress';
import { useTranslation } from 'react-i18next';

const { Text, Title } = Typography;

interface TaskProgressDisplayProps {
  userId: string;
  taskId: string;
  onTaskComplete?: (state: TaskProgressState) => void;
  onTaskFailed?: (state: TaskProgressState) => void;
}

export const TaskProgressDisplay: React.FC<TaskProgressDisplayProps> = ({
  userId,
  taskId,
  onTaskComplete,
  onTaskFailed
}) => {
  const { t, i18n } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);
  
  const {
    taskState,
    isConnected,
    isSubscribed,
    performFinalStateCheck
  } = useTaskProgress({
    userId,
    taskId,
    onProgressUpdate: (state) => {
      console.log('任务进度更新:', state);
    },
    onTaskComplete: (state) => {
      console.log('任务完成:', state);
      message.success(t('tasks.task_complete'));
      onTaskComplete?.(state);
    },
    onTaskFailed: (state) => {
      console.log('任务失败:', state);
      message.error(`${t('tasks.task_failed_prefix')}: ${state.message}`);
      onTaskFailed?.(state);
    }
  });

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'transcribe': return 'blue';
      case 'analyze': return 'green';
      case 'clip': return 'orange';
      case 'encode': return 'purple';
      case 'upload': return 'red';
      default: return 'default';
    }
  };

  const getPhaseText = (phase: string) => {
    switch (phase) {
      case 'transcribe': return t('tasks.phase_transcribe');
      case 'analyze': return t('tasks.phase_analyze');
      case 'clip': return t('tasks.phase_clip');
      case 'encode': return t('tasks.phase_encode');
      case 'upload': return t('tasks.phase_upload');
      default: return phase;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING': return 'default';
      case 'PROGRESS': return 'processing';
      case 'DONE': return 'success';
      case 'FAIL': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'PENDING': return t('tasks.status_pending');
      case 'PROGRESS': return t('tasks.status_progress');
      case 'DONE': return t('tasks.status_done');
      case 'FAIL': return t('tasks.status_fail');
      default: return status;
    }
  };

  if (!taskState) {
    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Text type="secondary">{t('tasks.modal_title')} {taskId}</Text>
          <Tag color={isConnected ? 'success' : 'error'}>
            {isConnected ? t('tasks.connected') : t('tasks.disconnected')}
          </Tag>
          <Tag color={isSubscribed ? 'success' : 'default'}>
            {isSubscribed ? t('tasks.subscribed') : t('tasks.unsubscribed')}
          </Tag>
        </Space>
      </Card>
    );
  }

  return (
    <Card 
      size="small" 
      style={{ marginBottom: 16 }}
      title={
        <Space>
          <Text strong>{t('tasks.column_progress')}</Text>
          <Tag color={getStatusColor(taskState.status)}>
            {getStatusText(taskState.status)}
          </Tag>
          <Tag color={getPhaseColor(taskState.phase)}>
            {getPhaseText(taskState.phase)}
          </Tag>
        </Space>
      }
      extra={
        <Space>
          <Button 
            size="small" 
            icon={<ReloadOutlined />}
            onClick={performFinalStateCheck}
            title={t('tasks.final_check')}
          />
          <Button 
            size="small" 
            type="text"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? t('tasks.collapse') : t('tasks.expand')}
          </Button>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 进度条 */}
        <div>
          <Progress 
            percent={taskState.progress}
            status={taskState.status === 'FAIL' ? 'exception' : 
                   taskState.status === 'DONE' ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {taskState.step}/{taskState.total} {t('tasks.steps_unit')}
          </Text>
        </div>

        {/* 当前消息 */}
        <Text>{taskState.message}</Text>

        {/* 展开的详细信息 */}
        {isExpanded && (
          <div style={{ 
            padding: '12px', 
            backgroundColor: '#f5f5f5', 
            borderRadius: '6px',
            fontSize: '12px'
          }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div>
                <Text strong>{t('tasks.task_id')}:</Text> {taskState.task_id}
              </div>
              <div>
                <Text strong>序列号:</Text> {taskState.seq}
              </div>
              <div>
                <Text strong>{t('tasks.column_created')}:</Text> {new Date(taskState.ts * 1000).toLocaleString(i18n.language === 'zh' ? 'zh-CN' : i18n.language === 'pt' ? 'pt-BR' : 'en-US')}
              </div>
              <div>
                <Text strong>{t('home.link_import')}:</Text> {new Date(taskState.last_updated).toLocaleString(i18n.language === 'zh' ? 'zh-CN' : i18n.language === 'pt' ? 'pt-BR' : 'en-US')}
              </div>
              {taskState.meta && (
                <div>
                  <Text strong>{t('tasks.meta')}:</Text> {JSON.stringify(taskState.meta, null, 2)}
                </div>
              )}
              <div>
                <Text strong>{t('tasks.column_status')}:</Text> 
                <Tag color={isConnected ? 'success' : 'error'} style={{ marginLeft: 8 }}>
                  {isConnected ? t('tasks.connected') : t('tasks.disconnected')}
                </Tag>
                <Tag color={isSubscribed ? 'success' : 'default'} style={{ marginLeft: 4 }}>
                  {isSubscribed ? t('tasks.subscribed') : t('tasks.unsubscribed')}
                </Tag>
              </div>
            </Space>
          </div>
        )}
      </Space>
    </Card>
  );
};

