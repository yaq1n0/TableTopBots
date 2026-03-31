import { useEffect, useState } from 'react'
import { listConfigs, loadConfig, saveConfig } from '../api'
import type { ConfigFile } from '../api'
import RobotPanel from './RobotPanel'
import InfoBanner from './InfoBanner'

interface Robot {
  name: string
  commands: (string | null)[]
}

interface Props {
  width: number
  height: number
  onWidthChange: (w: number) => void
  onHeightChange: (h: number) => void
  obstacles: Record<string, [number, number][]>
  onObstaclesChange: (obs: Record<string, [number, number][]>) => void
  robots: Robot[]
  onRobotsChange: (robots: Robot[]) => void
  activeObstacleName: string
  onActiveObstacleNameChange: (name: string) => void
}

function clampDimension(value: number): number {
  return Math.min(100, Math.max(5, Math.round(value) || 5))
}

function DimensionInput({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (v: number) => void
}) {
  const [draft, setDraft] = useState(String(value))

  useEffect(() => {
    setDraft(String(value))
  }, [value])

  function commitValue() {
    const clamped = clampDimension(Number(draft))
    onChange(clamped)
    setDraft(String(clamped))
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-gray-300">{label}</label>
        <input
          type="number"
          min={5}
          max={100}
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value)
            const n = Number(e.target.value)
            if (n >= 5 && n <= 100) onChange(n)
          }}
          onBlur={commitValue}
          onKeyDown={(e) => e.key === 'Enter' && commitValue()}
          className="w-14 border border-gray-600 bg-gray-700 text-white rounded px-1.5 py-0.5 text-xs text-center"
        />
      </div>
      <input
        type="range"
        min={5}
        max={100}
        value={value}
        onChange={(e) => {
          const n = Number(e.target.value)
          onChange(n)
          setDraft(String(n))
        }}
        className="w-full accent-blue-500"
      />
    </div>
  )
}

export default function SetupPanel({
  width,
  height,
  onWidthChange,
  onHeightChange,
  obstacles,
  onObstaclesChange,
  robots,
  onRobotsChange,
  activeObstacleName,
  onActiveObstacleNameChange,
}: Props) {
  const [newRobotName, setNewRobotName] = useState('')
  const [newObstacleName, setNewObstacleName] = useState('')
  const [editingObstacleName, setEditingObstacleName] = useState<string | null>(
    null,
  )
  const [configNames, setConfigNames] = useState<string[]>([])
  const [infoMessage, setInfoMessage] = useState<string | null>(null)

  useEffect(() => {
    listConfigs()
      .then(setConfigNames)
      .catch(() => {})
  }, [])

  async function handleLoadConfig(name: string) {
    const config = await loadConfig(name)
    onWidthChange(config.width)
    onHeightChange(config.height)
    onObstaclesChange(config.obstacles)
    onRobotsChange(config.robots)
    onActiveObstacleNameChange('')
    setInfoMessage(`Loaded config "${name}"`)
  }

  async function handleSaveConfig() {
    const name = prompt('Config name:')
    if (!name?.trim()) return
    const config: ConfigFile = {
      width,
      height,
      obstacles,
      robots: robots.map((r) => ({
        name: r.name,
        commands: r.commands.filter((c): c is string => c !== null),
      })),
    }
    await saveConfig(name.trim(), config)
    setConfigNames(await listConfigs())
  }

  // --- Obstacle handlers ---
  const selectedObstacle = activeObstacleName || null

  function addObstacle() {
    const name = newObstacleName.trim()
    if (!name || name in obstacles) return
    onObstaclesChange({ ...obstacles, [name]: [] })
    onActiveObstacleNameChange(name)
    setNewObstacleName('')
  }

  function selectObstacle(name: string) {
    if (activeObstacleName === name) {
      onActiveObstacleNameChange('')
    } else {
      onActiveObstacleNameChange(name)
    }
    setEditingObstacleName(null)
  }

  function startRenameObstacle(name: string) {
    setEditingObstacleName(name)
  }

  function commitRenameObstacle(oldName: string, newName: string) {
    const trimmed = newName.trim()
    setEditingObstacleName(null)
    if (!trimmed || trimmed === oldName) return
    if (trimmed in obstacles) return
    const updated: Record<string, [number, number][]> = {}
    for (const [k, v] of Object.entries(obstacles)) {
      updated[k === oldName ? trimmed : k] = v
    }
    onObstaclesChange(updated)
    if (activeObstacleName === oldName) {
      onActiveObstacleNameChange(trimmed)
    }
  }

  function removeObstacle(name: string) {
    const updated = { ...obstacles }
    delete updated[name]
    onObstaclesChange(updated)
    if (activeObstacleName === name) {
      onActiveObstacleNameChange('')
    }
  }

  // --- Robot handlers ---
  function addRobot() {
    const name = newRobotName.trim()
    if (!name || robots.some((r) => r.name === name)) return
    onRobotsChange([...robots, { name, commands: [] }])
    setNewRobotName('')
  }

  function removeRobot(index: number) {
    onRobotsChange(robots.filter((_, i) => i !== index))
  }

  function updateCommands(index: number, commands: (string | null)[]) {
    const updated = [...robots]
    updated[index] = { ...updated[index], commands }
    onRobotsChange(updated)
  }

  return (
    <div className="space-y-4">
      <InfoBanner message={infoMessage} />
      {/* Save / Load Configurations */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-bold text-gray-200">Configurations</h2>
          <button
            onClick={handleSaveConfig}
            className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
          >
            Save
          </button>
        </div>
        {configNames.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {configNames.map((name) => (
              <button
                key={name}
                onClick={() => handleLoadConfig(name)}
                className="px-2.5 py-1 bg-gray-700 text-gray-200 rounded text-xs hover:bg-gray-600 border border-gray-600"
              >
                {name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Board Configuration */}
      <div>
        <h2 className="text-sm font-bold mb-2 text-gray-200">Board Size</h2>
        <div className="space-y-2">
          <DimensionInput
            label="Width"
            value={width}
            onChange={onWidthChange}
          />
          <DimensionInput
            label="Height"
            value={height}
            onChange={onHeightChange}
          />
        </div>
      </div>

      {/* Obstacles */}
      <div>
        <h2 className="text-sm font-bold mb-2 text-gray-200">Obstacles</h2>
        <div className="flex gap-1.5 mb-2">
          <input
            type="text"
            placeholder="New obstacle name"
            value={newObstacleName}
            onChange={(e) => setNewObstacleName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addObstacle()}
            className="flex-1 border border-gray-600 bg-gray-700 text-white rounded px-2 py-1 text-xs placeholder-gray-400"
          />
          <button
            onClick={addObstacle}
            disabled={
              !newObstacleName.trim() || newObstacleName.trim() in obstacles
            }
            className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
        {Object.entries(obstacles).length > 0 && (
          <div className="space-y-1">
            {Object.entries(obstacles).map(([name, cells]) => {
              const isSelected = selectedObstacle === name
              const isEditing = editingObstacleName === name
              return (
                <div
                  key={name}
                  className={`flex items-center justify-between text-xs rounded px-2 py-1.5 cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-blue-600/30 border border-blue-500'
                      : 'bg-gray-700 border border-transparent hover:bg-gray-600'
                  }`}
                  onClick={() => selectObstacle(name)}
                >
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    {isEditing ? (
                      <input
                        autoFocus
                        defaultValue={name}
                        className="bg-gray-600 text-white rounded px-1 py-0.5 text-xs w-full"
                        onClick={(e) => e.stopPropagation()}
                        onBlur={(e) =>
                          commitRenameObstacle(name, e.target.value)
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter')
                            commitRenameObstacle(name, e.currentTarget.value)
                          if (e.key === 'Escape') setEditingObstacleName(null)
                        }}
                      />
                    ) : (
                      <>
                        <span className="font-medium text-gray-200 truncate">
                          {name}
                        </span>
                        <span className="text-gray-400 flex-shrink-0">
                          {cells.length} cell{cells.length !== 1 ? 's' : ''}
                        </span>
                      </>
                    )}
                  </div>
                  <div className="flex gap-1 flex-shrink-0 ml-1">
                    {isSelected && !isEditing && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          startRenameObstacle(name)
                        }}
                        className="text-gray-400 hover:text-white text-[10px]"
                      >
                        Rename
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        removeObstacle(name)
                      }}
                      className="text-red-400 hover:text-red-300 text-[10px]"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
        {selectedObstacle && (
          <p className="text-[10px] text-blue-400 mt-1">
            Click cells on the grid to toggle "{selectedObstacle}"
          </p>
        )}
      </div>

      {/* Robots */}
      <div>
        <h2 className="text-sm font-bold mb-2 text-gray-200">Robots</h2>
        <div className="flex gap-1.5 mb-2">
          <input
            type="text"
            placeholder="Robot name"
            value={newRobotName}
            onChange={(e) => setNewRobotName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addRobot()}
            className="flex-1 border border-gray-600 bg-gray-700 text-white rounded px-2 py-1 text-xs placeholder-gray-400"
          />
          <button
            onClick={addRobot}
            disabled={
              !newRobotName.trim() ||
              robots.some((r) => r.name === newRobotName.trim())
            }
            className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
        {robots.map((robot, i) => (
          <RobotPanel
            key={robot.name}
            mode="setup"
            name={robot.name}
            commands={robot.commands}
            onCommandsChange={(cmds) => updateCommands(i, cmds)}
            onRemove={() => removeRobot(i)}
          />
        ))}
      </div>
    </div>
  )
}
