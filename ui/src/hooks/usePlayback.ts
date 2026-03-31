import { useState } from 'react'
import type { SimulationResponse } from '../types'

export function usePlayback() {
  const [response, setResponse] = useState<SimulationResponse | null>(null)
  const [currentTurn, setCurrentTurn] = useState(0)

  const totalTurns = response?.snapshots.length ?? 0
  const currentSnapshot = response?.snapshots[currentTurn]

  function load(res: SimulationResponse) {
    setResponse(res)
    setCurrentTurn(0)
  }

  function reset() {
    setResponse(null)
    setCurrentTurn(0)
  }

  return {
    response,
    currentTurn,
    currentSnapshot,
    totalTurns,
    load,
    reset,
    setTurn: (t: number) => setCurrentTurn(Math.max(0, Math.min(totalTurns - 1, t))),
  }
}
