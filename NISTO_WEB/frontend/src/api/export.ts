import { apiClient } from './axios'

export interface ExportApiError {
  detail: string
}

/**
 * Download topology data as CSV file
 */
export const downloadTopologyCSV = async (): Promise<void> => {
  try {
    const response = await apiClient.get('/export/csv', {
      responseType: 'blob'
    })
    
    // Create blob link to download
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // Get filename from response headers or use default
    const disposition = response.headers['content-disposition']
    let filename = 'topology_export.csv'
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/"/g, '')
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error downloading CSV:', error)
    throw error
  }
}

/**
 * Download topology data as Excel file
 */
export const downloadTopologyExcel = async (): Promise<void> => {
  try {
    const response = await apiClient.get('/export/excel', {
      responseType: 'blob'
    })
    
    // Create blob link to download
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // Get filename from response headers or use default
    const disposition = response.headers['content-disposition']
    let filename = 'topology_export.xlsx'
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/"/g, '')
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error downloading Excel:', error)
    throw error
  }
}

/**
 * Calculate the bounding box of all devices in the topology
 */
const calculateDeviceBounds = (svgElement: SVGSVGElement) => {
  const deviceGroups = svgElement.querySelectorAll('.topology-node')
  
  if (deviceGroups.length === 0) {
    return { minX: 0, minY: 0, maxX: 1200, maxY: 800 }
  }
  
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  
  deviceGroups.forEach(group => {
    const transform = group.getAttribute('transform')
    if (transform) {
      const match = transform.match(/translate\(([^,]+),([^)]+)\)/)
      if (match) {
        const x = parseFloat(match[1])
        const y = parseFloat(match[2])
        
        // Add padding around each device (node radius + text)
        const padding = 80
        minX = Math.min(minX, x - padding)
        minY = Math.min(minY, y - padding)
        maxX = Math.max(maxX, x + padding)
        maxY = Math.max(maxY, y + padding)
      }
    }
  })
  
  // Add extra margin around the whole topology
  const margin = 50
  return {
    minX: minX - margin,
    minY: minY - margin,
    maxX: maxX + margin,
    maxY: maxY + margin
  }
}

/**
 * Create a clean SVG for export by recreating topology from scratch
 */
const createExportSvg = (svgElement: SVGSVGElement, bounds: { minX: number, minY: number, maxX: number, maxY: number }, boundaries?: any[]) => {
  const contentWidth = bounds.maxX - bounds.minX
  const contentHeight = bounds.maxY - bounds.minY
  
  // Create new SVG element
  const exportSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  exportSvg.setAttribute('width', contentWidth.toString())
  exportSvg.setAttribute('height', contentHeight.toString())
  exportSvg.setAttribute('viewBox', `${bounds.minX} ${bounds.minY} ${contentWidth} ${contentHeight}`)
  exportSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  
  // Add white background
  const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
  background.setAttribute('x', bounds.minX.toString())
  background.setAttribute('y', bounds.minY.toString())
  background.setAttribute('width', contentWidth.toString())
  background.setAttribute('height', contentHeight.toString())
  background.setAttribute('fill', 'white')
  exportSvg.appendChild(background)
  
  // Copy connection lines first (so they appear behind devices)
  const connections = svgElement.querySelectorAll('line')
  connections.forEach(line => {
    const newLine = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    newLine.setAttribute('x1', line.getAttribute('x1') || '0')
    newLine.setAttribute('y1', line.getAttribute('y1') || '0')
    newLine.setAttribute('x2', line.getAttribute('x2') || '0')
    newLine.setAttribute('y2', line.getAttribute('y2') || '0')
    newLine.setAttribute('stroke', '#6b7280')
    newLine.setAttribute('stroke-width', '2')
    exportSvg.appendChild(newLine)
  })
  
  // Add boundaries if provided
  if (boundaries && boundaries.length > 0) {
    boundaries.forEach(boundary => {
      if (boundary.points && boundary.points.length >= 3) {
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
        const points = boundary.points.map((p: any) => `${p.x},${p.y}`).join(' ')
        
        polygon.setAttribute('points', points)
        polygon.setAttribute('fill', boundary.style?.fill || 'none')
        polygon.setAttribute('fill-opacity', (boundary.style?.fillOpacity || 0).toString())
        polygon.setAttribute('stroke', boundary.style?.color || '#3b82f6')
        polygon.setAttribute('stroke-width', (boundary.style?.strokeWidth || 2).toString())
        
        if (boundary.style?.dashArray) {
          polygon.setAttribute('stroke-dasharray', boundary.style.dashArray)
        }
        
        exportSvg.appendChild(polygon)
        
        // Add boundary label
        if (boundary.label && boundary.points.length > 0) {
          const centerX = boundary.points.reduce((sum: number, p: any) => sum + p.x, 0) / boundary.points.length
          const centerY = boundary.points.reduce((sum: number, p: any) => sum + p.y, 0) / boundary.points.length
          
          const label = document.createElementNS('http://www.w3.org/2000/svg', 'text')
          label.setAttribute('x', centerX.toString())
          label.setAttribute('y', centerY.toString())
          label.setAttribute('text-anchor', 'middle')
          label.setAttribute('dominant-baseline', 'central')
          label.setAttribute('font-family', 'Arial, sans-serif')
          label.setAttribute('font-size', '14')
          label.setAttribute('font-weight', 'bold')
          label.setAttribute('fill', boundary.style?.color || '#3b82f6')
          label.setAttribute('paint-order', 'stroke')
          label.setAttribute('stroke', 'white')
          label.setAttribute('stroke-width', '3')
          label.textContent = boundary.label
          
          exportSvg.appendChild(label)
        }
      }
    })
  }
  
  // Get all device groups and recreate them
  const deviceGroups = svgElement.querySelectorAll('.topology-node')
  deviceGroups.forEach(group => {
    const transform = group.getAttribute('transform')
    if (!transform) return
    
    const match = transform.match(/translate\(([^,]+),([^)]+)\)/)
    if (!match) return
    
    const x = parseFloat(match[1])
    const y = parseFloat(match[2])
    
    // Create group for this device
    const deviceGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    deviceGroup.setAttribute('transform', `translate(${x}, ${y})`)
    
    // Create device circle
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    circle.setAttribute('cx', '0')
    circle.setAttribute('cy', '0')
    circle.setAttribute('r', '24')
    circle.setAttribute('fill', '#3b82f6')
    circle.setAttribute('stroke', '#1e40af')
    circle.setAttribute('stroke-width', '2')
    deviceGroup.appendChild(circle)
    
    // Get device info from text elements
    const titleText = group.querySelector('.topology-node-title')
    const subtitleText = group.querySelector('.topology-node-subtitle')
    const riskText = group.querySelector('.topology-node-risk')
    
    // Add device type abbreviation in circle
    if (subtitleText) {
      const deviceType = subtitleText.textContent || 'DEV'
      const abbrev = deviceType.substring(0, 3).toUpperCase()
      
      const typeText = document.createElementNS('http://www.w3.org/2000/svg', 'text')
      typeText.setAttribute('x', '0')
      typeText.setAttribute('y', '5')
      typeText.setAttribute('text-anchor', 'middle')
      typeText.setAttribute('font-family', 'Arial, sans-serif')
      typeText.setAttribute('font-size', '12')
      typeText.setAttribute('font-weight', 'bold')
      typeText.setAttribute('fill', 'white')
      typeText.textContent = abbrev
      deviceGroup.appendChild(typeText)
    }
    
    // Add device name below
    if (titleText) {
      const nameText = document.createElementNS('http://www.w3.org/2000/svg', 'text')
      nameText.setAttribute('x', '0')
      nameText.setAttribute('y', '44')
      nameText.setAttribute('text-anchor', 'middle')
      nameText.setAttribute('font-family', 'Arial, sans-serif')
      nameText.setAttribute('font-size', '14')
      nameText.setAttribute('font-weight', 'bold')
      nameText.setAttribute('fill', '#1f2937')
      nameText.textContent = titleText.textContent || 'Device'
      deviceGroup.appendChild(nameText)
    }
    
    // Add device type below name
    if (subtitleText) {
      const subtitleElement = document.createElementNS('http://www.w3.org/2000/svg', 'text')
      subtitleElement.setAttribute('x', '0')
      subtitleElement.setAttribute('y', '62')
      subtitleElement.setAttribute('text-anchor', 'middle')
      subtitleElement.setAttribute('font-family', 'Arial, sans-serif')
      subtitleElement.setAttribute('font-size', '12')
      subtitleElement.setAttribute('fill', '#6b7280')
      subtitleElement.textContent = subtitleText.textContent || ''
      deviceGroup.appendChild(subtitleElement)
    }
    
    // Add risk level if available
    if (riskText) {
      const riskElement = document.createElementNS('http://www.w3.org/2000/svg', 'text')
      riskElement.setAttribute('x', '0')
      riskElement.setAttribute('y', '80')
      riskElement.setAttribute('text-anchor', 'middle')
      riskElement.setAttribute('font-family', 'Arial, sans-serif')
      riskElement.setAttribute('font-size', '10')
      
      const riskContent = riskText.textContent || ''
      if (riskContent.includes('High')) {
        riskElement.setAttribute('fill', '#ef4444')
      } else if (riskContent.includes('Moderate')) {
        riskElement.setAttribute('fill', '#f59e0b')
      } else if (riskContent.includes('Low')) {
        riskElement.setAttribute('fill', '#22c55e')
      } else {
        riskElement.setAttribute('fill', '#6b7280')
      }
      
      riskElement.textContent = riskContent
      deviceGroup.appendChild(riskElement)
    }
    
    exportSvg.appendChild(deviceGroup)
  })
  
  return exportSvg
}

/**
 * Export topology canvas as PNG image with proper cropping and rendering
 */
export const exportTopologyImage = (svgElement: SVGSVGElement, filename: string = 'topology.png', boundaries?: any[]): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      // Calculate the bounds of actual content
      const bounds = calculateDeviceBounds(svgElement)
      const contentWidth = bounds.maxX - bounds.minX
      const contentHeight = bounds.maxY - bounds.minY
      
      // Create a completely new, clean SVG for export
      const exportSvg = createExportSvg(svgElement, bounds, boundaries)
      
      // Create a canvas element
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Could not get canvas context'))
        return
      }
      
      // Set canvas size with some scaling for better quality
      const scale = 2 // Higher DPI
      canvas.width = contentWidth * scale
      canvas.height = contentHeight * scale
      canvas.style.width = contentWidth + 'px'
      canvas.style.height = contentHeight + 'px'
      ctx.scale(scale, scale)
      
      // Set white background immediately
      ctx.fillStyle = 'white'
      ctx.fillRect(0, 0, contentWidth, contentHeight)
      
      // Convert SVG to image
      const svgData = new XMLSerializer().serializeToString(exportSvg)
      console.log('Export SVG created:', svgData.substring(0, 500) + '...') // Debug log
      
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
      const url = URL.createObjectURL(svgBlob)
      
      const img = new Image()
      img.onload = () => {
        try {
          console.log('Image loaded successfully, drawing to canvas...')
          
          // Draw the SVG image on top of white background
          ctx.drawImage(img, 0, 0, contentWidth, contentHeight)
          
          // Download the image
          canvas.toBlob((blob) => {
            if (blob) {
              const downloadUrl = URL.createObjectURL(blob)
              const link = document.createElement('a')
              link.href = downloadUrl
              link.download = filename
              document.body.appendChild(link)
              link.click()
              link.remove()
              URL.revokeObjectURL(downloadUrl)
              URL.revokeObjectURL(url)
              console.log('PNG export completed successfully')
              resolve()
            } else {
              URL.revokeObjectURL(url)
              reject(new Error('Failed to create image blob'))
            }
          }, 'image/png')
        } catch (drawError) {
          console.error('Error drawing to canvas:', drawError)
          URL.revokeObjectURL(url)
          reject(drawError)
        }
      }
      
      img.onerror = (error) => {
        console.error('Failed to load SVG image:', error)
        URL.revokeObjectURL(url)
        reject(new Error('Failed to load SVG image'))
      }
      
      // Add timeout to prevent hanging
      setTimeout(() => {
        if (!img.complete) {
          console.error('Image loading timeout')
          URL.revokeObjectURL(url)
          reject(new Error('Image loading timeout'))
        }
      }, 10000) // 10 second timeout
      
      console.log('Starting image load...')
      img.src = url
    } catch (error) {
      console.error('Error exporting image:', error)
      reject(error)
    }
  })
}

/**
 * Export topology canvas as SVG file
 */
export const exportTopologySVG = (svgElement: SVGSVGElement, filename: string = 'topology.svg'): void => {
  try {
    // Clone the SVG to avoid modifying the original
    const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement
    
    // Add XML namespace if not present
    if (!clonedSvg.getAttribute('xmlns')) {
      clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    }
    
    // Serialize SVG
    const svgData = new XMLSerializer().serializeToString(clonedSvg)
    
    // Create blob and download
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error exporting SVG:', error)
    throw error
  }
}
