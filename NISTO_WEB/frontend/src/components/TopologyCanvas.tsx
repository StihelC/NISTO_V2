import type { PointerEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { selectConnections, selectDevices, selectSelectedEntity } from '../store/selectors'
import { selectEntity } from '../store/uiSlice'
import { updateDevice, updateDeviceAsync } from '../store/devicesSlice'

const CANVAS_WIDTH = 4000
const CANVAS_HEIGHT = 2400
const NODE_RADIUS = 36
const LABEL_PADDING = 6
const LABEL_HEIGHT = 22
const ESTIMATED_CHAR_WIDTH = 7
const MIN_ZOOM = 1.0
const MAX_ZOOM = 3
const ZOOM_STEP = 0.05

interface DragState {
  id: string
  offsetX: number
  offsetY: number
  position: { x: number; y: number }
  startTime: number
  startPosition: { x: number; y: number }
  hasMoved: boolean
}

interface PanState {
  isPanning: boolean
  startX: number
  startY: number
  startPanOffset: { x: number; y: number }
}

const TopologyCanvas = () => {
  const dispatch = useDispatch()
  const devices = useSelector(selectDevices)
  const connections = useSelector(selectConnections)
  const selected = useSelector(selectSelectedEntity)

  const svgRef = useRef<SVGSVGElement | null>(null)
  const canvasAreaRef = useRef<HTMLDivElement | null>(null)
  const [dragState, setDragState] = useState<DragState | null>(null)
  const [panState, setPanState] = useState<PanState | null>(null)
  const [zoom, setZoom] = useState(1)
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })
  const [containerDimensions, setContainerDimensions] = useState({
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT
  })

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
    if (canvasAreaRef.current) {
      const rect = canvasAreaRef.current.getBoundingClientRect()
      const panelWidth = rect.width || 800
      const panelHeight = rect.height || 600
      
      if (zoom < 0.9) {
        // When significantly zoomed out, show the expanded canvas area
        const viewBoxWidth = effectiveCanvasWidth
        const viewBoxHeight = effectiveCanvasHeight
        // Center the expanded view
        const offsetX = (effectiveCanvasWidth - CANVAS_WIDTH) / 2
        const offsetY = (effectiveCanvasHeight - CANVAS_HEIGHT) / 2
        return {
          x: panOffset.x - offsetX,
          y: panOffset.y - offsetY,
          width: viewBoxWidth,
          height: viewBoxHeight
        }
      } else {
        // Normal zoom: center the large canvas in the panel
        const viewBoxWidth = effectiveCanvasWidth / zoom
        const viewBoxHeight = effectiveCanvasHeight / zoom
        
        // Calculate centering offset to show the center of the large canvas
        const centerX = CANVAS_WIDTH / 2
        const centerY = CANVAS_HEIGHT / 2
        const halfViewWidth = viewBoxWidth / 2
        const halfViewHeight = viewBoxHeight / 2
        
        return {
          x: panOffset.x + centerX - halfViewWidth,
          y: panOffset.y + centerY - halfViewHeight,
          width: viewBoxWidth,
          height: viewBoxHeight
        }
      }
    }
    
    // Fallback
    return {
      x: panOffset.x,
      y: panOffset.y,
      width: effectiveCanvasWidth / zoom,
      height: effectiveCanvasHeight / zoom
    }
  }, [zoom, effectiveCanvasWidth, effectiveCanvasHeight, panOffset])

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

      const draggingPosition =
        dragState && dragState.id === device.id ? dragState.position : undefined

      const position = draggingPosition ?? basePosition

      return {
        device,
        x: position.x,
        y: position.y,
      }
    })
  }, [devices, dragState, effectiveCanvasWidth, effectiveCanvasHeight, zoom, containerDimensions])

  const positionsById = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>()
    positionedDevices.forEach(({ device, x, y }) => {
      map.set(device.id, { x, y })
    })
    return map
  }, [positionedDevices])

  const connectionSegments = useMemo(() => {
    return connections
      .map((connection) => {
        const source = positionsById.get(connection.sourceDeviceId)
        const target = positionsById.get(connection.targetDeviceId)

        if (!source || !target) {
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

        return {
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
      })
      .filter((segment): segment is NonNullable<typeof segment> => Boolean(segment))
  }, [connections, positionsById])

  const handleBackgroundClick = () => {
    dispatch(selectEntity(null))
  }

  const handleZoomIn = () => {
    setZoom(prevZoom => Math.min(MAX_ZOOM, prevZoom + ZOOM_STEP))
  }

  const handleZoomOut = () => {
    setZoom(prevZoom => Math.max(MIN_ZOOM, prevZoom - ZOOM_STEP))
  }

  const handleZoomReset = () => {
    setZoom(1)
    setPanOffset({ x: 0, y: 0 })
  }

  const handleWheel = useCallback((event: React.WheelEvent) => {
    event.preventDefault()
    // Use consistent step for the new zoom range
    const delta = event.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
    setZoom(prevZoom => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prevZoom + delta)))
  }, [zoom])

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
      } else {
        // Arrow keys for panning
        const panStep = 50
        switch (event.key) {
          case 'ArrowUp':
            event.preventDefault()
            setPanOffset(prev => ({ x: prev.x, y: prev.y - panStep }))
            break
          case 'ArrowDown':
            event.preventDefault()
            setPanOffset(prev => ({ x: prev.x, y: prev.y + panStep }))
            break
          case 'ArrowLeft':
            event.preventDefault()
            setPanOffset(prev => ({ x: prev.x - panStep, y: prev.y }))
            break
          case 'ArrowRight':
            event.preventDefault()
            setPanOffset(prev => ({ x: prev.x + panStep, y: prev.y }))
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

  const handleBackgroundPointerDown = useCallback((event: React.PointerEvent) => {
    // Only start panning if not clicking on a device
    const target = event.target as Element
    if (target.closest('.topology-node') || target.closest('.topology-connection')) {
      return
    }

    event.preventDefault()
    const svgPoint = svgPointFromEvent(event)
    if (svgPoint) {
      setPanState({
        isPanning: true,
        startX: svgPoint.x,
        startY: svgPoint.y,
        startPanOffset: { ...panOffset }
      })
      
      // Capture pointer for smooth panning
      if (event.currentTarget instanceof Element) {
        event.currentTarget.setPointerCapture(event.pointerId)
      }
    }
  }, [panOffset, svgPointFromEvent])

  const handleBackgroundPointerMove = useCallback((event: React.PointerEvent) => {
    if (!panState?.isPanning) return

    event.preventDefault()
    const svgPoint = svgPointFromEvent(event)
    if (svgPoint) {
      const deltaX = panState.startX - svgPoint.x
      const deltaY = panState.startY - svgPoint.y
      
      // Apply pan constraints to prevent panning too far
      const maxPanX = CANVAS_WIDTH / 2
      const maxPanY = CANVAS_HEIGHT / 2
      const minPanX = -CANVAS_WIDTH / 2
      const minPanY = -CANVAS_HEIGHT / 2
      
      const newPanX = Math.max(minPanX, Math.min(maxPanX, panState.startPanOffset.x + deltaX))
      const newPanY = Math.max(minPanY, Math.min(maxPanY, panState.startPanOffset.y + deltaY))
      
      setPanOffset({ x: newPanX, y: newPanY })
    }
  }, [panState, svgPointFromEvent])

  const handleBackgroundPointerUp = useCallback((event: React.PointerEvent) => {
    if (panState?.isPanning) {
      event.preventDefault()
      setPanState(null)
      
      // Release pointer capture
      if (event.currentTarget instanceof Element) {
        event.currentTarget.releasePointerCapture(event.pointerId)
      }
    }
  }, [panState])

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
        <div className="zoom-controls">
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
        </div>
      </header>
      <div 
        ref={canvasAreaRef} 
        className={`topology-canvas-area ${panState?.isPanning ? 'panning' : ''}`} 
        onClick={handleBackgroundClick} 
        onWheel={handleWheel}
      >
        <svg
          ref={svgRef}
          className="topology-canvas-svg"
          viewBox={`${viewBoxDimensions.x} ${viewBoxDimensions.y} ${viewBoxDimensions.width} ${viewBoxDimensions.height}`}
          preserveAspectRatio="xMidYMid meet"
          onPointerDown={handleBackgroundPointerDown}
          onPointerMove={handleBackgroundPointerMove}
          onPointerUp={handleBackgroundPointerUp}
          onPointerLeave={() => {
            if (dragState) {
              setDragState(null)
            }
            if (panState?.isPanning) {
              setPanState(null)
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

          {positionedDevices.map(({ device, x, y }) => {
            const isSelected = selected?.kind === 'device' && selected.id === device.id
            
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
                className={`topology-node ${isSelected ? 'is-selected' : ''}`}
                transform={`translate(${x}, ${y})`}
                style={{ cursor: 'pointer' }}
                onClick={(event) => {
                  event.stopPropagation()
                  console.log('Device clicked:', device.id)
                  dispatch(selectEntity({ kind: 'device', id: device.id }))
                }}
                onPointerDown={(event) => {
                  event.stopPropagation()
                  event.preventDefault()
                  const currentPosition = positionsById.get(device.id)
                  const svgPoint = svgPointFromEvent(event)
                  if (!currentPosition || !svgPoint) {
                    return
                  }

                  setDragState({
                    id: device.id,
                    offsetX: svgPoint.x - currentPosition.x,
                    offsetY: svgPoint.y - currentPosition.y,
                    position: currentPosition,
                    startTime: Date.now(),
                    startPosition: { x: svgPoint.x, y: svgPoint.y },
                    hasMoved: false,
                  })
                  event.currentTarget.setPointerCapture(event.pointerId)
                }}
                onPointerMove={(event) => {
                  if (!dragState || dragState.id !== device.id) {
                    return
                  }

                  const svgPoint = svgPointFromEvent(event)
                  if (!svgPoint) {
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
                  if (dragState && dragState.id === device.id) {
                    event.currentTarget.releasePointerCapture(event.pointerId)
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
                  if (dragState && dragState.id === device.id) {
                    event.currentTarget.releasePointerCapture(event.pointerId)
                    setDragState(null)
                  }
                }}
              >
                {/* Main device circle */}
                <circle r={zoom < 0.2 ? NODE_RADIUS * 0.8 : NODE_RADIUS} fill={`url(#${gradientId})`} />
                
                {/* Security indicators */}
                {vulnerabilities > 0 && (
                  <circle 
                    r={6} 
                    cx={NODE_RADIUS - 8} 
                    cy={-NODE_RADIUS + 8} 
                    fill="#ef4444" 
                    stroke="white" 
                    strokeWidth="2"
                  />
                )}
                
                {!monitoringEnabled && (
                  <circle 
                    r={6} 
                    cx={-NODE_RADIUS + 8} 
                    cy={-NODE_RADIUS + 8} 
                    fill="#f59e0b" 
                    stroke="white" 
                    strokeWidth="2"
                  />
                )}
                
                {complianceStatus === 'Compliant' && (
                  <circle 
                    r={6} 
                    cx={0} 
                    cy={-NODE_RADIUS + 8} 
                    fill="#22c55e" 
                    stroke="white" 
                    strokeWidth="2"
                  />
                )}
                
                {complianceStatus === 'Non-Compliant' && (
                  <circle 
                    r={6} 
                    cx={0} 
                    cy={-NODE_RADIUS + 8} 
                    fill="#ef4444" 
                    stroke="white" 
                    strokeWidth="2"
                  />
                )}
                
                <text className="topology-node-title" y={NODE_RADIUS + 20}>
                  {device.name}
                </text>
                <text className="topology-node-subtitle" y={NODE_RADIUS + 38}>
                  {device.type}
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
    </div>
  )
}

export default TopologyCanvas


