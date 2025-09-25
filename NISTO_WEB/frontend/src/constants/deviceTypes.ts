import type { DeviceType } from '../store/types'

// Organized device types by category for better UX
export const DEVICE_CATEGORIES = {
  'Network Infrastructure': [
    'switch', 'router', 'firewall', 'load-balancer', 'proxy', 'gateway', 
    'modem', 'access-point', 'wireless-controller'
  ],
  'Security Devices': [
    'ids-ips', 'waf', 'vpn-concentrator', 'security-appliance', 'utm', 'dlp', 'siem'
  ],
  'Servers & Compute': [
    'server', 'web-server', 'database-server', 'file-server', 'mail-server', 
    'dns-server', 'dhcp-server', 'domain-controller', 'hypervisor', 'vm', 
    'container', 'kubernetes-node', 'docker-host'
  ],
  'Storage Systems': [
    'nas', 'san', 'storage-array', 'backup-server', 'tape-library'
  ],
  'Endpoints': [
    'workstation', 'laptop', 'desktop', 'thin-client', 'tablet', 
    'smartphone', 'pos-terminal', 'kiosk'
  ],
  'IoT & Embedded': [
    'iot-device', 'sensor', 'camera', 'ip-phone', 'printer', 
    'scanner', 'badge-reader', 'smart-tv'
  ],
  'AWS Services': [
    'aws-ec2', 'aws-rds', 'aws-s3', 'aws-lambda', 'aws-ecs', 'aws-eks', 
    'aws-elb', 'aws-cloudfront', 'aws-api-gateway', 'aws-vpc', 'aws-route53', 
    'aws-iam', 'aws-cloudwatch', 'aws-sqs', 'aws-sns', 'aws-dynamodb'
  ],
  'Azure Services': [
    'azure-vm', 'azure-sql', 'azure-storage', 'azure-functions', 'azure-aks', 
    'azure-app-service', 'azure-load-balancer', 'azure-cdn', 'azure-api-management', 
    'azure-vnet', 'azure-dns', 'azure-ad', 'azure-monitor', 'azure-service-bus'
  ],
  'GCP Services': [
    'gcp-compute', 'gcp-cloud-sql', 'gcp-storage', 'gcp-functions', 'gcp-gke', 
    'gcp-app-engine', 'gcp-load-balancer'
  ],
  'Operating Systems': [
    'windows-server', 'linux-server', 'ubuntu-server', 'centos-server', 
    'redhat-server', 'debian-server', 'windows-10', 'windows-11', 'macos', 
    'ubuntu-desktop', 'android', 'ios'
  ],
  'Monitoring & Management': [
    'monitoring-server', 'log-server', 'nms', 'orchestrator', 'automation-server'
  ],
  'Legacy Systems': [
    'mainframe', 'as400', 'legacy-system'
  ],
  'Other': [
    'generic', 'unknown'
  ]
} as const

// Flatten all device types for backwards compatibility
export const DEVICE_TYPES: DeviceType[] = Object.values(DEVICE_CATEGORIES).flat() as DeviceType[]

// Human-readable labels for device types
export const DEVICE_LABELS: Record<DeviceType, string> = {
  // Network Infrastructure
  'switch': 'Network Switch',
  'router': 'Router',
  'firewall': 'Firewall',
  'load-balancer': 'Load Balancer',
  'proxy': 'Proxy Server',
  'gateway': 'Gateway',
  'modem': 'Modem',
  'access-point': 'Wireless Access Point',
  'wireless-controller': 'Wireless Controller',
  
  // Security Devices
  'ids-ips': 'IDS/IPS',
  'waf': 'Web Application Firewall',
  'vpn-concentrator': 'VPN Concentrator',
  'security-appliance': 'Security Appliance',
  'utm': 'Unified Threat Management',
  'dlp': 'Data Loss Prevention',
  'siem': 'SIEM',
  
  // Servers & Compute
  'server': 'Server',
  'web-server': 'Web Server',
  'database-server': 'Database Server',
  'file-server': 'File Server',
  'mail-server': 'Mail Server',
  'dns-server': 'DNS Server',
  'dhcp-server': 'DHCP Server',
  'domain-controller': 'Domain Controller',
  'hypervisor': 'Hypervisor',
  'vm': 'Virtual Machine',
  'container': 'Container',
  'kubernetes-node': 'Kubernetes Node',
  'docker-host': 'Docker Host',
  
  // Storage
  'nas': 'Network Attached Storage',
  'san': 'Storage Area Network',
  'storage-array': 'Storage Array',
  'backup-server': 'Backup Server',
  'tape-library': 'Tape Library',
  
  // Endpoints
  'workstation': 'Workstation',
  'laptop': 'Laptop',
  'desktop': 'Desktop Computer',
  'thin-client': 'Thin Client',
  'tablet': 'Tablet',
  'smartphone': 'Smartphone',
  'pos-terminal': 'POS Terminal',
  'kiosk': 'Kiosk',
  
  // IoT & Embedded
  'iot-device': 'IoT Device',
  'sensor': 'Sensor',
  'camera': 'IP Camera',
  'ip-phone': 'IP Phone',
  'printer': 'Network Printer',
  'scanner': 'Network Scanner',
  'badge-reader': 'Badge Reader',
  'smart-tv': 'Smart TV',
  
  // AWS Services
  'aws-ec2': 'AWS EC2',
  'aws-rds': 'AWS RDS',
  'aws-s3': 'AWS S3',
  'aws-lambda': 'AWS Lambda',
  'aws-ecs': 'AWS ECS',
  'aws-eks': 'AWS EKS',
  'aws-elb': 'AWS Load Balancer',
  'aws-cloudfront': 'AWS CloudFront',
  'aws-api-gateway': 'AWS API Gateway',
  'aws-vpc': 'AWS VPC',
  'aws-route53': 'AWS Route 53',
  'aws-iam': 'AWS IAM',
  'aws-cloudwatch': 'AWS CloudWatch',
  'aws-sqs': 'AWS SQS',
  'aws-sns': 'AWS SNS',
  'aws-dynamodb': 'AWS DynamoDB',
  
  // Azure Services
  'azure-vm': 'Azure Virtual Machine',
  'azure-sql': 'Azure SQL',
  'azure-storage': 'Azure Storage',
  'azure-functions': 'Azure Functions',
  'azure-aks': 'Azure AKS',
  'azure-app-service': 'Azure App Service',
  'azure-load-balancer': 'Azure Load Balancer',
  'azure-cdn': 'Azure CDN',
  'azure-api-management': 'Azure API Management',
  'azure-vnet': 'Azure Virtual Network',
  'azure-dns': 'Azure DNS',
  'azure-ad': 'Azure Active Directory',
  'azure-monitor': 'Azure Monitor',
  'azure-service-bus': 'Azure Service Bus',
  
  // GCP Services
  'gcp-compute': 'Google Compute Engine',
  'gcp-cloud-sql': 'Google Cloud SQL',
  'gcp-storage': 'Google Cloud Storage',
  'gcp-functions': 'Google Cloud Functions',
  'gcp-gke': 'Google GKE',
  'gcp-app-engine': 'Google App Engine',
  'gcp-load-balancer': 'Google Load Balancer',
  
  // Operating Systems
  'windows-server': 'Windows Server',
  'linux-server': 'Linux Server',
  'ubuntu-server': 'Ubuntu Server',
  'centos-server': 'CentOS Server',
  'redhat-server': 'Red Hat Server',
  'debian-server': 'Debian Server',
  'windows-10': 'Windows 10',
  'windows-11': 'Windows 11',
  'macos': 'macOS',
  'ubuntu-desktop': 'Ubuntu Desktop',
  'android': 'Android',
  'ios': 'iOS',
  
  // Monitoring & Management
  'monitoring-server': 'Monitoring Server',
  'log-server': 'Log Server',
  'nms': 'Network Management System',
  'orchestrator': 'Orchestrator',
  'automation-server': 'Automation Server',
  
  // Legacy
  'mainframe': 'Mainframe',
  'as400': 'AS/400',
  'legacy-system': 'Legacy System',
  
  // Generic
  'generic': 'Generic Device',
  'unknown': 'Unknown Device'
}

// Device type icons (emoji for now, can be replaced with actual icons later)
export const DEVICE_ICONS: Record<DeviceType, string> = {
  // Network Infrastructure
  'switch': '🔌',
  'router': '📡',
  'firewall': '🛡️',
  'load-balancer': '⚖️',
  'proxy': '🔄',
  'gateway': '🚪',
  'modem': '📶',
  'access-point': '📶',
  'wireless-controller': '📡',
  
  // Security Devices
  'ids-ips': '🛡️',
  'waf': '🛡️',
  'vpn-concentrator': '🔒',
  'security-appliance': '🛡️',
  'utm': '🛡️',
  'dlp': '🔒',
  'siem': '👁️',
  
  // Servers & Compute
  'server': '🖥️',
  'web-server': '🌐',
  'database-server': '🗄️',
  'file-server': '📁',
  'mail-server': '📧',
  'dns-server': '🌐',
  'dhcp-server': '📡',
  'domain-controller': '🏢',
  'hypervisor': '🖥️',
  'vm': '💻',
  'container': '📦',
  'kubernetes-node': '☸️',
  'docker-host': '🐳',
  
  // Storage
  'nas': '💾',
  'san': '💾',
  'storage-array': '💾',
  'backup-server': '💿',
  'tape-library': '📼',
  
  // Endpoints
  'workstation': '🖥️',
  'laptop': '💻',
  'desktop': '🖥️',
  'thin-client': '💻',
  'tablet': '📱',
  'smartphone': '📱',
  'pos-terminal': '💳',
  'kiosk': '🏪',
  
  // IoT & Embedded
  'iot-device': '🌐',
  'sensor': '📡',
  'camera': '📹',
  'ip-phone': '☎️',
  'printer': '🖨️',
  'scanner': '📄',
  'badge-reader': '🏷️',
  'smart-tv': '📺',
  
  // AWS Services
  'aws-ec2': '☁️',
  'aws-rds': '🗄️',
  'aws-s3': '🪣',
  'aws-lambda': '⚡',
  'aws-ecs': '📦',
  'aws-eks': '☸️',
  'aws-elb': '⚖️',
  'aws-cloudfront': '🌐',
  'aws-api-gateway': '🚪',
  'aws-vpc': '🏢',
  'aws-route53': '🌐',
  'aws-iam': '👤',
  'aws-cloudwatch': '👁️',
  'aws-sqs': '📬',
  'aws-sns': '📢',
  'aws-dynamodb': '🗄️',
  
  // Azure Services
  'azure-vm': '☁️',
  'azure-sql': '🗄️',
  'azure-storage': '💾',
  'azure-functions': '⚡',
  'azure-aks': '☸️',
  'azure-app-service': '🌐',
  'azure-load-balancer': '⚖️',
  'azure-cdn': '🌐',
  'azure-api-management': '🚪',
  'azure-vnet': '🏢',
  'azure-dns': '🌐',
  'azure-ad': '👤',
  'azure-monitor': '👁️',
  'azure-service-bus': '🚌',
  
  // GCP Services
  'gcp-compute': '☁️',
  'gcp-cloud-sql': '🗄️',
  'gcp-storage': '💾',
  'gcp-functions': '⚡',
  'gcp-gke': '☸️',
  'gcp-app-engine': '🌐',
  'gcp-load-balancer': '⚖️',
  
  // Operating Systems
  'windows-server': '🪟',
  'linux-server': '🐧',
  'ubuntu-server': '🐧',
  'centos-server': '🐧',
  'redhat-server': '🎩',
  'debian-server': '🐧',
  'windows-10': '🪟',
  'windows-11': '🪟',
  'macos': '🍎',
  'ubuntu-desktop': '🐧',
  'android': '🤖',
  'ios': '📱',
  
  // Monitoring & Management
  'monitoring-server': '👁️',
  'log-server': '📋',
  'nms': '🔧',
  'orchestrator': '🎼',
  'automation-server': '🤖',
  
  // Legacy
  'mainframe': '🏭',
  'as400': '🏭',
  'legacy-system': '🕰️',
  
  // Generic
  'generic': '📱',
  'unknown': '❓'
}
