import { useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { createConnectionAsync, fetchConnections } from '../store/connectionsSlice'
import type { AppDispatch, RootState } from '../store'
import type { Device } from '../store/types'

type AutoConnectPattern = 'chain' | 'nearest' | 'star' | 'mesh'

const calculateDistance = (device1: Device, device2: Device) => {
  if (!device1.position || !device2.position) return Number.POSITIVE_INFINITY
  const dx = device1.position.x - device2.position.x
  const dy = device1.position.y - device2.position.y
  return Math.sqrt(dx * dx + dy * dy)
}

interface UseAutoConnectOptions {
  multiSelectedDevices: Device[]
  connectionType: string
}

export const useAutoConnect = ({
  multiSelectedDevices,
  connectionType,
}: UseAutoConnectOptions) => {
  const dispatch = useDispatch<AppDispatch>()
  const connections = useSelector((state: RootState) => state.connections.items)

  const connectSelection = useCallback(
    async (pattern: AutoConnectPattern): Promise<number> => {
      if (multiSelectedDevices.length < 2) {
        window.alert('Select at least two devices to auto-connect.')
        return 0
      }

      const plan: Array<{ sourceId: string; targetId: string }> = []

      switch (pattern) {
        case 'chain':
          for (let i = 0; i < multiSelectedDevices.length - 1; i += 1) {
            plan.push({
              sourceId: multiSelectedDevices[i].id,
              targetId: multiSelectedDevices[i + 1].id,
            })
          }
          break
        case 'nearest':
          multiSelectedDevices.forEach((device, index) => {
            if (index === multiSelectedDevices.length - 1) {
              return
            }

            let nearestDevice: Device | null = null
            let nearestDistance = Number.POSITIVE_INFINITY

            for (let i = index + 1; i < multiSelectedDevices.length; i += 1) {
              const otherDevice = multiSelectedDevices[i]
              const distance = calculateDistance(device, otherDevice)
              if (distance < nearestDistance) {
                nearestDistance = distance
                nearestDevice = otherDevice
              }
            }

            if (nearestDevice) {
              plan.push({ sourceId: device.id, targetId: nearestDevice.id })
            }
          })
          break
        case 'star':
          if (multiSelectedDevices.length >= 2) {
            const centerDevice = multiSelectedDevices[0]
            for (let i = 1; i < multiSelectedDevices.length; i += 1) {
              plan.push({ sourceId: centerDevice.id, targetId: multiSelectedDevices[i].id })
            }
          }
          break
        case 'mesh':
          for (let i = 0; i < multiSelectedDevices.length; i += 1) {
            for (let j = i + 1; j < multiSelectedDevices.length; j += 1) {
              plan.push({ sourceId: multiSelectedDevices[i].id, targetId: multiSelectedDevices[j].id })
            }
          }
          break
        default:
          break
      }

      if (plan.length === 0) {
        return 0
      }

      const existingConnectionKeys = new Set(
        connections.map((connection) => {
          const ids = [connection.sourceDeviceId, connection.targetDeviceId].sort()
          return ids.join('::')
        }),
      )

      let createdCount = 0

      for (const { sourceId, targetId } of plan) {
        const key = [sourceId, targetId].sort().join('::')
        if (existingConnectionKeys.has(key)) {
          continue
        }

        existingConnectionKeys.add(key)

        try {
          await dispatch(
            createConnectionAsync({
              sourceDeviceId: sourceId,
              targetDeviceId: targetId,
              linkType: connectionType,
            }),
          ).unwrap()
          createdCount += 1
        } catch (error) {
          console.error('Failed to create connection', error)
        }
      }

      if (createdCount > 0) {
        const refreshAction = await dispatch(fetchConnections())
        if (fetchConnections.rejected.match(refreshAction)) {
          console.error('Failed to refresh connections', refreshAction)
        }
      }

      return createdCount
    },
    [connectionType, connections, dispatch, multiSelectedDevices],
  )

  const connectNearestNeighbor = useCallback(async () => {
    const created = await connectSelection('nearest')
    if (created === 0) {
      window.alert('Nearest neighbor pairs are already connected.')
    } else {
      window.alert(`Created ${created} nearest neighbor connection${created === 1 ? '' : 's'}.`)
    }
  }, [connectSelection])

  const connectStar = useCallback(async () => {
    const created = await connectSelection('star')
    if (created === 0) {
      window.alert('A star centered on the first selected device already exists.')
    } else {
      window.alert(`Created ${created} star connection${created === 1 ? '' : 's'}.`)
    }
  }, [connectSelection])

  const connectChain = useCallback(async () => {
    const created = await connectSelection('chain')
    if (created === 0) {
      window.alert('All adjacent selected device pairs are already connected.')
    } else {
      window.alert(`Created ${created} chain connection${created === 1 ? '' : 's'} between selected devices.`)
    }
  }, [connectSelection])

  const connectMesh = useCallback(async () => {
    const created = await connectSelection('mesh')
    if (created === 0) {
      window.alert('A full mesh already exists between the selected devices.')
    } else {
      window.alert(`Created ${created} mesh connection${created === 1 ? '' : 's'}.`)
    }
  }, [connectSelection])

  return {
    connectSelection,
    connectNearestNeighbor,
    connectStar,
    connectChain,
    connectMesh,
  }
}

export type UseAutoConnectReturn = ReturnType<typeof useAutoConnect>


