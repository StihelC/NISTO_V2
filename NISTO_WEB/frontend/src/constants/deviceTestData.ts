import type { DeviceType } from '../store/types'

// Sample test devices for each category to verify functionality
export const DEVICE_TEST_SAMPLES: Array<{ name: string; type: DeviceType; description: string }> = [
  // Network Infrastructure
  { name: 'Core Switch 01', type: 'switch', description: 'Main distribution switch' },
  { name: 'Border Router', type: 'router', description: 'Internet gateway router' },
  { name: 'Perimeter Firewall', type: 'firewall', description: 'Network security firewall' },
  { name: 'Web Load Balancer', type: 'load-balancer', description: 'HTTP/HTTPS load balancer' },
  
  // Security Devices
  { name: 'Intrusion Detection', type: 'ids-ips', description: 'Network monitoring IDS/IPS' },
  { name: 'Web App Firewall', type: 'waf', description: 'Application layer protection' },
  { name: 'Site-to-Site VPN', type: 'vpn-concentrator', description: 'VPN endpoint' },
  
  // Servers & Compute
  { name: 'Web Server 01', type: 'web-server', description: 'Apache/Nginx web server' },
  { name: 'Database Primary', type: 'database-server', description: 'MySQL/PostgreSQL database' },
  { name: 'File Share Server', type: 'file-server', description: 'Network file storage' },
  { name: 'Exchange Server', type: 'mail-server', description: 'Email server' },
  { name: 'Active Directory', type: 'domain-controller', description: 'Windows domain controller' },
  { name: 'VMware Host', type: 'hypervisor', description: 'Virtualization host' },
  { name: 'Linux VM', type: 'vm', description: 'Ubuntu virtual machine' },
  { name: 'App Container', type: 'container', description: 'Docker container' },
  
  // Storage
  { name: 'Synology NAS', type: 'nas', description: 'Network attached storage' },
  { name: 'EMC Storage Array', type: 'storage-array', description: 'Enterprise storage' },
  { name: 'Backup Server', type: 'backup-server', description: 'Veeam backup server' },
  
  // Endpoints
  { name: 'Admin Workstation', type: 'workstation', description: 'IT administrator PC' },
  { name: 'Manager Laptop', type: 'laptop', description: 'Mobile work device' },
  { name: 'Reception Desk', type: 'desktop', description: 'Front desk computer' },
  { name: 'Kiosk Terminal', type: 'kiosk', description: 'Public access terminal' },
  
  // IoT & Embedded
  { name: 'Security Camera 01', type: 'camera', description: 'IP surveillance camera' },
  { name: 'VoIP Phone', type: 'ip-phone', description: 'Cisco IP phone' },
  { name: 'Network Printer', type: 'printer', description: 'HP LaserJet printer' },
  { name: 'Badge Reader', type: 'badge-reader', description: 'Access control reader' },
  
  // AWS Services
  { name: 'Web Tier EC2', type: 'aws-ec2', description: 'Application server instance' },
  { name: 'User Database', type: 'aws-rds', description: 'Managed MySQL database' },
  { name: 'Media Storage', type: 'aws-s3', description: 'Object storage bucket' },
  { name: 'Image Processor', type: 'aws-lambda', description: 'Serverless function' },
  { name: 'App Load Balancer', type: 'aws-elb', description: 'Application load balancer' },
  { name: 'CDN Distribution', type: 'aws-cloudfront', description: 'Content delivery network' },
  
  // Azure Services
  { name: 'App Service VM', type: 'azure-vm', description: 'Windows Server VM' },
  { name: 'SQL Database', type: 'azure-sql', description: 'Managed SQL database' },
  { name: 'Blob Storage', type: 'azure-storage', description: 'Object storage account' },
  { name: 'Function App', type: 'azure-functions', description: 'Serverless compute' },
  { name: 'AKS Cluster', type: 'azure-aks', description: 'Kubernetes cluster' },
  
  // GCP Services
  { name: 'Compute Instance', type: 'gcp-compute', description: 'Google VM instance' },
  { name: 'Cloud SQL DB', type: 'gcp-cloud-sql', description: 'Managed database' },
  { name: 'Cloud Storage', type: 'gcp-storage', description: 'Object storage bucket' },
  { name: 'Cloud Functions', type: 'gcp-functions', description: 'Serverless functions' },
  
  // Operating Systems
  { name: 'Windows Server 2022', type: 'windows-server', description: 'Windows Server host' },
  { name: 'Ubuntu 22.04 LTS', type: 'ubuntu-server', description: 'Linux server host' },
  { name: 'Red Hat Enterprise', type: 'redhat-server', description: 'RHEL server' },
  { name: 'Windows 11 Pro', type: 'windows-11', description: 'Client workstation OS' },
  { name: 'macOS Ventura', type: 'macos', description: 'Apple desktop OS' },
  
  // Monitoring & Management
  { name: 'Nagios Monitor', type: 'monitoring-server', description: 'Infrastructure monitoring' },
  { name: 'Splunk Logger', type: 'log-server', description: 'Log aggregation server' },
  { name: 'PRTG NMS', type: 'nms', description: 'Network management system' },
  { name: 'Ansible Tower', type: 'automation-server', description: 'Configuration automation' },
  
  // Legacy Systems
  { name: 'IBM Mainframe', type: 'mainframe', description: 'Legacy mainframe system' },
  { name: 'AS/400 System', type: 'as400', description: 'IBM iSeries system' },
  { name: 'Legacy ERP', type: 'legacy-system', description: 'Old enterprise system' }
]

// Quick test function to create sample devices
export const createSampleDevices = () => {
  // Return a subset of samples for testing
  return DEVICE_TEST_SAMPLES.slice(0, 10).map((sample, index) => ({
    id: `test-${index + 1}`,
    name: sample.name,
    type: sample.type,
    config: {
      description: sample.description,
      riskLevel: 'Moderate',
      complianceStatus: 'Not Assessed'
    },
    position: {
      x: 100 + (index % 5) * 150,
      y: 100 + Math.floor(index / 5) * 150
    }
  }))
}
