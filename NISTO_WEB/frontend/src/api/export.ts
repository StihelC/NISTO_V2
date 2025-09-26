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
 * Calculate the bounding box of all devices and boundaries in the topology
 */
const calculateDeviceBounds = (svgElement: SVGSVGElement, boundaries?: any[]) => {
  const deviceGroups = svgElement.querySelectorAll('.topology-node')
  
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  
  // Calculate bounds from devices
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
  
  // Calculate bounds from boundaries
  if (boundaries && boundaries.length > 0) {
    boundaries.forEach(boundary => {
      if (boundary.points && boundary.points.length >= 3) {
        boundary.points.forEach((point: any) => {
          minX = Math.min(minX, point.x)
          minY = Math.min(minY, point.y)
          maxX = Math.max(maxX, point.x)
          maxY = Math.max(maxY, point.y)
        })
      }
    })
  }
  
  // If no devices or boundaries found, use default bounds
  if (minX === Infinity || deviceGroups.length === 0) {
    return { minX: 0, minY: 0, maxX: 1200, maxY: 800 }
  }
  
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
 * Create a clean SVG for export by cloning the existing SVG and fixing styling
 */
const createExportSvg = (svgElement: SVGSVGElement, bounds: { minX: number, minY: number, maxX: number, maxY: number }, boundaries?: any[]) => {
  const contentWidth = bounds.maxX - bounds.minX
  const contentHeight = bounds.maxY - bounds.minY
  
  // Clone the entire SVG to preserve everything exactly as displayed
  const exportSvg = svgElement.cloneNode(true) as SVGSVGElement
  
  // Set the viewBox to crop to the content bounds
  exportSvg.setAttribute('viewBox', `${bounds.minX} ${bounds.minY} ${contentWidth} ${contentHeight}`)
  exportSvg.setAttribute('width', contentWidth.toString())
  exportSvg.setAttribute('height', contentHeight.toString())
  
  // Fix any label backgrounds that might appear black in export
  const labelBgs = exportSvg.querySelectorAll('.topology-connection-label-bg, .topology-node-label-bg')
  labelBgs.forEach(bg => {
    bg.setAttribute('fill', 'white')
    bg.setAttribute('stroke', '#9ca3af')
    bg.setAttribute('stroke-width', '1')
  })
  
  // Ensure all text is dark for visibility and properly positioned
  const textElements = exportSvg.querySelectorAll('text')
  textElements.forEach(text => {
    const currentFill = text.getAttribute('fill')
    if (!currentFill || currentFill === 'rgba(255, 255, 255, 0.85)' || currentFill.includes('rgba')) {
      text.setAttribute('fill', '#111827')
    }
    
    // Ensure text positioning attributes are preserved
    if (!text.getAttribute('text-anchor')) {
      text.setAttribute('text-anchor', 'middle')
    }
    if (!text.getAttribute('dominant-baseline')) {
      text.setAttribute('dominant-baseline', 'middle')
    }
  })
  
  // Ensure connection lines are visible
  const connectionLines = exportSvg.querySelectorAll('line.topology-connection-line')
  connectionLines.forEach(line => {
    line.setAttribute('stroke', '#6b7280')
    line.setAttribute('stroke-width', '2')
    line.setAttribute('stroke-linecap', 'round')
  })
  
  // Ensure canvas backdrop is white
  const backdrop = exportSvg.querySelector('.topology-canvas-backdrop')
  if (backdrop) {
    backdrop.setAttribute('fill', 'white')
  }
  
  // Remove any margin elements that might interfere
  const marginElements = exportSvg.querySelectorAll('.topology-canvas-margin')
  marginElements.forEach(el => el.remove())
  
  return exportSvg
}

/**
 * Export topology canvas as PNG image with proper cropping and rendering
 */
export const exportTopologyImage = (svgElement: SVGSVGElement, filename: string = 'topology.png', boundaries?: any[]): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      // Calculate the bounds of actual content including boundaries
      const bounds = calculateDeviceBounds(svgElement, boundaries)
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
      
      // Convert SVG to data URL to avoid tainted canvas issues
      const svgData = new XMLSerializer().serializeToString(exportSvg)
      console.log('Export SVG created:', svgData.substring(0, 500) + '...') // Debug log
      
      // Create data URL from SVG
      const svgDataUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
      
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
              console.log('PNG export completed successfully')
              resolve()
            } else {
              reject(new Error('Failed to create image blob'))
            }
          }, 'image/png')
        } catch (drawError) {
          console.error('Error drawing to canvas:', drawError)
          reject(drawError)
        }
      }
      
      img.onerror = (error) => {
        console.error('Failed to load SVG image:', error)
        reject(new Error('Failed to load SVG image'))
      }
      
      // Add timeout to prevent hanging
      setTimeout(() => {
        if (!img.complete) {
          console.error('Image loading timeout')
          reject(new Error('Image loading timeout'))
        }
      }, 10000) // 10 second timeout
      
      console.log('Starting image load...')
      img.src = svgDataUrl
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
