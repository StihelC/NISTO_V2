import React from 'react'
import type { DeviceType } from '../store/types'
import {
  Server,
  Router,
  Shield,
  Activity,
  Monitor,
  Smartphone,
  Printer,
  Camera,
  Wifi,
  Cloud,
  Database,
  Globe,
  Lock,
  Cpu,
  HardDrive,
  Terminal,
  Network,
  Phone,
  Tv,
  // Headphones,
  CircuitBoard,
  Zap,
  Container,
  Layers,
  Settings,
  Eye,
  FileText,
  BarChart3,
  Cog,
  Building
} from 'lucide-react'

interface DeviceIconProps {
  deviceType: DeviceType
  size?: number
  className?: string
  color?: string
}

// Professional icon mapping using Lucide React
const getDeviceIcon = (deviceType: DeviceType) => {
  switch (deviceType) {
    // Network Infrastructure
    case 'switch':
      return CircuitBoard
    case 'router':
      return Router
    case 'firewall':
      return Shield
    case 'load-balancer':
      return Activity
    case 'proxy':
      return Globe
    case 'gateway':
      return Router
    case 'modem':
      return Wifi
    case 'access-point':
      return Wifi
    case 'wireless-controller':
      return Network
    
    // Security Devices
    case 'ids-ips':
      return Eye
    case 'waf':
      return Shield
    case 'vpn-concentrator':
      return Lock
    case 'security-appliance':
      return Shield
    case 'utm':
      return Shield
    case 'dlp':
      return Lock
    case 'siem':
      return Eye
    
    // Servers & Compute
    case 'server':
      return Server
    case 'web-server':
      return Globe
    case 'database-server':
      return Database
    case 'file-server':
      return HardDrive
    case 'mail-server':
      return Server
    case 'dns-server':
      return Globe
    case 'dhcp-server':
      return Network
    case 'domain-controller':
      return Building
    case 'hypervisor':
      return Layers
    case 'vm':
      return Monitor
    case 'container':
      return Container
    case 'kubernetes-node':
      return Cpu
    case 'docker-host':
      return Container
    
    // Storage Systems
    case 'nas':
      return HardDrive
    case 'san':
      return HardDrive
    case 'storage-array':
      return Database
    case 'backup-server':
      return HardDrive
    case 'tape-library':
      return HardDrive
    
    // Endpoints
    case 'workstation':
      return Monitor
    case 'laptop':
      return Monitor
    case 'desktop':
      return Monitor
    case 'thin-client':
      return Monitor
    case 'tablet':
      return Smartphone
    case 'smartphone':
      return Smartphone
    case 'pos-terminal':
      return Terminal
    case 'kiosk':
      return Monitor
    
    // IoT & Embedded
    case 'iot-device':
      return Cpu
    case 'sensor':
      return Activity
    case 'camera':
      return Camera
    case 'ip-phone':
      return Phone
    case 'printer':
      return Printer
    case 'scanner':
      return Printer
    case 'badge-reader':
      return Lock
    case 'smart-tv':
      return Tv
    
    // AWS Services
    case 'aws-ec2':
    case 'aws-ecs':
    case 'aws-eks':
      return Cloud
    case 'aws-rds':
    case 'aws-dynamodb':
      return Database
    case 'aws-s3':
      return HardDrive
    case 'aws-lambda':
      return Zap
    case 'aws-elb':
      return Activity
    case 'aws-cloudfront':
    case 'aws-api-gateway':
    case 'aws-route53':
      return Globe
    case 'aws-vpc':
      return Network
    case 'aws-iam':
      return Lock
    case 'aws-cloudwatch':
      return BarChart3
    case 'aws-sqs':
    case 'aws-sns':
      return Settings
    
    // Azure Services
    case 'azure-vm':
    case 'azure-aks':
    case 'azure-functions':
      return Cloud
    case 'azure-sql':
      return Database
    case 'azure-storage':
      return HardDrive
    case 'azure-app-service':
    case 'azure-cdn':
    case 'azure-api-management':
    case 'azure-dns':
      return Globe
    case 'azure-load-balancer':
      return Activity
    case 'azure-vnet':
      return Network
    case 'azure-ad':
      return Lock
    case 'azure-monitor':
      return BarChart3
    case 'azure-service-bus':
      return Settings
    
    // GCP Services
    case 'gcp-compute':
    case 'gcp-gke':
    case 'gcp-functions':
      return Cloud
    case 'gcp-cloud-sql':
      return Database
    case 'gcp-storage':
      return HardDrive
    case 'gcp-app-engine':
    case 'gcp-load-balancer':
      return Globe
    
    // Operating Systems
    case 'windows-server':
    case 'linux-server':
    case 'ubuntu-server':
    case 'centos-server':
    case 'redhat-server':
    case 'debian-server':
      return Server
    case 'windows-10':
    case 'windows-11':
    case 'macos':
    case 'ubuntu-desktop':
      return Monitor
    case 'android':
    case 'ios':
      return Smartphone
    
    // Monitoring & Management
    case 'monitoring-server':
      return BarChart3
    case 'log-server':
      return FileText
    case 'nms':
      return Settings
    case 'orchestrator':
      return Cog
    case 'automation-server':
      return Settings
    
    // Legacy Systems
    case 'mainframe':
    case 'as400':
    case 'legacy-system':
      return Building
    
    // Generic/Unknown
    case 'generic':
    case 'unknown':
    default:
      return Server
  }
}

// Color mapping for different device categories
const getDeviceColor = (deviceType: DeviceType): string => {
  // Network Infrastructure
  if (['switch', 'router', 'firewall', 'load-balancer', 'proxy', 'gateway', 'modem', 'access-point', 'wireless-controller'].includes(deviceType)) {
    return '#2563eb' // Blue
  }
  
  // Security Devices
  if (['ids-ips', 'waf', 'vpn-concentrator', 'security-appliance', 'utm', 'dlp', 'siem'].includes(deviceType)) {
    return '#dc2626' // Red
  }
  
  // Servers & Compute
  if (['server', 'web-server', 'database-server', 'file-server', 'mail-server', 'dns-server', 'dhcp-server', 'domain-controller', 'hypervisor', 'vm', 'container', 'kubernetes-node', 'docker-host'].includes(deviceType)) {
    return '#059669' // Green
  }
  
  // Storage Systems
  if (['nas', 'san', 'storage-array', 'backup-server', 'tape-library'].includes(deviceType)) {
    return '#0891b2' // Cyan
  }
  
  // Cloud Services (AWS, Azure, GCP)
  if (deviceType.startsWith('aws-') || deviceType.startsWith('azure-') || deviceType.startsWith('gcp-')) {
    return '#7c3aed' // Purple
  }
  
  // Endpoints
  if (['workstation', 'laptop', 'desktop', 'thin-client', 'tablet', 'smartphone', 'pos-terminal', 'kiosk'].includes(deviceType)) {
    return '#ea580c' // Orange
  }
  
  // IoT & Embedded
  if (['iot-device', 'sensor', 'camera', 'ip-phone', 'printer', 'scanner', 'badge-reader', 'smart-tv'].includes(deviceType)) {
    return '#65a30d' // Lime
  }
  
  // Operating Systems
  if (deviceType.includes('server') || deviceType.includes('windows') || deviceType.includes('linux') || deviceType.includes('ubuntu') || deviceType.includes('centos') || deviceType.includes('redhat') || deviceType.includes('debian') || deviceType.includes('macos') || deviceType.includes('android') || deviceType.includes('ios')) {
    return '#7c2d12' // Brown
  }
  
  // Monitoring & Management
  if (['monitoring-server', 'log-server', 'nms', 'orchestrator', 'automation-server'].includes(deviceType)) {
    return '#1d4ed8' // Indigo
  }
  
  // Legacy Systems
  if (['mainframe', 'as400', 'legacy-system'].includes(deviceType)) {
    return '#6b7280' // Gray
  }
  
  // Default
  return '#6b7280' // Gray
}

const DeviceIcon: React.FC<DeviceIconProps> = ({ 
  deviceType, 
  size = 20, 
  className = '', 
  color 
}) => {
  const IconComponent = getDeviceIcon(deviceType)
  const iconColor = color || getDeviceColor(deviceType)
  
  return (
    <IconComponent 
      size={size}
      color={iconColor}
      className={`device-icon ${className}`}
      style={{ minWidth: size, minHeight: size }}
    />
  )
}

export default DeviceIcon
