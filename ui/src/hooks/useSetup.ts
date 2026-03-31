import { useMemo, useState } from 'react'
import type { SimulationResponse } from '../types'
import { simulate } from '../api'

export interface Robot {
  name: string
  commands: (string | null)[]
}

export function useSetup(
  onRunComplete: (response: SimulationResponse) => void,
  onError: (message: string) => void,
) {
  const [width, setWidth] = useState(5)
  const [height, setHeight] = useState(5)
  const [obstacles, setObstacles] = useState<
    Record<string, [number, number][]>
  >({})
  const [activeObstacleName, setActiveObstacleName] = useState('')
  const [robots, setRobots] = useState<Robot[]>([])

  const robotColorIndex = useMemo(() => {
    const index: Record<string, number> = {}
    robots.forEach((r, i) => {
      index[r.name] = i
    })
    return index
  }, [robots])

  function handleCellClick(x: number, y: number) {
    if (!activeObstacleName.trim()) return
    const name = activeObstacleName.trim()
    const updated = { ...obstacles }
    const cells = updated[name] || []
    const filtered = cells.filter(([cx, cy]) => !(cx === x && cy === y))
    if (filtered.length < cells.length) {
      if (filtered.length === 0) {
        delete updated[name]
      } else {
        updated[name] = filtered
      }
    } else {
      updated[name] = [...cells, [x, y]]
    }
    setObstacles(updated)
  }

  async function handleRun() {
    const maxLen =
      robots.length === 0
        ? 0
        : Math.max(...robots.map((r) => r.commands.length))
    const paddedStacks = robots.map((r) => {
      const stack: (string | null)[] = [...r.commands]
      while (stack.length < maxLen) stack.push(null)
      return stack
    })

    try {
      const res = await simulate({
        width,
        height,
        obstacles,
        robot_names: robots.map((r) => r.name),
        command_stacks: paddedStacks,
      })
      onRunComplete(res)
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Simulation failed')
    }
  }

  return {
    width,
    setWidth,
    height,
    setHeight,
    obstacles,
    setObstacles,
    activeObstacleName,
    setActiveObstacleName,
    robots,
    setRobots,
    robotColorIndex,
    handleCellClick,
    handleRun,
  }
}
