import { useState } from 'react'
import { useSelector } from 'react-redux'
import { downloadTopologyCSV, downloadTopologyExcel, exportTopologyImage, exportTopologySVG } from '../api/export'
import { selectBoundaries } from '../store/boundariesSlice'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  svgRef: React.RefObject<SVGSVGElement>
}

const ExportModal = ({ isOpen, onClose, svgRef }: ExportModalProps) => {
  const boundaries = useSelector(selectBoundaries)
  const [isExporting, setIsExporting] = useState(false)
  const [exportStatus, setExportStatus] = useState<string | null>(null)

  if (!isOpen) return null

  const handleExportCSV = async () => {
    setIsExporting(true)
    setExportStatus('Exporting CSV...')
    try {
      await downloadTopologyCSV()
      setExportStatus('CSV exported successfully!')
      setTimeout(() => {
        setExportStatus(null)
        onClose()
      }, 1500)
    } catch (error) {
      setExportStatus('Error exporting CSV')
      console.error('CSV export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportExcel = async () => {
    setIsExporting(true)
    setExportStatus('Exporting Excel...')
    try {
      await downloadTopologyExcel()
      setExportStatus('Excel exported successfully!')
      setTimeout(() => {
        setExportStatus(null)
        onClose()
      }, 1500)
    } catch (error) {
      setExportStatus('Error exporting Excel')
      console.error('Excel export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportPNG = async () => {
    if (!svgRef.current) {
      setExportStatus('No topology to export')
      return
    }

    setIsExporting(true)
    setExportStatus('Exporting PNG image...')
    try {
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-')
      await exportTopologyImage(svgRef.current, `topology-${timestamp}.png`, boundaries)
      setExportStatus('PNG exported successfully!')
      setTimeout(() => {
        setExportStatus(null)
        onClose()
      }, 1500)
    } catch (error) {
      setExportStatus('Error exporting PNG')
      console.error('PNG export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportSVG = () => {
    if (!svgRef.current) {
      setExportStatus('No topology to export')
      return
    }

    setIsExporting(true)
    setExportStatus('Exporting SVG image...')
    try {
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-')
      exportTopologySVG(svgRef.current, `topology-${timestamp}.svg`)
      setExportStatus('SVG exported successfully!')
      setTimeout(() => {
        setExportStatus(null)
        onClose()
      }, 1500)
    } catch (error) {
      setExportStatus('Error exporting SVG')
      console.error('SVG export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Export Topology</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="export-section">
            <h3>Data Export</h3>
            <p className="export-description">
              Export device and connection data with positions and all properties. 
              Compatible with Excel and other spreadsheet applications.
            </p>
            <div className="export-buttons">
              <button 
                className="export-button" 
                onClick={handleExportCSV}
                disabled={isExporting}
              >
                📄 Export CSV
              </button>
              <button 
                className="export-button" 
                onClick={handleExportExcel}
                disabled={isExporting}
              >
                📊 Export Excel
              </button>
            </div>
          </div>

          <div className="export-section">
            <h3>Image Export</h3>
            <p className="export-description">
              Export the visual topology as an image file for documentation or presentations.
            </p>
            <div className="export-buttons">
              <button 
                className="export-button" 
                onClick={handleExportPNG}
                disabled={isExporting}
              >
                🖼️ Export PNG
              </button>
              <button 
                className="export-button" 
                onClick={handleExportSVG}
                disabled={isExporting}
              >
                🎨 Export SVG
              </button>
            </div>
          </div>

          {exportStatus && (
            <div className={`export-status ${exportStatus.includes('Error') ? 'error' : 'success'}`}>
              {exportStatus}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="button secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default ExportModal
