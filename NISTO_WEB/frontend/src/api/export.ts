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
 * Export topology canvas as PNG image
 */
export const exportTopologyImage = (svgElement: SVGSVGElement, filename: string = 'topology.png'): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      // Get the SVG's viewBox or use default dimensions
      const viewBox = svgElement.getAttribute('viewBox')
      let width = 1200
      let height = 800
      
      if (viewBox) {
        const [x, y, w, h] = viewBox.split(' ').map(Number)
        width = w
        height = h
      }
      
      // Create a canvas element
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Could not get canvas context'))
        return
      }
      
      // Set canvas size
      canvas.width = width
      canvas.height = height
      
      // Create an image from SVG
      const svgData = new XMLSerializer().serializeToString(svgElement)
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
      const url = URL.createObjectURL(svgBlob)
      
      const img = new Image()
      img.onload = () => {
        // Set white background
        ctx.fillStyle = 'white'
        ctx.fillRect(0, 0, width, height)
        
        // Draw the SVG image
        ctx.drawImage(img, 0, 0, width, height)
        
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
            resolve()
          } else {
            reject(new Error('Failed to create image blob'))
          }
        }, 'image/png')
        
        URL.revokeObjectURL(url)
      }
      
      img.onerror = () => {
        console.error('Failed to load SVG image')
        URL.revokeObjectURL(url)
        reject(new Error('Failed to load SVG image'))
      }
      
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
