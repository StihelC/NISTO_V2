export interface ConnectionTypeOption {
  value: string
  label: string
}

export const CONNECTION_TYPE_OPTIONS: ConnectionTypeOption[] = [
  { value: 'ethernet', label: 'Ethernet' },
  { value: 'fiber', label: 'Fiber Optic' },
  { value: 'wireless', label: 'Wireless' },
  { value: 'vpn', label: 'VPN' },
  { value: 'serial', label: 'Serial' },
  { value: 'usb', label: 'USB' },
  { value: 'coax', label: 'Coaxial' },
  { value: 'bluetooth', label: 'Bluetooth' },
  { value: 'infrared', label: 'Infrared' },
  { value: 'orthogonal', label: 'Orthogonal' },
  { value: 'custom', label: 'Custom' },
]

export const CONNECTION_TYPE_VALUES = CONNECTION_TYPE_OPTIONS.map((option) => option.value)

