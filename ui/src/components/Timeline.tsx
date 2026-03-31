interface Props {
  currentTurn: number
  totalTurns: number
  onChange: (turn: number) => void
}

export default function Timeline({
  currentTurn,
  totalTurns,
  onChange,
}: Props) {
  const maxTurn = totalTurns - 1

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-gray-800 rounded-lg">
      <span className="text-xs font-medium text-gray-400 whitespace-nowrap">
        Turn
      </span>
      <input
        type="range"
        min={0}
        max={maxTurn}
        value={currentTurn}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 accent-blue-500 h-2 cursor-pointer"
      />
      <span className="text-xs font-mono text-gray-300 whitespace-nowrap min-w-[4ch] text-right">
        {currentTurn}/{maxTurn}
      </span>
    </div>
  )
}
