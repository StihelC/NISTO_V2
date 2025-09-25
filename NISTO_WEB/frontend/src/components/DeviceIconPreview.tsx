import React, { useState } from 'react'
import DeviceIcon from './DeviceIcon'
import { DEVICE_CATEGORIES, DEVICE_LABELS } from '../constants/deviceTypes'
import type { DeviceType } from '../store/types'

interface DeviceIconPreviewProps {
  onClose?: () => void
  onSelectDeviceType?: (deviceType: DeviceType) => void
  mode?: 'gallery' | 'selector'
  selectedDeviceType?: DeviceType
}

const DeviceIconPreview: React.FC<DeviceIconPreviewProps> = ({ 
  onClose, 
  onSelectDeviceType, 
  mode = 'gallery',
  selectedDeviceType 
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // Filter device types based on search and category
  const filteredCategories = Object.entries(DEVICE_CATEGORIES).reduce((acc, [category, deviceTypes]) => {
    if (selectedCategory !== 'all' && selectedCategory !== category) {
      return acc
    }

    const filteredDeviceTypes = deviceTypes.filter(deviceType => {
      const label = DEVICE_LABELS[deviceType].toLowerCase()
      const type = deviceType.toLowerCase()
      const search = searchTerm.toLowerCase()
      return label.includes(search) || type.includes(search) || category.toLowerCase().includes(search)
    })

    if (filteredDeviceTypes.length > 0) {
      acc[category] = filteredDeviceTypes
    }
    return acc
  }, {} as Record<string, DeviceType[]>)

  const allCategories = Object.keys(DEVICE_CATEGORIES)

  const handleDeviceTypeClick = (deviceType: DeviceType) => {
    if (mode === 'selector' && onSelectDeviceType) {
      onSelectDeviceType(deviceType)
      onClose?.()
    }
  }

  return (
    <div className="device-icon-preview-overlay">
      <div className="device-icon-preview-modal">
        <div className="device-icon-preview-header">
          <h2>
            {mode === 'selector' ? '🎯 Select Device Type' : '🎨 Device Icon Preview Gallery'}
          </h2>
          <button type="button" className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="device-icon-preview-controls">
          <div className="search-controls">
            <input
              type="text"
              placeholder="Search device types..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="category-filter"
            >
              <option value="all">All Categories</option>
              {allCategories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
          
          <div className="preview-stats">
            {Object.values(filteredCategories).reduce((sum, types) => sum + types.length, 0)} device types
          </div>
        </div>

        <div className="device-icon-preview-content">
          {Object.entries(filteredCategories).map(([category, deviceTypes]) => (
            <div key={category} className="category-section">
              <h3 className="category-title">{category}</h3>
              <div className="device-grid">
                {deviceTypes.map(deviceType => {
                  const isSelected = selectedDeviceType === deviceType
                  return (
                    <div 
                      key={deviceType} 
                      className={`device-preview-item ${mode === 'selector' ? 'selectable' : ''} ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleDeviceTypeClick(deviceType)}
                    >
                      <div className="device-icon-display">
                        <DeviceIcon deviceType={deviceType} size={32} />
                      </div>
                      <div className="device-info">
                        <div className="device-label">{DEVICE_LABELS[deviceType]}</div>
                        <div className="device-type">{deviceType}</div>
                      </div>
                      {mode === 'selector' && (
                        <div className="selection-indicator">
                          {isSelected ? '✓' : ''}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
          
          {Object.keys(filteredCategories).length === 0 && (
            <div className="no-results">
              <p>No device types found matching "{searchTerm}"</p>
              <p>Try a different search term or category filter.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DeviceIconPreview
