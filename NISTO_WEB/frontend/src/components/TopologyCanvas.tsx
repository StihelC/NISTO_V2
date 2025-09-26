import type { PointerEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { selectConnections, selectDevices, selectSelectedEntity } from '../store/selectors'
import { resetConnections } from '../store/connectionsSlice'
import { selectEntity, toggleMultiSelect, clearMultiSelection, setContextMenu, clearContextMenu, resetUi } from '../store/uiSlice'
import { updateDeviceAsync, resetDevices } from '../store/devicesSlice'
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
  updateBoundaryAsync,
  BOUNDARY_LABELS,
  BOUNDARY_STYLES
} from '../store/boundariesSlice'
import { DEVICE_LABELS } from '../constants/deviceTypes'
// import { CONNECTION_TYPE_OPTIONS } from '../constants/connectionTypes'
import type { RootState } from '../store'
import DeviceIcon from './DeviceIcon'
import ExportModal from './ExportModal'
// Removed DeviceDisplaySettings import - now using per-device preferences
import type { Boundary } from '../store/types'

type BoundaryPosition = {
  x: number
  y: number
  width: number
  height: number
}

const CANVAS_WIDTH = 1920
const CANVAS_HEIGHT = 1080
const CANVAS_PADDING = 80
const TOTAL_CANVAS_WIDTH = CANVAS_WIDTH + CANVAS_PADDING * 2
const TOTAL_CANVAS_HEIGHT = CANVAS_HEIGHT + CANVAS_PADDING * 2
const NODE_RADIUS = 36
const LABEL_PADDING = 6
const LABEL_HEIGHT = 22
const ESTIMATED_CHAR_WIDTH = 7
const MIN_ZOOM = 0.5
const MAX_ZOOM = 3.0
const ZOOM_STEP = 0.2

const isValidNumber = (value: number | undefined | null): value is number =>
  typeof value === 'number' && !Number.isNaN(value)

const DEFAULT_BOUNDARY_SIZE = 200
const BOUNDARY_LABEL_OFFSET = 18

type BoundaryLabelPosition = 'center' | 'below'

const deriveBoundaryPosition = (boundary: Boundary): BoundaryPosition => {
  if (
    isValidNumber(boundary.x) &&
    isValidNumber(boundary.y) &&
    isValidNumber(boundary.width) &&
    isValidNumber(boundary.height)
  ) {
    return {
      x: boundary.x,
      y: boundary.y,
      width: boundary.width,
      height: boundary.height
    }
  }

  if (Array.isArray(boundary.points) && boundary.points.length > 0) {
    const xs = boundary.points.map((point: { x: number }) => point.x)
    const ys = boundary.points.map((point: { y: number }) => point.y)

    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const minY = Math.min(...ys)
    const maxY = Math.max(...ys)

    return {
      x: minX,
      y: minY,
      width: Math.max(maxX - minX, 1),
      height: Math.max(maxY - minY, 1)
    }
  }

  return {
    x: 0,
    y: 0,
    width: DEFAULT_BOUNDARY_SIZE,
    height: DEFAULT_BOUNDARY_SIZE
  }
}

const buildRectanglePoints = (position: BoundaryPosition) => {
  const { x, y, width, height } = position
  return [
    { x, y },
    { x: x + width, y },
    { x: x + width, y: y + height },
    { x, y: y + height }
  ]
}

const getBoundaryGeometry = (boundary: Boundary) => {
  const position = deriveBoundaryPosition(boundary)
  const points = buildRectanglePoints(position)
  return { position, points }
}

const getBoundaryLabelProps = (
  position: BoundaryPosition,
  placement: BoundaryLabelPosition,
) => {
  const centerX = position.x + position.width / 2
  const centerY = position.y + position.height / 2

  switch (placement) {
    case 'below':
      return {
        x: centerX,
        y: position.y + position.height + BOUNDARY_LABEL_OFFSET,
        dominantBaseline: 'hanging' as const,
      }
    case 'center':
    default:
      return {
        x: centerX,
        y: centerY,
        dominantBaseline: 'middle' as const,
      }
  }
}

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
  // Remove global device display preferences - now using per-device preferences
  const multiSelected = useSelector((state: RootState) => state.ui.multiSelected)
  const contextMenu = useSelector((state: RootState) => state.ui.contextMenu)
  
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
  const zoomTimeoutRef = useRef<number | null>(null)
  const [containerDimensions, setContainerDimensions] = useState({
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT
  })
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  // Removed global display settings - now using per-device preferences
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null)
  const [isMouseDown, setIsMouseDown] = useState(false)
  const [mouseDownPosition, setMouseDownPosition] = useState<{ x: number; y: number } | null>(null)
  // const [contextMenuSelection, setContextMenuSelection] = useState<{ deviceIds: string[] } | null>(null)

  // Calculate effective canvas dimensions based on zoom level and actual container size
  const effectiveCanvasWidth = useMemo(() => {
    // For sub-1.0 zoom, keep consistent dimensions to prevent coordinate drift
    return Math.max(containerDimensions.width, CANVAS_WIDTH)
  }, [containerDimensions.width])

  const effectiveCanvasHeight = useMemo(() => {
    // For sub-1.0 zoom, keep consistent dimensions to prevent coordinate drift
    return Math.max(containerDimensions.height, CANVAS_HEIGHT)
  }, [containerDimensions.height])

  // Calculate viewBox dimensions to center the large canvas in the panel
  const viewBoxDimensions = useMemo(() => {
    // At 100% zoom, show the entire canvas plus a subtle margin around the edges
    // At higher zoom, show a smaller portion centered on zoomCenter
    // At lower zoom, ensure we don't exceed the actual canvas bounds
    const viewBoxWidth = Math.min(TOTAL_CANVAS_WIDTH / zoom, TOTAL_CANVAS_WIDTH * 2)
    const viewBoxHeight = Math.min(TOTAL_CANVAS_HEIGHT / zoom, TOTAL_CANVAS_HEIGHT * 2)
    
    // Center the view around zoomCenter, but constrain to canvas bounds
    const halfViewWidth = viewBoxWidth / 2
    const halfViewHeight = viewBoxHeight / 2
    
    // Ensure the viewBox doesn't go outside the canvas bounds
    const minX = -CANVAS_PADDING
    const maxX = CANVAS_WIDTH + CANVAS_PADDING
    const minY = -CANVAS_PADDING
    const maxY = CANVAS_HEIGHT + CANVAS_PADDING
    
    const constrainedX = Math.max(minX, Math.min(maxX - viewBoxWidth, zoomCenter.x - halfViewWidth))
    const constrainedY = Math.max(minY, Math.min(maxY - viewBoxHeight, zoomCenter.y - halfViewHeight))
    
    return {
      x: constrainedX,
      y: constrainedY,
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
          x: CANVAS_WIDTH / 2,
          y: CANVAS_HEIGHT / 2,
        })
      } else {
        // Create multiple rings for better space utilization when zoomed out
        const maxRadius = Math.min(CANVAS_WIDTH, CANVAS_HEIGHT) / 2.1 - NODE_RADIUS * 2
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
            x: CANVAS_WIDTH / 2 + radius * Math.cos(angle),
            y: CANVAS_HEIGHT / 2 + radius * Math.sin(angle),
          })
        })
      }
    }

    return devices.map((device, index) => {
      const fallback = fallbackPositions.get(device.id)
      let basePosition = device.position ?? fallback ?? {
        x: CANVAS_WIDTH / 2 + index * 10,
        y: CANVAS_HEIGHT / 2 + index * 10,
      }

      // For zoom levels below 1.0, keep original positions to prevent coordinate drift
      // The viewBox scaling will handle the visual zoom effect
      if (device.position && zoom < 1) {
        // Simply use the original position without scaling
        basePosition = device.position
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
        const clampedSvgX = Math.min(Math.max(svgX, 0), CANVAS_WIDTH)
        const clampedSvgY = Math.min(Math.max(svgY, 0), CANVAS_HEIGHT)
        
        setIsMouseDown(true)
        setMouseDownPosition({ x: clampedSvgX, y: clampedSvgY })
        
        if (drawingPoints.length === 0) {
          // Start drawing - set the first corner
          dispatch(addDrawingPoint({ x: clampedSvgX, y: clampedSvgY }))
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
        const clampedSvgX = Math.min(Math.max(svgX, 0), CANVAS_WIDTH)
        const clampedSvgY = Math.min(Math.max(svgY, 0), CANVAS_HEIGHT)
        
        // Complete the rectangle
        const firstPoint = drawingPoints[0]
        const secondPoint = { x: clampedSvgX, y: clampedSvgY }
        
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
          dispatch(createBoundaryAsync(newBoundary) as any)
          
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
        const clampedSvgX = Math.min(Math.max(svgX, 0), CANVAS_WIDTH)
        const clampedSvgY = Math.min(Math.max(svgY, 0), CANVAS_HEIGHT)

        setMousePosition({ x: clampedSvgX, y: clampedSvgY })
      }
    } else {
      setMousePosition(null)
    }
  }

  const handleZoomIn = () => {
    setZoom(prevZoom => Math.min(MAX_ZOOM, prevZoom + ZOOM_STEP * 1.5))
  }

  const handleZoomOut = () => {
    setZoom(prevZoom => Math.max(MIN_ZOOM, prevZoom - ZOOM_STEP * 1.5))
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
    
    // Calculate zoom delta with improved responsiveness
    // Use a more aggressive zoom step based on deltaY magnitude
    const deltaY = event.deltaY
    const zoomFactor = Math.min(Math.abs(deltaY) / 100, 1) // Normalize deltaY
    const baseDelta = deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
    const delta = baseDelta * (0.5 + zoomFactor * 0.5) // Scale between 0.5x and 1x of base step
    const newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom + delta))
    
    if (newZoom !== zoom) {
      // Calculate new center to keep the cursor point stable
      const viewBoxWidth = TOTAL_CANVAS_WIDTH / newZoom
      const viewBoxHeight = TOTAL_CANVAS_HEIGHT / newZoom
      
      // Calculate where the cursor point should be in the new view
      const cursorRatioX = cursorX / rect.width
      const cursorRatioY = cursorY / rect.height
      
      // Calculate new center that keeps the cursor point stable
      const newCenterX = svgX - (cursorRatioX - 0.5) * viewBoxWidth
      const newCenterY = svgY - (cursorRatioY - 0.5) * viewBoxHeight
      
      // Constrain the center to keep content visible
      const canvasMinX = -CANVAS_PADDING
      const canvasMaxX = CANVAS_WIDTH + CANVAS_PADDING
      const canvasMinY = -CANVAS_PADDING
      const canvasMaxY = CANVAS_HEIGHT + CANVAS_PADDING
      const maxCenterX = canvasMaxX - viewBoxWidth / 2
      const minCenterX = canvasMinX + viewBoxWidth / 2
      const maxCenterY = canvasMaxY - viewBoxHeight / 2
      const minCenterY = canvasMinY + viewBoxHeight / 2
      
      const constrainedCenterX = Math.max(minCenterX, Math.min(maxCenterX, newCenterX))
      const constrainedCenterY = Math.max(minCenterY, Math.min(maxCenterY, newCenterY))
      
      // Clear any existing timeout
      if (zoomTimeoutRef.current) {
        window.clearTimeout(zoomTimeoutRef.current)
      }
      
      // Apply zoom immediately for responsiveness
      setZoom(newZoom)
      setZoomCenter({ x: constrainedCenterX, y: constrainedCenterY })
      
      // Set a small timeout to prevent excessive updates
      zoomTimeoutRef.current = window.setTimeout(() => {
        zoomTimeoutRef.current = null
      }, 16) // ~60fps
    }
  }, [zoom, viewBoxDimensions])

  // Cleanup zoom timeout on unmount
  useEffect(() => {
    return () => {
      if (zoomTimeoutRef.current) {
        window.clearTimeout(zoomTimeoutRef.current)
      }
    }
  }, [])

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
        // const rect = canvasAreaRef.current.getBoundingClientRect()
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
    dispatch(fetchBoundaries() as any)
  }, [dispatch])

  const clampPosition = useCallback((value: { x: number; y: number }) => {
    return {
      x: Math.min(CANVAS_WIDTH - NODE_RADIUS, Math.max(NODE_RADIUS, value.x)),
      y: Math.min(CANVAS_HEIGHT - NODE_RADIUS, Math.max(NODE_RADIUS, value.y)),
    }
  }, [])

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
      <div className="topology-canvas" role="presentation">
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
    <div className={`topology-canvas ${zoom < 0.3 ? 'zoomed-out' : ''}`} role="presentation">
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
            {/* Removed global display settings button - now using per-device preferences */}
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
          style={{
            transition: 'viewBox 0.15s ease-out'
          }}
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

          <rect
            x={-CANVAS_PADDING}
            y={-CANVAS_PADDING}
            width={TOTAL_CANVAS_WIDTH}
            height={TOTAL_CANVAS_HEIGHT}
            className="topology-canvas-margin"
          />
          <rect width={CANVAS_WIDTH} height={CANVAS_HEIGHT} className="topology-canvas-backdrop" />

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
            const { position, points } = getBoundaryGeometry(boundary)
            const polygonPoints = points.map(p => `${p.x},${p.y}`).join(' ')
            const labelPlacement = (boundary.config?.labelPosition as BoundaryLabelPosition) || 'center'
            const labelProps = getBoundaryLabelProps(position, labelPlacement)

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
                  points={polygonPoints}
                  fill={boundary.style.fill || 'none'}
                  fillOpacity={boundary.style.fillOpacity || 0}
                  stroke={isSelected ? '#2563eb' : boundary.style.color}
                  strokeWidth={isSelected ? boundary.style.strokeWidth + 1 : boundary.style.strokeWidth}
                  strokeDasharray={boundary.style.dashArray || 'none'}
                  style={{ pointerEvents: 'auto' }}
                />
                {/* Invisible clickable area for easier selection */}
                <polygon
                  points={polygonPoints}
                  fill="transparent"
                  strokeWidth="10"
                  stroke="transparent"
                  style={{ pointerEvents: 'auto' }}
                />
                {/* Boundary label */}
                {points.length > 0 && (
                  <text
                    x={labelProps.x}
                    y={labelProps.y}
                    textAnchor="middle"
                    dominantBaseline={labelProps.dominantBaseline}
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
                {isSelected && points.length > 0 && (() => {
                  const minX = position.x
                  const minY = position.y
                  const maxX = position.x + position.width
                  const maxY = position.y + position.height

                  const handleSize = 8
                  const handleColor = '#2563eb'
                  
                  const ResizeHandle = ({ cx, cy, cursor, onMouseDown }: { cx: number; cy: number; cursor: string; onMouseDown: (e: React.MouseEvent) => void }) => (
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

                    const handleResizeStart = (e: React.MouseEvent, corner: string) => {
                    e.stopPropagation()
                    e.preventDefault()
                    
                    const startX = e.clientX
                    const startY = e.clientY
                    // const svgRect = e.currentTarget.closest('svg').getBoundingClientRect()
                    
                    const originalBounds = { minX, maxX, minY, maxY }
                    
                    const handleMouseMove = (moveEvent: MouseEvent) => {
                      const deltaX = (moveEvent.clientX - startX) / zoom
                      const deltaY = (moveEvent.clientY - startY) / zoom

                      let newMinX = originalBounds.minX
                      let newMaxX = originalBounds.maxX
                      let newMinY = originalBounds.minY
                      let newMaxY = originalBounds.maxY

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

                      const newPosition = {
                        x: newMinX,
                        y: newMinY,
                        width: newMaxX - newMinX,
                        height: newMaxY - newMinY
                      }

                      const newPoints = buildRectanglePoints(newPosition)

                      dispatch(
                        updateBoundary({
                          id: boundary.id,
                          updates: {
                            points: newPoints,
                            position: newPosition,
                            x: newPosition.x,
                            y: newPosition.y,
                            width: newPosition.width,
                            height: newPosition.height
                          }
                        })
                      )
                    }

                    const handleMouseUp = (upEvent: MouseEvent) => {
                      document.removeEventListener('mousemove', handleMouseMove)
                      document.removeEventListener('mouseup', handleMouseUp)

                      const deltaX = (upEvent.clientX - startX) / zoom
                      const deltaY = (upEvent.clientY - startY) / zoom

                      let newMinX = originalBounds.minX
                      let newMaxX = originalBounds.maxX
                      let newMinY = originalBounds.minY
                      let newMaxY = originalBounds.maxY

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

                      const finalPosition = {
                        x: newMinX,
                        y: newMinY,
                        width: newMaxX - newMinX,
                        height: newMaxY - newMinY
                      }

                      dispatch(
                        (updateBoundaryAsync({
                          id: boundary.id,
                          updates: {
                            x: finalPosition.x,
                            y: finalPosition.y,
                            width: finalPosition.width,
                            height: finalPosition.height,
                            points: buildRectanglePoints(finalPosition)
                          }
                        }) as any)
                      )
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
                        onMouseDown={(e: React.MouseEvent) => handleResizeStart(e, 'top-left')}
                      />
                      <ResizeHandle 
                        cx={maxX} 
                        cy={minY} 
                        cursor="ne-resize"
                        onMouseDown={(e: React.MouseEvent) => handleResizeStart(e, 'top-right')}
                      />
                      <ResizeHandle 
                        cx={maxX} 
                        cy={maxY} 
                        cursor="se-resize"
                        onMouseDown={(e: React.MouseEvent) => handleResizeStart(e, 'bottom-right')}
                      />
                      <ResizeHandle 
                        cx={minX} 
                        cy={maxY} 
                        cursor="sw-resize"
                        onMouseDown={(e: React.MouseEvent) => handleResizeStart(e, 'bottom-left')}
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
            // const complianceStatus = device.config.complianceStatus || 'Not Assessed'
            // const vulnerabilities = parseInt(device.config.vulnerabilities || '0')
            // const monitoringEnabled = device.config.monitoringEnabled === 'true'
            
            // Choose gradient based on risk level
            // let gradientId = 'nodeGradient'
            // switch (riskLevel) {
            //   case 'Very Low':
            //   case 'Low':
            //     gradientId = 'nodeGradientLowRisk'
            //     break
            //   case 'Moderate':
            //     gradientId = 'nodeGradientMediumRisk'
            //     break
            //   case 'High':
            //   case 'Very High':
            //     gradientId = 'nodeGradientHighRisk'
            //     break
            //   default:
            //     gradientId = 'nodeGradientUnknown'
            // }

            return (
              <g
                key={device.id}
                className={`topology-node ${isSelected ? 'is-selected' : ''} ${isMultiSelected ? 'is-multi-selected' : ''} ${isGroupDragging ? 'is-group-dragging' : ''}`}
                transform={`translate(${x}, ${y})`}
                style={{ cursor: 'pointer' }}
                onClick={(event) => {
                  event.stopPropagation()
                  if (contextMenu) {
                    dispatch(clearContextMenu())
                  }
                  // Don't interfere with boundary drawing
                  if (!isDrawingBoundary) {
                    if (event.ctrlKey || event.metaKey) {
                      dispatch(toggleMultiSelect({ kind: 'device', id: device.id }))
                    } else {
                      dispatch(selectEntity({ kind: 'device', id: device.id }))
                    }
                  }
                  // setContextMenuSelection(null)
                }}
                onContextMenu={(event) => {
                  event.preventDefault()
                  event.stopPropagation()

                  if (isDrawingBoundary) {
                    return
                  }

                  const menuX = event.clientX
                  const menuY = event.clientY

                  let currentSelection = multiSelected?.kind === 'device' ? multiSelected.ids : []

                  if (!(event.ctrlKey || event.metaKey)) {
                    if (!currentSelection.includes(device.id) || currentSelection.length < 2) {
                      currentSelection = [device.id]
                    }
                  } else {
                    if (currentSelection.includes(device.id)) {
                      currentSelection = currentSelection.filter((id) => id !== device.id)
                    } else {
                      currentSelection = [...currentSelection, device.id]
                    }
                  }

                  // setContextMenuSelection({ deviceIds: currentSelection })

                  dispatch(setContextMenu({
                    position: { x: menuX, y: menuY },
                    options: [
                      {
                        id: 'connect-devices',
                        label: currentSelection.length >= 2
                          ? `Connect ${currentSelection.length} devices`
                          : 'Select at least two devices to connect',
                        disabled: currentSelection.length < 2,
                      },
                      {
                        id: 'clear-selection',
                        label: 'Clear selection',
                        disabled: currentSelection.length === 0,
                      },
                    ],
                    meta: {
                      selectedDeviceIds: currentSelection,
                    },
                  }))
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
                        dispatch((updateDeviceAsync({
                          id: groupDevice.id,
                          position: groupDevice.currentPosition
                        }) as any))
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
                      dispatch((updateDeviceAsync({ id: device.id, position: finalPosition }) as any))
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
                
                {/* Single device info bubble */}
                {(() => {
                  // Get device-specific display preferences or use defaults
                  const deviceDisplayPreferences = device.displayPreferences || {
                    // General Properties
                    showDeviceName: true,
                    showDeviceType: true,
                    showCategorizationType: false,
                    
                    // Security Properties
                    showPatchLevel: false,
                    showEncryptionStatus: false,
                    showAccessControlPolicy: false,
                    showMonitoringEnabled: false,
                    showBackupPolicy: false,
                    
                    // Risk Properties
                    showRiskLevel: true,
                    showConfidentialityImpact: false,
                    showIntegrityImpact: false,
                    showAvailabilityImpact: false,
                    showComplianceStatus: false,
                    showVulnerabilities: false,
                    showAuthorizer: false,
                    showLastAssessment: false,
                    showNextAssessment: false,
                  }
                  
                  // Collect all selected properties into a single text
                  const infoLines = []
                  
                  // General Properties
                  if (deviceDisplayPreferences.showDeviceName) {
                    infoLines.push(device.name)
                  }
                  
                  if (deviceDisplayPreferences.showDeviceType) {
                    infoLines.push(DEVICE_LABELS[device.type] || device.type)
                  }
                  
                  if (deviceDisplayPreferences.showCategorizationType) {
                    infoLines.push(`Cat: ${device.config.categorizationType || 'Not Set'}`)
                  }
                  
                  // Security Properties
                  if (deviceDisplayPreferences.showPatchLevel) {
                    infoLines.push(`Patch: ${device.config.patchLevel || 'Unknown'}`)
                  }
                  
                  if (deviceDisplayPreferences.showEncryptionStatus) {
                    infoLines.push(`Enc: ${device.config.encryptionStatus || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showAccessControlPolicy) {
                    infoLines.push(`Access: ${device.config.accessControlPolicy || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showMonitoringEnabled) {
                    const monitoringValue = device.config.monitoringEnabled === 'true' ? 'On' : 
                                          device.config.monitoringEnabled === 'false' ? 'Off' : 'Not Set'
                    infoLines.push(`Monitoring: ${monitoringValue}`)
                  }
                  
                  if (deviceDisplayPreferences.showBackupPolicy) {
                    infoLines.push(`Backup: ${device.config.backupPolicy || 'Not Set'}`)
                  }
                  
                  // Risk Properties
                  if (deviceDisplayPreferences.showRiskLevel) {
                    infoLines.push(`${riskLevel} Risk`)
                  }
                  
                  if (deviceDisplayPreferences.showConfidentialityImpact) {
                    infoLines.push(`C: ${device.config.confidentialityImpact || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showIntegrityImpact) {
                    infoLines.push(`I: ${device.config.integrityImpact || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showAvailabilityImpact) {
                    infoLines.push(`A: ${device.config.availabilityImpact || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showComplianceStatus) {
                    infoLines.push(`Compliance: ${device.config.complianceStatus || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showVulnerabilities) {
                    infoLines.push(`Vulns: ${device.config.vulnerabilities || '0'}`)
                  }
                  
                  if (deviceDisplayPreferences.showAuthorizer) {
                    infoLines.push(`AO: ${device.config.authorizer || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showLastAssessment) {
                    infoLines.push(`Last: ${device.config.lastAssessment || 'Not Set'}`)
                  }
                  
                  if (deviceDisplayPreferences.showNextAssessment) {
                    infoLines.push(`Next: ${device.config.nextAssessment || 'Not Set'}`)
                  }
                  
                  // Only show bubble if there are properties to display
                  if (infoLines.length === 0) {
                    return null
                  }
                  
                  // Calculate dimensions for multi-line bubble
                  const lineHeight = 16
                  const padding = 8
                  const maxLineWidth = Math.max(...infoLines.map(line => line.length * 7))
                  const bgWidth = maxLineWidth + (padding * 2)
                  const bgHeight = (infoLines.length * lineHeight) + (padding * 2)
                  const bgX = -bgWidth / 2
                  const bgY = NODE_RADIUS + 8 // Closer to icon
                  
                  return (
                    <g>
                      <rect
                        className="topology-node-label-bg"
                        x={bgX}
                        y={bgY}
                        width={bgWidth}
                        height={bgHeight}
                        rx={8}
                        ry={8}
                        pointerEvents="none"
                      />
                      {infoLines.map((line, index) => (
                        <text 
                          key={index}
                          className="topology-node-subtitle" 
                          y={bgY + padding + (index * lineHeight) + 12}
                        >
                          {line}
                        </text>
                      ))}
                    </g>
                  )
                })()}
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
      
      {/* Removed global DeviceDisplaySettings modal - now using per-device preferences */}
    </div>
  )
}

export default TopologyCanvas


