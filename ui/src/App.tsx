import { useState } from 'react'
import { useSetup } from './hooks/useSetup'
import { usePlayback } from './hooks/usePlayback'
import BoardGrid from './components/BoardGrid'
import SetupPanel from './components/SetupPanel'
import RobotPanel from './components/RobotPanel'
import Timeline from './components/Timeline'
import ErrorBanner from './components/ErrorBanner'

type Phase = 'setup' | 'run'

export default function App() {
  const [phase, setPhase] = useState<Phase>('setup')
  const [error, setError] = useState<string | null>(null)

  const playback = usePlayback()

  const setup = useSetup((res) => {
    playback.load(res)
    setPhase('run')
    setError(null)
  }, setError)

  function handleReset() {
    playback.reset()
    setPhase('setup')
    setError(null)
  }

  const canRun =
    setup.robots.length > 0 && setup.robots.every((r) => r.commands.length > 0)
  const displayRobots = playback.currentSnapshot?.robots ?? []

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b bg-white flex-shrink-0">
        <div className="w-24">
          {phase === 'run' && (
            <button
              onClick={handleReset}
              className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-100"
            >
              &larr; Back
            </button>
          )}
        </div>
        <h1 className="text-xl font-bold text-gray-800">Toy Robot Simulator</h1>
        <div className="w-24 flex justify-end">
          {phase === 'setup' && (
            <button
              onClick={setup.handleRun}
              disabled={!canRun}
              className="px-3 py-1.5 text-sm font-semibold text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Simulate
            </button>
          )}
        </div>
      </div>

      <ErrorBanner message={error} />

      {/* Main content */}
      <div className="flex-1 flex gap-6 px-6 py-4 min-h-0 overflow-hidden">
        {/* Left: Grid area */}
        <div className="flex-1 flex flex-col min-h-0 min-w-0">
          {phase === 'run' && (
            <div className="flex-shrink-0 mb-3">
              <Timeline
                currentTurn={playback.currentTurn}
                totalTurns={playback.totalTurns}
                onChange={(t) => playback.setTurn(t)}
              />
            </div>
          )}
          <div className="flex-1 flex items-center justify-center min-h-0">
            <BoardGrid
              width={setup.width}
              height={setup.height}
              robots={displayRobots}
              obstacles={setup.obstacles}
              robotColorIndex={setup.robotColorIndex}
              onCellClick={
                phase === 'setup' ? setup.handleCellClick : undefined
              }
            />
          </div>
        </div>

        {/* Right: Sidebar */}
        <div className="w-80 flex-shrink-0 overflow-y-auto">
          {phase === 'setup' ? (
            <SetupPanel
              width={setup.width}
              height={setup.height}
              onWidthChange={setup.setWidth}
              onHeightChange={setup.setHeight}
              obstacles={setup.obstacles}
              onObstaclesChange={setup.setObstacles}
              robots={setup.robots}
              onRobotsChange={setup.setRobots}
              activeObstacleName={setup.activeObstacleName}
              onActiveObstacleNameChange={setup.setActiveObstacleName}
            />
          ) : (
            <div className="space-y-4">
              <h2 className="text-lg font-bold">
                Turn {playback.currentTurn} Results
              </h2>
              {setup.robots.map((robot) => {
                const result = playback.currentSnapshot?.results.find(
                  (r) => r.robot_name === robot.name,
                )
                return (
                  <RobotPanel
                    key={robot.name}
                    mode="run"
                    name={robot.name}
                    result={result}
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
