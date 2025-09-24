import type { PointerEvent } from 'react'
import { useCallback, useMemo, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { selectConnections, selectDevices, selectSelectedEntity } from '../store/selectors'
import { selectEntity } from '../store/uiSlice'
import { updateDevice } from '../store/devicesSlice'

const CANVAS_WIDTH = 960
const CANVAS_HEIGHT = 600
const NODE_RADIUS = 36
const LABEL_PADDING = 6
const LABEL_HEIGHT = 22
const ESTIMATED_CHAR_WIDTH = 7

interface DragState {
  id: string
  offsetX: number
  offsetY: number
  position: { x: number; y: number }
}

const TopologyCanvas = () => {
  const dispatch = useDispatch()
  const devices = useSelector(selectDevices)
  const connections = useSelector(selectConnections)
  const selected = useSelector(selectSelectedEntity)

  const svgRef = useRef<SVGSVGElement | null>(null)
  const [dragState, setDragState] = useState<DragState | null>(null)

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
        const radius = Math.max(
          Math.min(CANVAS_WIDTH, CANVAS_HEIGHT) / 2 - NODE_RADIUS * 2,
          NODE_RADIUS * 2.8,
        )
        devicesWithoutPosition.forEach((device, index) => {
          const angle = (index / devicesWithoutPosition.length) * Math.PI * 2
          fallbackPositions.set(device.id, {
            x: CANVAS_WIDTH / 2 + radius * Math.cos(angle),
            y: CANVAS_HEIGHT / 2 + radius * Math.sin(angle),
          })
        })
      }
    }

    return devices.map((device, index) => {
      const fallback = fallbackPositions.get(device.id)
      const basePosition = device.position ?? fallback ?? {
        x: CANVAS_WIDTH / 2 + index * 10,
        y: CANVAS_HEIGHT / 2 + index * 10,
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
  }, [devices, dragState])

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
      <div className="panel topology-canvas" role="presentation">
        <header className="panel-header">
          <div>
            <h3>Topology View</h3>
            <p className="panel-subtitle">Add devices to visualize the network.</p>
          </div>
        </header>
        <div className="topology-canvas-area">
          <p className="topology-canvas-empty">Create a device to populate the canvas.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="panel topology-canvas" role="presentation">
      <header className="panel-header">
        <div>
          <h3>Topology View</h3>
          <p className="panel-subtitle">Visualize how devices are linked.</p>
        </div>
      </header>
      <div className="topology-canvas-area" onClick={handleBackgroundClick}>
        <svg
          ref={svgRef}
          className="topology-canvas-svg"
          viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
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
          </defs>

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

          {positionedDevices.map(({ device, x, y }) => {
            const isSelected = selected?.kind === 'device' && selected.id === device.id

            return (
              <g
                key={device.id}
                className={`topology-node ${isSelected ? 'is-selected' : ''}`}
                transform={`translate(${x}, ${y})`}
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
                  })
                  event.currentTarget.setPointerCapture(event.pointerId)
                  dispatch(selectEntity({ kind: 'device', id: device.id }))
                }}
                onPointerMove={(event) => {
                  if (!dragState || dragState.id !== device.id) {
                    return
                  }

                  const svgPoint = svgPointFromEvent(event)
                  if (!svgPoint) {
                    return
                  }

                  const nextPosition = clampPosition({
                    x: svgPoint.x - dragState.offsetX,
                    y: svgPoint.y - dragState.offsetY,
                  })

                  setDragState((previous) =>
                    previous && previous.id === device.id
                      ? {
                          ...previous,
                          position: nextPosition,
                        }
                      : previous,
                  )
                }}
                onPointerUp={(event) => {
                  if (dragState && dragState.id === device.id) {
                    event.currentTarget.releasePointerCapture(event.pointerId)
                    const finalPosition = dragState.position
                    setDragState(null)
                    if (finalPosition) {
                      dispatch(updateDevice({ id: device.id, position: finalPosition }))
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
                <circle r={NODE_RADIUS} />
                <text className="topology-node-title" y={NODE_RADIUS + 20}>
                  {device.name}
                </text>
                <text className="topology-node-subtitle" y={NODE_RADIUS + 38}>
                  {device.type}
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


