import type { PointerEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { selectConnections, selectDevices, selectSelectedEntity } from '../store/selectors'
import { resetConnections } from '../store/connectionsSlice'
import { selectEntity, toggleMultiSelect, clearMultiSelection, resetUi } from '../store/uiSlice'
import { updateDevice, updateDeviceAsync, resetDevices } from '../store/devicesSlice'
import { 
  startDrawing, 
  addDrawingPoint, 
  finishDrawing, 
  cancelDrawing,
  clearAllBoundaries,
  createBoundaryAsync,
  fetchBoundaries,
  selectBoundaries,
  selectIsDrawingBoundary,
  selectCurrentBoundaryType,
  selectDrawingPoints,
  updateBoundary,
  BOUNDARY_LABELS,
  BOUNDARY_STYLES
} from '../store/boundariesSlice'
import { DEVICE_LABELS } from '../constants/deviceTypes'
import DeviceIcon from './DeviceIcon'
import ExportModal from './ExportModal'

const CANVAS_WIDTH = 1920
const CANVAS_HEIGHT = 1080
const NODE_RADIUS = 36
const LABEL_PADDING = 6
const LABEL_HEIGHT = 22
const ESTIMATED_CHAR_WIDTH = 7
const MIN_ZOOM = 0.5
const MAX_ZOOM = 2.0
const ZOOM_STEP = 0.1

interface DragState {
  id: string
  offsetX: number
  offsetY: number
  position: { x: number; y: number }
  startTime: number
  startPosition: { x: number; y: number }
  hasMoved: boolean
}

interface GroupDragState {
  devices: {
    id: string
    offset: { x: number; y: number }
    initialPosition: { x: number; y: number }
    currentPosition: { x: number; y: number }
  }[]
  startTime: number
  startPosition: { x: number; y: number }
  hasMoved: boolean
}


const TopologyCanvas = () => {
  const dispatch = useDispatch()
  const devices = useSelector(selectDevices)
  const connections = useSelector(selectConnections)
  const selected = useSelector(selectSelectedEntity)
  const multiSelected = useSelector((state: any) => state.ui.multiSelected)
  
  // Boundary state
  const boundaries = useSelector(selectBoundaries)
  const isDrawingBoundary = useSelector(selectIsDrawingBoundary)
  const currentBoundaryType = useSelector(selectCurrentBoundaryType)
  const drawingPoints = useSelector(selectDrawingPoints)

  const svgRef = useRef<SVGSVGElement | null>(null)
  const canvasAreaRef = useRef<HTMLDivElement | null>(null)
  const [dragState, setDragState] = useState<DragState | null>(null)
  const [groupDragState, setGroupDragState] = useState<GroupDragState | null>(null)
  const [zoom, setZoom] = useState(1)
  const [zoomCenter, setZoomCenter] = useState({ x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 })
  const [containerDimensions, setContainerDimensions] = useState({
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT
  })
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null)
  const [isMouseDown, setIsMouseDown] = useState(false)
  const [mouseDownPosition, setMouseDownPosition] = useState<{ x: number; y: number } | null>(null)

  // Calculate effective canvas dimensions based on zoom level and actual container size
  const effectiveCanvasWidth = useMemo(() => {
    // Use actual container width as base, expand when zooming out
    const baseWidth = Math.max(containerDimensions.width, CANVAS_WIDTH)
    const expansionFactor = zoom < 1 ? (1 / zoom) : 1
    return baseWidth * expansionFactor
  }, [zoom, containerDimensions.width])

  const effectiveCanvasHeight = useMemo(() => {
    // Use actual container height as base, expand when zooming out
    const baseHeight = Math.max(containerDimensions.height, CANVAS_HEIGHT)
    const expansionFactor = zoom < 1 ? (1 / zoom) : 1
    return baseHeight * expansionFactor
  }, [zoom, containerDimensions.height])

  // Calculate viewBox dimensions to center the large canvas in the panel
  const viewBoxDimensions = useMemo(() => {
    // At 100% zoom, show the entire canvas
    // At higher zoom, show a smaller portion centered on zoomCenter
    const viewBoxWidth = CANVAS_WIDTH / zoom
    const viewBoxHeight = CANVAS_HEIGHT / zoom
    
    // Center the view around zoomCenter
    const halfViewWidth = viewBoxWidth / 2
    const halfViewHeight = viewBoxHeight / 2
    
    return {
      x: zoomCenter.x - halfViewWidth,
      y: zoomCenter.y - halfViewHeight,
      width: viewBoxWidth,
      height: viewBoxHeight
    }
  }, [zoom, zoomCenter])

  const positionedDevices = useMemo(() => {
    if (devices.length === 0) {
      return []
    }

    const devicesWithoutPosition = devices.filter((device) => !device.position)

    const fallbackPositions = new Map<string, { x: number; y: number }>()

    if (devicesWithoutPosition.length > 0) {
      if (devicesWithoutPosition.length === 1) {
        fallbackPositions.set(devicesWithoutPosition[0].id, {
          x: effectiveCanvasWidth / 2,
          y: effectiveCanvasHeight / 2,
        })
      } else {
        // Create multiple rings for better space utilization when zoomed out
        const maxRadius = Math.min(effectiveCanvasWidth, effectiveCanvasHeight) / 2.1 - NODE_RADIUS * 2
        const minRadius = NODE_RADIUS * 8
        const deviceCount = devicesWithoutPosition.length
        
        // Determine how many rings we need based on device count and zoom level
        const ringsNeeded = Math.max(1, Math.floor(Math.sqrt(deviceCount / 6)))
        const devicesPerRing = Math.ceil(deviceCount / ringsNeeded)
        
        devicesWithoutPosition.forEach((device, index) => {
          const ringIndex = Math.floor(index / devicesPerRing)
          const deviceInRing = index % devicesPerRing
          const totalInThisRing = Math.min(devicesPerRing, deviceCount - ringIndex * devicesPerRing)
          
          // Calculate radius for this ring
          const radiusStep = ringsNeeded > 1 ? (maxRadius - minRadius) / (ringsNeeded - 1) : 0
          const radius = minRadius + (radiusStep * ringIndex)
          
          // Calculate angle for device in this ring
          const angle = (deviceInRing / totalInThisRing) * Math.PI * 2
          
          fallbackPositions.set(device.id, {
            x: effectiveCanvasWidth / 2 + radius * Math.cos(angle),
            y: effectiveCanvasHeight / 2 + radius * Math.sin(angle),
          })
        })
      }
    }

    return devices.map((device, index) => {
      const fallback = fallbackPositions.get(device.id)
      let basePosition = device.position ?? fallback ?? {
        x: effectiveCanvasWidth / 2 + index * 10,
        y: effectiveCanvasHeight / 2 + index * 10,
      }

      // If device has a saved position and canvas is expanded, scale the position to use more space
      if (device.position && zoom < 1) {
        const baseWidth = Math.max(containerDimensions.width, CANVAS_WIDTH)
        const baseHeight = Math.max(containerDimensions.height, CANVAS_HEIGHT)
        const scaleFactorX = effectiveCanvasWidth / baseWidth
        const scaleFactorY = effectiveCanvasHeight / baseHeight
        
        // Scale position from center
        const centerX = baseWidth / 2
        const centerY = baseHeight / 2
        const offsetX = (device.position.x - centerX) * scaleFactorX
        const offsetY = (device.position.y - centerY) * scaleFactorY
        
        basePosition = {
          x: effectiveCanvasWidth / 2 + offsetX,
          y: effectiveCanvasHeight / 2 + offsetY,
        }
      }

      // Handle individual device drag
      const draggingPosition =
        dragState && dragState.id === device.id ? dragState.position : undefined

      // Handle group drag
      let groupDragPosition = undefined
      if (groupDragState) {
        const groupDevice = groupDragState.devices.find(d => d.id === device.id)
        if (groupDevice) {
          groupDragPosition = groupDevice.currentPosition
        }
      }

      const position = draggingPosition ?? groupDragPosition ?? basePosition

      return {
        device,
        x: position.x,
        y: position.y,
      }
    })
  }, [devices, dragState, groupDragState, effectiveCanvasWidth, effectiveCanvasHeight, zoom, containerDimensions])

  const positionsById = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>()
    positionedDevices.forEach(({ device, x, y }) => {
      map.set(device.id, { x, y })
    })
    return map
  }, [positionedDevices])

  const connectionSegments = useMemo(() => {
    // console.log('🔍 DEBUG: Calculating connection segments')
    // console.log('Connections count:', connections.length)
    // console.log('Connections data:', connections)
    // console.log('Device positions map:', positionsById)
    
    const result = connections
      .map((connection) => {
        const source = positionsById.get(connection.sourceDeviceId)
        const target = positionsById.get(connection.targetDeviceId)

        // console.log(`Connection ${connection.id}: ${connection.sourceDeviceId} → ${connection.targetDeviceId}`)
        // console.log(`Source position for ${connection.sourceDeviceId}:`, source)
        // console.log(`Target position for ${connection.targetDeviceId}:`, target)

        if (!source || !target) {
          console.warn(`❌ Skipping connection ${connection.id} - missing positions`)
          return null
        }

        const midpoint = {
          x: (source.x + target.x) / 2,
          y: (source.y + target.y) / 2,
        }

        const labelText = connection.linkType || 'connection'
        const labelWidth = Math.max(
          labelText.length * ESTIMATED_CHAR_WIDTH + LABEL_PADDING * 2,
          44,
        )
        const labelX = midpoint.x - labelWidth / 2
        const labelY = midpoint.y - LABEL_HEIGHT / 2

        const segment = {
          connection,
          source,
          target,
          midpoint,
          label: {
            text: labelText,
            width: labelWidth,
            x: labelX,
            y: labelY,
            height: LABEL_HEIGHT,
            centerY: labelY + LABEL_HEIGHT / 2,
          },
        }
        
        // console.log(`✅ Created segment for connection ${connection.id}:`, segment)
        return segment
      })
      .filter((segment): segment is NonNullable<typeof segment> => Boolean(segment))
    
    // console.log('🎯 Final connection segments count:', result.length)
    // console.log('🎯 Final connection segments:', result)
    return result
  }, [connections, positionsById])

  const handleBackgroundMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    if (isDrawingBoundary) {
      const rect = canvasAreaRef.current?.getBoundingClientRect()
      if (rect) {
        const cursorX = event.clientX - rect.left
        const cursorY = event.clientY - rect.top
        
        // Convert to SVG coordinates using viewBox
        const viewBox = viewBoxDimensions
        const svgX = viewBox.x + (cursorX / rect.width) * viewBox.width
        const svgY = viewBox.y + (cursorY / rect.height) * viewBox.height
        
        setIsMouseDown(true)
        setMouseDownPosition({ x: svgX, y: svgY })
        
        if (drawingPoints.length === 0) {
          // Start drawing - set the first corner
          dispatch(addDrawingPoint({ x: svgX, y: svgY }))
        }
      }
      return
    }
    
    // Only set mouse down if not clicking on interactive elements
    const target = event.target as Element
    if (!target.closest('.topology-boundary') && !target.closest('.topology-node')) {
      setIsMouseDown(true)
    }
  }

  const handleBackgroundMouseUp = (event: React.MouseEvent<HTMLDivElement>) => {
    if (isDrawingBoundary && isMouseDown && mouseDownPosition && drawingPoints.length === 1) {
      const rect = canvasAreaRef.current?.getBoundingClientRect()
      if (rect) {
        const cursorX = event.clientX - rect.left
        const cursorY = event.clientY - rect.top
        
        // Convert to SVG coordinates using viewBox
        const viewBox = viewBoxDimensions
        const svgX = viewBox.x + (cursorX / rect.width) * viewBox.width
        const svgY = viewBox.y + (cursorY / rect.height) * viewBox.height
        
        // Complete the rectangle
        const firstPoint = drawingPoints[0]
        const secondPoint = { x: svgX, y: svgY }
        
        // Only create boundary if there's a meaningful size
        const minSize = 20 // minimum size in SVG units
        if (Math.abs(secondPoint.x - firstPoint.x) > minSize || Math.abs(secondPoint.y - firstPoint.y) > minSize) {
          // Create a rectangle from these two diagonal corners
          const minX = Math.min(firstPoint.x, secondPoint.x)
          const maxX = Math.max(firstPoint.x, secondPoint.x)
          const minY = Math.min(firstPoint.y, secondPoint.y)
          const maxY = Math.max(firstPoint.y, secondPoint.y)
          
          // Create a new boundary with the rectangle points
          const newBoundary = {
            id: `boundary-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            type: currentBoundaryType!,
            label: `${BOUNDARY_LABELS[currentBoundaryType!]} ${new Date().toLocaleDateString()}`,
            points: [
              { x: minX, y: minY }, // Top-left
              { x: maxX, y: minY }, // Top-right
              { x: maxX, y: maxY }, // Bottom-right
              { x: minX, y: maxY }  // Bottom-left
            ],
            closed: true,
            style: BOUNDARY_STYLES[currentBoundaryType!],
            created: new Date().toISOString(),
            // New device-like properties
            position: {
              x: minX,
              y: minY,
              width: maxX - minX,
              height: maxY - minY
            },
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
            config: {}
          }
          
          // Create the boundary via API
          dispatch(createBoundaryAsync(newBoundary))
          
          // Finish the drawing
          dispatch(finishDrawing({ 
            label: newBoundary.label
          }))
        } else {
          // Too small, cancel the drawing
          dispatch(cancelDrawing())
        }
      }
    } else if (!isDrawingBoundary && isMouseDown) {
      // Only clear selection if we actually started the mouse down on the background
      // and didn't click on any interactive element
      const target = event.target as Element
      if (!target.closest('.topology-boundary') && !target.closest('.topology-node')) {
        dispatch(selectEntity(null))
        if (multiSelected) {
          dispatch(clearMultiSelection())
        }
      }
    }
    
    setIsMouseDown(false)
    setMouseDownPosition(null)
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    // Track mouse position for boundary drawing preview
    if (isDrawingBoundary) {
      const rect = canvasAreaRef.current?.getBoundingClientRect()
      if (rect) {
        const cursorX = event.clientX - rect.left
        const cursorY = event.clientY - rect.top
        
        // Convert to SVG coordinates using viewBox (same as click handler)
        const viewBox = viewBoxDimensions
        const svgX = viewBox.x + (cursorX / rect.width) * viewBox.width
        const svgY = viewBox.y + (cursorY / rect.height) * viewBox.height
        
        setMousePosition({ x: svgX, y: svgY })
      }
    } else {
      setMousePosition(null)
    }
  }

  const handleZoomIn = () => {
    setZoom(prevZoom => Math.min(MAX_ZOOM, prevZoom + ZOOM_STEP))
  }

  const handleZoomOut = () => {
    setZoom(prevZoom => Math.max(MIN_ZOOM, prevZoom - ZOOM_STEP))
  }

  const handleZoomReset = () => {
    setZoom(1)
    setZoomCenter({ x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 })
  }

  const handleNewDiagram = () => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      'Create a new diagram? This will clear all devices, connections, and boundaries. This action cannot be undone.'
    )
    
    if (confirmed) {
      // Clear all data
      dispatch(resetDevices())
      dispatch(resetConnections())
      dispatch(clearAllBoundaries())
      dispatch(resetUi())
      
      // Reset view
      setZoom(1)
      setZoomCenter({ x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 })
    }
  }

  const handleWheel = useCallback((event: React.WheelEvent) => {
    // Don't use preventDefault for passive events
    if (event.cancelable) {
      event.preventDefault()
    }
    
    // Get cursor position relative to the canvas
    const rect = canvasAreaRef.current?.getBoundingClientRect()
    if (!rect) return
    
    const cursorX = event.clientX - rect.left
    const cursorY = event.clientY - rect.top
    
    // Convert to SVG coordinates using the current viewBox
    const viewBox = viewBoxDimensions
    const svgX = viewBox.x + (cursorX / rect.width) * viewBox.width
    const svgY = viewBox.y + (cursorY / rect.height) * viewBox.height
    
    // Calculate zoom delta
    const delta = event.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
    const newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom + delta))
    
    if (newZoom !== zoom) {
      // Calculate new center to keep the cursor point stable
      const viewBoxWidth = CANVAS_WIDTH / newZoom
      const viewBoxHeight = CANVAS_HEIGHT / newZoom
      
      // Calculate where the cursor point should be in the new view
      const cursorRatioX = cursorX / rect.width
      const cursorRatioY = cursorY / rect.height
      
      // Calculate new center that keeps the cursor point stable
      const newCenterX = svgX - (cursorRatioX - 0.5) * viewBoxWidth
      const newCenterY = svgY - (cursorRatioY - 0.5) * viewBoxHeight
      
      // Constrain the center to keep content visible
      const maxCenterX = CANVAS_WIDTH - viewBoxWidth / 2
      const minCenterX = viewBoxWidth / 2
      const maxCenterY = CANVAS_HEIGHT - viewBoxHeight / 2
      const minCenterY = viewBoxHeight / 2
      
      const constrainedCenterX = Math.max(minCenterX, Math.min(maxCenterX, newCenterX))
      const constrainedCenterY = Math.max(minCenterY, Math.min(maxCenterY, newCenterY))
      
      setZoom(newZoom)
      setZoomCenter({ x: constrainedCenterX, y: constrainedCenterY })
    }
  }, [zoom, viewBoxDimensions])

  // Keyboard shortcuts for zoom and pan
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case '=':
          case '+':
            event.preventDefault()
            handleZoomIn()
            break
          case '-':
            event.preventDefault()
            handleZoomOut()
            break
          case '0':
            event.preventDefault()
            handleZoomReset()
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [zoom]) // Re-bind when zoom changes to access current zoom value

  // Monitor container size changes
  useEffect(() => {
    const updateDimensions = () => {
      if (canvasAreaRef.current) {
        const rect = canvasAreaRef.current.getBoundingClientRect()
        // Always use the large canvas dimensions for maximum space
        setContainerDimensions({
          width: CANVAS_WIDTH,
          height: CANVAS_HEIGHT
        })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    
    // Use ResizeObserver if available for better container tracking
    let resizeObserver: ResizeObserver | null = null
    if (canvasAreaRef.current && window.ResizeObserver) {
      resizeObserver = new ResizeObserver(updateDimensions)
      resizeObserver.observe(canvasAreaRef.current)
    }

    return () => {
      window.removeEventListener('resize', updateDimensions)
      if (resizeObserver) {
        resizeObserver.disconnect()
      }
    }
  }, [])

  // Fetch boundaries on component mount
  useEffect(() => {
    dispatch(fetchBoundaries())
  }, [dispatch])

  const clampPosition = useCallback((value: { x: number; y: number }) => {
    return {
      x: Math.min(effectiveCanvasWidth - NODE_RADIUS, Math.max(NODE_RADIUS, value.x)),
      y: Math.min(effectiveCanvasHeight - NODE_RADIUS, Math.max(NODE_RADIUS, value.y)),
    }
  }, [effectiveCanvasWidth, effectiveCanvasHeight])

  const svgPointFromEvent = useCallback(
    (event: PointerEvent<SVGGElement | SVGElement>) => {
      const svg = svgRef.current
      if (!svg) {
        return null
      }

      const point = svg.createSVGPoint()
      point.x = event.clientX
      point.y = event.clientY

      const ctm = svg.getScreenCTM()
      if (!ctm) {
        return null
      }

      const transformed = point.matrixTransform(ctm.inverse())
      return { x: transformed.x, y: transformed.y }
    },
    [],
  )



  if (devices.length === 0) {
    return (
      <div className="panel topology-canvas" role="presentation">
        <header className="panel-header">
          <div>
            <h3>Topology View</h3>
            <p className="panel-subtitle">Add devices to visualize the network.</p>
          </div>
          <div className="zoom-controls">
            <button className="zoom-button" disabled title="Zoom Out">−</button>
            <span className="zoom-indicator">100%</span>
            <button className="zoom-button" disabled title="Zoom In">+</button>
            <button className="zoom-button zoom-reset" disabled title="Reset Zoom">⌂</button>
          </div>
        </header>
        <div className="topology-canvas-area">
          <p className="topology-canvas-empty">Create a device to populate the canvas.</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`panel topology-canvas ${zoom < 0.3 ? 'zoomed-out' : ''}`} role="presentation">
      <header className="panel-header">
        <div>
          <h3>Topology View</h3>
          <p className="panel-subtitle">Visualize how devices are linked.</p>
        </div>
        <div className="topology-controls">
          <div className="boundary-controls">
            <button 
              className="boundary-button ato"
              onClick={() => dispatch(startDrawing('ato'))}
              disabled={isDrawingBoundary}
              title="Draw ATO Boundary"
            >
              🔴 ATO
            </button>
            <button 
              className="boundary-button building"
              onClick={() => dispatch(startDrawing('building'))}
              disabled={isDrawingBoundary}
              title="Draw Building Boundary"
            >
              🏢 Building
            </button>
            <button 
              className="boundary-button network"
              onClick={() => dispatch(startDrawing('network_segment'))}
              disabled={isDrawingBoundary}
              title="Draw Network Segment"
            >
              🌐 Network
            </button>
            <button 
              className="boundary-button security"
              onClick={() => dispatch(startDrawing('security_zone'))}
              disabled={isDrawingBoundary}
              title="Draw Security Zone"
            >
              🛡️ Security
            </button>
            {isDrawingBoundary && (
              <>
                <button 
                  className="boundary-button finish"
                  onClick={() => dispatch(finishDrawing({ label: `${BOUNDARY_LABELS[currentBoundaryType!]} ${new Date().toLocaleDateString()}` }))}
                  disabled={drawingPoints.length < 3}
                  title="Finish Drawing Boundary"
                >
                  ✅ Finish
                </button>
                <button 
                  className="boundary-button cancel"
                  onClick={() => dispatch(cancelDrawing())}
                  title="Cancel Drawing"
                >
                  ❌ Cancel
                </button>
              </>
            )}
          </div>
          
          <div className="zoom-controls">
            <button 
              className="zoom-button new-diagram-button" 
              onClick={handleNewDiagram}
              title="New Diagram"
            >
              📄
            </button>
            <button 
              className="zoom-button" 
              onClick={handleZoomOut} 
              disabled={zoom <= MIN_ZOOM}
              title="Zoom Out"
            >
              −
            </button>
            <span className="zoom-indicator">
              {zoom >= 0.1 ? Math.round(zoom * 100) : Math.round(zoom * 1000) / 10}%
            </span>
            <button 
              className="zoom-button" 
              onClick={handleZoomIn} 
              disabled={zoom >= MAX_ZOOM}
              title="Zoom In"
            >
              +
            </button>
            <button 
              className="zoom-button zoom-reset" 
              onClick={handleZoomReset}
              title="Reset Zoom"
            >
              ⌂
            </button>
            <button 
              className="zoom-button" 
              onClick={() => setIsExportModalOpen(true)}
              title="Export Topology"
            >
              📤
            </button>
          </div>
        </div>
      </header>
      <div 
        ref={canvasAreaRef} 
        className="topology-canvas-area" 
        onMouseDown={handleBackgroundMouseDown}
        onMouseUp={handleBackgroundMouseUp}
        onMouseMove={handleMouseMove}
        onWheel={handleWheel}
      >
        <svg
          ref={svgRef}
          className="topology-canvas-svg"
          viewBox={`${viewBoxDimensions.x} ${viewBoxDimensions.y} ${viewBoxDimensions.width} ${viewBoxDimensions.height}`}
          preserveAspectRatio="xMidYMid meet"
          onPointerLeave={() => {
            if (dragState) {
              setDragState(null)
            }
          }}
        >
          <defs>
            <radialGradient id="nodeGradient" cx="50%" cy="50%" r="65%">
              <stop offset="0%" stopColor="#dbeafe" />
              <stop offset="100%" stopColor="#60a5fa" />
            </radialGradient>
            <radialGradient id="nodeGradientLowRisk" cx="50%" cy="50%" r="65%">
              <stop offset="0%" stopColor="#dcfce7" />
              <stop offset="100%" stopColor="#22c55e" />
            </radialGradient>
            <radialGradient id="nodeGradientMediumRisk" cx="50%" cy="50%" r="65%">
              <stop offset="0%" stopColor="#fef3c7" />
              <stop offset="100%" stopColor="#f59e0b" />
            </radialGradient>
            <radialGradient id="nodeGradientHighRisk" cx="50%" cy="50%" r="65%">
              <stop offset="0%" stopColor="#fee2e2" />
              <stop offset="100%" stopColor="#ef4444" />
            </radialGradient>
            <radialGradient id="nodeGradientUnknown" cx="50%" cy="50%" r="65%">
              <stop offset="0%" stopColor="#f3f4f6" />
              <stop offset="100%" stopColor="#9ca3af" />
            </radialGradient>
          </defs>

          <rect width={effectiveCanvasWidth} height={effectiveCanvasHeight} className="topology-canvas-backdrop" />

          {connectionSegments.map(({ connection, source, target, midpoint, label }) => {
            const isSelected = selected?.kind === 'connection' && selected.id === connection.id

            return (
              <g
                key={connection.id}
                className={`topology-connection ${isSelected ? 'is-selected' : ''}`}
                onClick={(event) => {
                  event.stopPropagation()
                  dispatch(selectEntity({ kind: 'connection', id: connection.id }))
                }}
              >
                <line
                  className="topology-connection-hitbox"
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                />
                <line
                  className="topology-connection-line"
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                />
                <rect
                  className="topology-connection-label-bg"
                  x={label.x}
                  y={label.y}
                  width={label.width}
                  height={label.height}
                  rx={label.height / 2}
                  ry={label.height / 2}
                  pointerEvents="none"
                />
                <text className="topology-connection-label" x={midpoint.x} y={label.centerY}>
                  {label.text}
                </text>
              </g>
            )
          })}

          {/* Render boundaries */}
          {boundaries.map(boundary => {
            const isSelected = selected?.kind === 'boundary' && selected.id === boundary.id
            return (
              <g 
                key={boundary.id} 
                className={`topology-boundary ${isSelected ? 'is-selected' : ''}`}
                style={{ cursor: 'pointer' }}
                onClick={(event) => {
                  event.stopPropagation()
                  event.preventDefault()
                  console.log('🔥 BOUNDARY CLICK EVENT:', boundary.id, 'isDrawing:', isDrawingBoundary)
                  // Don't interfere with boundary drawing
                  if (!isDrawingBoundary) {
                    console.log('🔥 Dispatching boundary selection...')
                    dispatch(selectEntity({ kind: 'boundary', id: boundary.id }))
                  }
                }}
              >
                <polygon
                  points={boundary.points.map(p => `${p.x},${p.y}`).join(' ')}
                  fill={boundary.style.fill || 'none'}
                  fillOpacity={boundary.style.fillOpacity || 0}
                  stroke={isSelected ? '#2563eb' : boundary.style.color}
                  strokeWidth={isSelected ? boundary.style.strokeWidth + 1 : boundary.style.strokeWidth}
                  strokeDasharray={boundary.style.dashArray || 'none'}
                  style={{ pointerEvents: 'auto' }}
                />
                {/* Invisible clickable area for easier selection */}
                <polygon
                  points={boundary.points.map(p => `${p.x},${p.y}`).join(' ')}
                  fill="transparent"
                  strokeWidth="10"
                  stroke="transparent"
                  style={{ pointerEvents: 'auto' }}
                />
                {/* Boundary label */}
                {boundary.points.length > 0 && (
                  <text
                    x={boundary.points.reduce((sum, p) => sum + p.x, 0) / boundary.points.length}
                    y={boundary.points.reduce((sum, p) => sum + p.y, 0) / boundary.points.length}
                    textAnchor="middle"
                    className="topology-boundary-label"
                    fill={isSelected ? '#2563eb' : boundary.style.color}
                    fontSize="14"
                    fontWeight="bold"
                    pointerEvents="none"
                  >
                    {boundary.label}
                  </text>
                )}

                {/* Resize handles for selected boundaries */}
                {isSelected && boundary.points.length > 0 && (() => {
                  // Calculate bounding box from points
                  const minX = Math.min(...boundary.points.map(p => p.x))
                  const maxX = Math.max(...boundary.points.map(p => p.x))
                  const minY = Math.min(...boundary.points.map(p => p.y))
                  const maxY = Math.max(...boundary.points.map(p => p.y))
                  
                  const handleSize = 8
                  const handleColor = '#2563eb'
                  
                  const ResizeHandle = ({ cx, cy, cursor, onMouseDown }) => (
                    <rect
                      x={cx - handleSize/2}
                      y={cy - handleSize/2}
                      width={handleSize}
                      height={handleSize}
                      fill={handleColor}
                      stroke="white"
                      strokeWidth="2"
                      style={{ 
                        cursor, 
                        pointerEvents: 'auto',
                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                      }}
                      onMouseDown={onMouseDown}
                    />
                  )

                  const handleResizeStart = (e, corner) => {
                    e.stopPropagation()
                    e.preventDefault()
                    
                    const startX = e.clientX
                    const startY = e.clientY
                    const svgRect = e.currentTarget.closest('svg').getBoundingClientRect()
                    
                    const originalBounds = { minX, maxX, minY, maxY }
                    
                    const handleMouseMove = (moveEvent) => {
                      const deltaX = (moveEvent.clientX - startX) / zoom
                      const deltaY = (moveEvent.clientY - startY) / zoom
                      
                      let newMinX = originalBounds.minX
                      let newMaxX = originalBounds.maxX  
                      let newMinY = originalBounds.minY
                      let newMaxY = originalBounds.maxY
                      
                      // Adjust bounds based on which corner is being dragged
                      switch (corner) {
                        case 'top-left':
                          newMinX = Math.min(originalBounds.minX + deltaX, originalBounds.maxX - 50)
                          newMinY = Math.min(originalBounds.minY + deltaY, originalBounds.maxY - 50)
                          break
                        case 'top-right':
                          newMaxX = Math.max(originalBounds.maxX + deltaX, originalBounds.minX + 50)
                          newMinY = Math.min(originalBounds.minY + deltaY, originalBounds.maxY - 50)
                          break
                        case 'bottom-left':
                          newMinX = Math.min(originalBounds.minX + deltaX, originalBounds.maxX - 50)
                          newMaxY = Math.max(originalBounds.maxY + deltaY, originalBounds.minY + 50)
                          break
                        case 'bottom-right':
                          newMaxX = Math.max(originalBounds.maxX + deltaX, originalBounds.minX + 50)
                          newMaxY = Math.max(originalBounds.maxY + deltaY, originalBounds.minY + 50)
                          break
                      }
                      
                      // Update boundary points to match new bounds
                      const newPoints = [
                        { x: newMinX, y: newMinY },
                        { x: newMaxX, y: newMinY },
                        { x: newMaxX, y: newMaxY },
                        { x: newMinX, y: newMaxY }
                      ]
                      
                      // Update position properties
                      const newPosition = {
                        x: newMinX,
                        y: newMinY,
                        width: newMaxX - newMinX,
                        height: newMaxY - newMinY
                      }
                      
                      dispatch(updateBoundary({ 
                        id: boundary.id, 
                        updates: { 
                          points: newPoints,
                          position: newPosition,
                          x: newMinX,
                          y: newMinY,
                          width: newMaxX - newMinX,
                          height: newMaxY - newMinY
                        }
                      }))
                    }
                    
                    const handleMouseUp = () => {
                      document.removeEventListener('mousemove', handleMouseMove)
                      document.removeEventListener('mouseup', handleMouseUp)
                    }
                    
                    document.addEventListener('mousemove', handleMouseMove)
                    document.addEventListener('mouseup', handleMouseUp)
                  }
                  
                  return (
                    <g className="boundary-resize-handles">
                      {/* Corner handles */}
                      <ResizeHandle 
                        cx={minX} 
                        cy={minY} 
                        cursor="nw-resize"
                        onMouseDown={(e) => handleResizeStart(e, 'top-left')}
                      />
                      <ResizeHandle 
                        cx={maxX} 
                        cy={minY} 
                        cursor="ne-resize"
                        onMouseDown={(e) => handleResizeStart(e, 'top-right')}
                      />
                      <ResizeHandle 
                        cx={maxX} 
                        cy={maxY} 
                        cursor="se-resize"
                        onMouseDown={(e) => handleResizeStart(e, 'bottom-right')}
                      />
                      <ResizeHandle 
                        cx={minX} 
                        cy={maxY} 
                        cursor="sw-resize"
                        onMouseDown={(e) => handleResizeStart(e, 'bottom-left')}
                      />
                    </g>
                  )
                })()}
              </g>
            )
          })}

          {/* Render drawing boundary (preview) - Rectangular boundaries */}
          {isDrawingBoundary && (
            <g className="topology-boundary-drawing">
              {/* Show live rectangular preview during drag */}
              {drawingPoints.length === 1 && isMouseDown && mousePosition && (
                (() => {
                  const firstPoint = drawingPoints[0]
                  const minX = Math.min(firstPoint.x, mousePosition.x)
                  const maxX = Math.max(firstPoint.x, mousePosition.x)
                  const minY = Math.min(firstPoint.y, mousePosition.y)
                  const maxY = Math.max(firstPoint.y, mousePosition.y)
                  
                  return (
                    <>
                      {/* Live rectangle preview */}
                      <rect
                        x={minX}
                        y={minY}
                        width={maxX - minX}
                        height={maxY - minY}
                        fill="rgba(59, 130, 246, 0.1)"
                        stroke="#3b82f6"
                        strokeWidth="2"
                        strokeDasharray="5,5"
                        pointerEvents="none"
                      />
                      {/* Show corner points */}
                      <circle cx={minX} cy={minY} r="3" fill="#3b82f6" stroke="white" strokeWidth="1" pointerEvents="none" />
                      <circle cx={maxX} cy={minY} r="3" fill="#3b82f6" stroke="white" strokeWidth="1" pointerEvents="none" />
                      <circle cx={maxX} cy={maxY} r="3" fill="#3b82f6" stroke="white" strokeWidth="1" pointerEvents="none" />
                      <circle cx={minX} cy={maxY} r="3" fill="#3b82f6" stroke="white" strokeWidth="1" pointerEvents="none" />
                    </>
                  )
                })()
              )}
              
              {/* Show static preview when not dragging but have mouse position */}
              {drawingPoints.length === 1 && !isMouseDown && mousePosition && (
                (() => {
                  const firstPoint = drawingPoints[0]
                  const minX = Math.min(firstPoint.x, mousePosition.x)
                  const maxX = Math.max(firstPoint.x, mousePosition.x)
                  const minY = Math.min(firstPoint.y, mousePosition.y)
                  const maxY = Math.max(firstPoint.y, mousePosition.y)
                  
                  return (
                    <rect
                      x={minX}
                      y={minY}
                      width={maxX - minX}
                      height={maxY - minY}
                      fill="none"
                      stroke="#94a3b8"
                      strokeWidth="1"
                      strokeDasharray="3,3"
                      pointerEvents="none"
                      opacity="0.5"
                    />
                  )
                })()
              )}
              
              {/* Show placed first corner */}
              {drawingPoints.length >= 1 && (
                <circle
                  cx={drawingPoints[0].x}
                  cy={drawingPoints[0].y}
                  r="5"
                  fill="#3b82f6"
                  stroke="white"
                  strokeWidth="2"
                  pointerEvents="none"
                />
              )}
              
              {/* Show instruction text */}
              {drawingPoints.length === 0 && (
                <text
                  x={mousePosition?.x || CANVAS_WIDTH / 2}
                  y={(mousePosition?.y || CANVAS_HEIGHT / 2) - 20}
                  textAnchor="middle"
                  fill="#3b82f6"
                  fontSize="14"
                  fontWeight="bold"
                  pointerEvents="none"
                >
                  Mouse down and drag to draw boundary
                </text>
              )}
              
              {drawingPoints.length === 1 && !isMouseDown && (
                <text
                  x={mousePosition?.x || CANVAS_WIDTH / 2}
                  y={(mousePosition?.y || CANVAS_HEIGHT / 2) - 20}
                  textAnchor="middle"
                  fill="#3b82f6"
                  fontSize="14"
                  fontWeight="bold"
                  pointerEvents="none"
                >
                  Mouse down and drag to complete boundary
                </text>
              )}
              
              {drawingPoints.length === 1 && isMouseDown && (
                <text
                  x={mousePosition?.x || CANVAS_WIDTH / 2}
                  y={(mousePosition?.y || CANVAS_HEIGHT / 2) - 20}
                  textAnchor="middle"
                  fill="#3b82f6"
                  fontSize="14"
                  fontWeight="bold"
                  pointerEvents="none"
                >
                  Release to create boundary
                </text>
              )}
            </g>
          )}

          {positionedDevices.map(({ device, x, y }) => {
            const isSingleSelected = selected?.kind === 'device' && selected.id === device.id
            const isMultiSelected = multiSelected?.kind === 'device' && multiSelected.ids.includes(device.id)
            const isSelected = isSingleSelected || isMultiSelected
            const isGroupDragging = groupDragState?.devices.some(d => d.id === device.id) || false
            
            // Determine security status and visual indicators
            const riskLevel = device.config.riskLevel || 'Moderate'
            const complianceStatus = device.config.complianceStatus || 'Not Assessed'
            const vulnerabilities = parseInt(device.config.vulnerabilities || '0')
            const monitoringEnabled = device.config.monitoringEnabled === 'true'
            
            // Choose gradient based on risk level
            let gradientId = 'nodeGradient'
            switch (riskLevel) {
              case 'Very Low':
              case 'Low':
                gradientId = 'nodeGradientLowRisk'
                break
              case 'Moderate':
                gradientId = 'nodeGradientMediumRisk'
                break
              case 'High':
              case 'Very High':
                gradientId = 'nodeGradientHighRisk'
                break
              default:
                gradientId = 'nodeGradientUnknown'
            }

            return (
              <g
                key={device.id}
                className={`topology-node ${isSelected ? 'is-selected' : ''} ${isMultiSelected ? 'is-multi-selected' : ''} ${isGroupDragging ? 'is-group-dragging' : ''}`}
                transform={`translate(${x}, ${y})`}
                style={{ cursor: 'pointer' }}
                onClick={(event) => {
                  event.stopPropagation()
                  // Don't interfere with boundary drawing
                  if (!isDrawingBoundary) {
                    if (event.ctrlKey || event.metaKey) {
                      dispatch(toggleMultiSelect({ kind: 'device', id: device.id }))
                    } else {
                      dispatch(selectEntity({ kind: 'device', id: device.id }))
                    }
                  }
                }}
                onPointerDown={(event) => {
                  event.stopPropagation()
                  event.preventDefault()
                  const currentPosition = positionsById.get(device.id)
                  const svgPoint = svgPointFromEvent(event)
                  if (!currentPosition || !svgPoint) {
                    return
                  }

                  // Check if this device is part of a multi-selection
                  const isInMultiSelection = multiSelected?.kind === 'device' && multiSelected.ids.includes(device.id)
                  
                  if (isInMultiSelection && multiSelected.ids.length > 1) {
                    // Start group drag for all selected devices
                    const groupDevices = multiSelected.ids.map(deviceId => {
                      const devicePosition = positionsById.get(deviceId)
                      if (!devicePosition) return null
                      
                      return {
                        id: deviceId,
                        offset: {
                          x: svgPoint.x - devicePosition.x,
                          y: svgPoint.y - devicePosition.y
                        },
                        initialPosition: devicePosition,
                        currentPosition: devicePosition
                      }
                    }).filter(Boolean) as GroupDragState['devices']

                    setGroupDragState({
                      devices: groupDevices,
                      startTime: Date.now(),
                      startPosition: { x: svgPoint.x, y: svgPoint.y },
                      hasMoved: false,
                    })
                  } else {
                    // Start single device drag
                    setDragState({
                      id: device.id,
                      offsetX: svgPoint.x - currentPosition.x,
                      offsetY: svgPoint.y - currentPosition.y,
                      position: currentPosition,
                      startTime: Date.now(),
                      startPosition: { x: svgPoint.x, y: svgPoint.y },
                      hasMoved: false,
                    })
                  }
                  
                  event.currentTarget.setPointerCapture(event.pointerId)
                }}
                onPointerMove={(event) => {
                  const svgPoint = svgPointFromEvent(event)
                  if (!svgPoint) {
                    return
                  }

                  // Handle group drag
                  if (groupDragState) {
                    const deltaX = Math.abs(svgPoint.x - groupDragState.startPosition.x)
                    const deltaY = Math.abs(svgPoint.y - groupDragState.startPosition.y)
                    const hasMoved = deltaX > 5 || deltaY > 5

                    // Calculate new positions for all devices in the group
                    const updatedDevices = groupDragState.devices.map(groupDevice => {
                      const newX = svgPoint.x - groupDevice.offset.x
                      const newY = svgPoint.y - groupDevice.offset.y
                      const clampedPosition = clampPosition({ x: newX, y: newY })
                      
                      return {
                        ...groupDevice,
                        currentPosition: clampedPosition
                      }
                    })

                    setGroupDragState(prev => prev ? {
                      ...prev,
                      devices: updatedDevices,
                      hasMoved
                    } : null)
                    return
                  }

                  // Handle single device drag
                  if (!dragState || dragState.id !== device.id) {
                    return
                  }

                  // Check if we've moved enough to consider this a drag (not just a click)
                  const deltaX = Math.abs(svgPoint.x - dragState.startPosition.x)
                  const deltaY = Math.abs(svgPoint.y - dragState.startPosition.y)
                  const hasMoved = deltaX > 5 || deltaY > 5

                  const nextPosition = clampPosition({
                    x: svgPoint.x - dragState.offsetX,
                    y: svgPoint.y - dragState.offsetY,
                  })

                  setDragState((previous) =>
                    previous && previous.id === device.id
                      ? {
                          ...previous,
                          position: nextPosition,
                          hasMoved,
                        }
                      : previous,
                  )
                }}
                onPointerUp={(event) => {
                  event.currentTarget.releasePointerCapture(event.pointerId)
                  
                  // Handle group drag completion
                  if (groupDragState) {
                    const wasActuallyDragged = groupDragState.hasMoved
                    const groupDevices = groupDragState.devices
                    
                    setGroupDragState(null)
                    
                    // Update positions for all devices if they were actually dragged
                    if (wasActuallyDragged) {
                      groupDevices.forEach(groupDevice => {
                        dispatch(updateDeviceAsync({ 
                          id: groupDevice.id, 
                          position: groupDevice.currentPosition 
                        }))
                      })
                    }
                    return
                  }
                  
                  // Handle single device drag completion
                  if (dragState && dragState.id === device.id) {
                    const finalPosition = dragState.position
                    const wasActuallyDragged = dragState.hasMoved
                    
                    setDragState(null)
                    
                    // Only update position if the device was actually dragged
                    if (finalPosition && wasActuallyDragged) {
                      // Only update backend - it will update local state when successful
                      dispatch(updateDeviceAsync({ id: device.id, position: finalPosition }))
                    }
                  }
                }}
                onPointerCancel={(event) => {
                  event.currentTarget.releasePointerCapture(event.pointerId)
                  
                  // Cancel group drag
                  if (groupDragState) {
                    setGroupDragState(null)
                    return
                  }
                  
                  // Cancel single device drag
                  if (dragState && dragState.id === device.id) {
                    setDragState(null)
                  }
                }}
              >
                {/* Invisible background circle for click area and positioning */}
                <circle 
                  r={zoom < 0.2 ? NODE_RADIUS * 0.8 : NODE_RADIUS} 
                  fill="transparent" 
                  stroke="none"
                  strokeWidth="0"
                  opacity="0"
                />
                
                {/* Selection ring for selected devices */}
                {(isSelected || isMultiSelected) && (
                  <circle 
                    r={zoom < 0.2 ? 22 : 28} 
                    fill="none" 
                    stroke={isSelected ? "#3b82f6" : "#10b981"}
                    strokeWidth={zoom < 0.2 ? "2" : "3"}
                    opacity="0.8"
                    className="selection-ring"
                  />
                )}
                
                {/* Main device icon (replaces the circle) */}
                <foreignObject 
                  x={zoom < 0.2 ? "-18" : "-24"} 
                  y={zoom < 0.2 ? "-18" : "-24"} 
                  width={zoom < 0.2 ? "36" : "48"} 
                  height={zoom < 0.2 ? "36" : "48"}
                  className="topology-node-icon"
                >
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    width: '100%', 
                    height: '100%' 
                  }}>
                    <DeviceIcon 
                      deviceType={device.type} 
                      size={zoom < 0.2 ? 28 : 36} 
                    />
                  </div>
                </foreignObject>
                
                {/* Security indicators removed for clean icon display */}
                
                <text className="topology-node-title" y={NODE_RADIUS + 20}>
                  {device.name}
                </text>
                <text className="topology-node-subtitle" y={NODE_RADIUS + 38}>
                  {DEVICE_LABELS[device.type] || device.type}
                </text>
                
                {/* Risk level indicator */}
                <text 
                  className="topology-node-risk" 
                  y={NODE_RADIUS + 56}
                  fill={
                    riskLevel === 'High' || riskLevel === 'Very High' ? '#ef4444' :
                    riskLevel === 'Moderate' ? '#f59e0b' :
                    riskLevel === 'Low' || riskLevel === 'Very Low' ? '#22c55e' :
                    '#6b7280'
                  }
                >
                  {riskLevel} Risk
                </text>
              </g>
            )
          })}
        </svg>
      </div>
      
      <ExportModal 
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        svgRef={svgRef}
      />
    </div>
  )
}

export default TopologyCanvas


