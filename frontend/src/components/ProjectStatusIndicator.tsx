import { Badge, Tooltip } from 'antd'
import { useTranslation } from 'react-i18next'
import { Project } from '../store/useProjectStore'
import { 
  getProjectStatusConfig, 
  normalizeProjectStatus 
} from '../utils/statusUtils'

interface ProjectStatusIndicatorProps {
  project: Project
  showProgress?: boolean
  size?: 'small' | 'default' | 'large'
}

const ProjectStatusIndicator: React.FC<ProjectStatusIndicatorProps> = ({
  project,
  size = 'default'
}) => {
  const { t } = useTranslation()
  // 暂时使用简单的状态处理
  const normalizedStatus = normalizeProjectStatus(project.status)
  const config = getProjectStatusConfig(normalizedStatus)

  const getStepName = () => {
    if (normalizedStatus === 'processing' && project.current_step) {
      const stepNames = {
        1: t('status.step1'),
        2: t('status.step2'),
        3: t('status.step3'),
        4: t('status.step4'),
        5: t('status.step5'),
        6: t('status.step6')
      }
      return stepNames[project.current_step as keyof typeof stepNames] || t('status.processing')
    }
    return config.text
  }

  if (size === 'small') {
    return (
      <Tooltip title={getStepName()}>
        <Badge status={config.badgeStatus} text={config.text} />
      </Tooltip>
    )
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      padding: '4px 8px',
      borderRadius: '4px',
      backgroundColor: `${config.color}15`,
      border: `1px solid ${config.color}30`,
      color: config.color,
      fontSize: '12px',
      fontWeight: 500,
      minHeight: '24px'
    }}>
      <span style={{ marginRight: '4px', display: 'flex', alignItems: 'center' }}>
        <config.icon />
      </span>
      <span>{config.text}</span>
    </div>
  )
}

export default ProjectStatusIndicator