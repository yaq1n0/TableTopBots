import type { RobotState } from '../types'

const ROBOT_COLORS = [
  'bg-blue-500',
  'bg-red-500',
  'bg-green-500',
  'bg-purple-500',
  'bg-orange-500',
  'bg-pink-500',
  'bg-teal-500',
  'bg-yellow-500',
]

const DIRECTION_ARROWS: Record<string, string> = {
  NORTH: '\u2191',
  SOUTH: '\u2193',
  EAST: '\u2192',
  WEST: '\u2190',
}

interface Props {
  width: number
  height: number
  robots: RobotState[]
  obstacles: Record<string, [number, number][]>
  robotColorIndex: Record<string, number>
  onCellClick?: (x: number, y: number) => void
}

export default function BoardGrid({
  width,
  height,
  robots,
  obstacles,
  robotColorIndex,
  onCellClick,
}: Props) {
  const obstacleMap = new Map<string, string>()
  for (const [name, cells] of Object.entries(obstacles)) {
    for (const [x, y] of cells) {
      obstacleMap.set(`${x},${y}`, name)
    }
  }

  const robotMap = new Map<string, RobotState>()
  for (const r of robots) {
    if (r.placed) {
      robotMap.set(`${r.x},${r.y}`, r)
    }
  }

  return (
    <div
      className="border border-gray-400 grid"
      style={{
        gridTemplateColumns: `repeat(${width}, 1fr)`,
        gridTemplateRows: `repeat(${height}, 1fr)`,
        aspectRatio: `${width} / ${height}`,
        width: '100%',
        maxHeight: '100%',
      }}
    >
      {Array.from({ length: height }, (_, ri) => {
        const y = height - 1 - ri
        return Array.from({ length: width }, (_, x) => {
          const key = `${x},${y}`
          const obstacle = obstacleMap.get(key)
          const robot = robotMap.get(key)

          return (
            <div
              key={key}
              className={`border border-gray-300 flex flex-col items-center justify-center overflow-hidden relative ${
                obstacle ? 'bg-gray-400' : 'bg-white'
              } ${onCellClick ? 'cursor-pointer hover:bg-gray-100' : ''}`}
              onClick={() => onCellClick?.(x, y)}
            >
              {obstacle && (
                <span className="text-gray-700 font-medium text-[8px] leading-none truncate max-w-full px-0.5">
                  {obstacle}
                </span>
              )}
              {robot && (
                <div
                  className={`${
                    ROBOT_COLORS[robotColorIndex[robot.name] % ROBOT_COLORS.length]
                  } rounded-full w-3/4 aspect-square flex flex-col items-center justify-center text-white`}
                >
                  <span className="text-[7px] font-bold leading-none truncate max-w-full">
                    {robot.name}
                  </span>
                  <span className="text-[10px] leading-none">
                    {DIRECTION_ARROWS[robot.facing]}
                  </span>
                </div>
              )}
            </div>
          )
        })
      })}
    </div>
  )
}
