import { useEffect, useRef, useState } from 'react'
import type { CommandResult } from '../types'
import { isValidCommand } from '../validation'
import {
  parseFile,
  listInstructions,
  loadInstructions,
  saveInstructions,
} from '../api'
import InfoBanner from './InfoBanner'

interface SetupProps {
  mode: 'setup'
  name: string
  commands: (string | null)[]
  onCommandsChange: (commands: (string | null)[]) => void
  onRemove: () => void
}

interface RunProps {
  mode: 'run'
  name: string
  result: CommandResult | undefined
}

type Props = SetupProps | RunProps

function RobotPanelRun({ name, result }: RunProps) {
  return (
    <div className="border rounded p-3 mb-2">
      <h3 className="font-bold text-sm mb-1">{name}</h3>
      {result ? (
        <div className="text-sm">
          <p>
            <span className="font-medium">Command: </span>
            {result.command
              ? result.command.type +
                (result.command.type === 'PLACE'
                  ? ` ${result.command.x},${result.command.y},${result.command.facing}`
                  : result.command.type !== 'REPORT' && result.command.count > 1
                    ? ` ${result.command.count}`
                    : '')
              : 'none'}
          </p>
          <p>
            <span
              className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium ${
                result.executed
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {result.executed ? 'Executed' : 'Blocked'}
            </span>
          </p>
          {result.reason && (
            <p className="text-gray-500 text-xs mt-0.5">{result.reason}</p>
          )}
          {result.output && (
            <p className="font-mono bg-gray-100 px-2 py-1 rounded mt-1 text-xs">
              Output: {result.output}
            </p>
          )}
        </div>
      ) : (
        <p className="text-sm text-gray-400">No result</p>
      )}
    </div>
  )
}

function RobotPanelSetup({
  name,
  commands,
  onCommandsChange,
  onRemove,
}: SetupProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Use local draft text so the textarea preserves whitespace/newlines while typing.
  // Only sync trimmed, non-empty commands to the parent on change.
  const commandsJoined = commands
    .filter((c): c is string => c !== null)
    .join('\n')
  const [draft, setDraft] = useState(commandsJoined)
  const [instructionFiles, setInstructionFiles] = useState<string[]>([])
  const [infoMessage, setInfoMessage] = useState<string | null>(null)

  useEffect(() => {
    listInstructions()
      .then(setInstructionFiles)
      .catch(() => {})
  }, [])

  // Sync draft when commands change externally (e.g. file import)
  useEffect(() => {
    setDraft(commandsJoined)
  }, [commandsJoined])

  async function handleLoadInstructions(fileName: string) {
    const cmds = await loadInstructions(fileName)
    onCommandsChange(cmds)
    setInfoMessage(`Loaded "${fileName}"`)
  }

  async function handleSaveInstructions() {
    const fileName = prompt('Instructions file name:')
    if (!fileName?.trim()) return
    const cmds = commands.filter((c): c is string => c !== null)
    if (cmds.length === 0) return
    await saveInstructions(fileName.trim(), cmds)
    setInstructionFiles(await listInstructions())
  }

  function handleTextChange(text: string) {
    setDraft(text)
    const lines = text
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0)
    onCommandsChange(lines.length > 0 ? lines : [])
  }

  function handleValidation(text: string): string | null {
    const lines = text.split('\n').filter((l) => l.trim().length > 0)
    for (const line of lines) {
      if (!isValidCommand(line.trim())) {
        return `Invalid command: "${line.trim()}"`
      }
    }
    return null
  }

  async function handleImport() {
    fileInputRef.current?.click()
  }

  async function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const cmds = await parseFile(file)
    onCommandsChange(cmds)
    setInfoMessage(`Loaded "${file.name}"`)
    e.target.value = ''
  }

  const validationError = draft.trim() ? handleValidation(draft) : null

  return (
    <div className="border rounded p-3 mb-2">
      <InfoBanner message={infoMessage} />
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-bold text-sm">{name}</h3>
        <div className="flex gap-1">
          <button
            onClick={handleSaveInstructions}
            className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
          >
            Save
          </button>
          <button
            onClick={handleImport}
            className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
          >
            Import File
          </button>
          <button
            onClick={onRemove}
            className="text-xs px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded"
          >
            Remove
          </button>
        </div>
      </div>
      {instructionFiles.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {instructionFiles.map((f) => (
            <button
              key={f}
              onClick={() => handleLoadInstructions(f)}
              className="px-2 py-0.5 bg-gray-700 text-gray-200 rounded text-xs hover:bg-gray-600 border border-gray-600"
            >
              {f}
            </button>
          ))}
        </div>
      )}
      <textarea
        className="w-full h-28 border rounded p-2 text-sm font-mono resize-y"
        placeholder="One command per line, e.g.&#10;PLACE 0,0,NORTH&#10;MOVE&#10;REPORT"
        value={draft}
        onChange={(e) => handleTextChange(e.target.value)}
      />
      {validationError && (
        <p className="text-red-500 text-xs mt-1">{validationError}</p>
      )}
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt"
        className="hidden"
        onChange={handleFileSelected}
      />
    </div>
  )
}

export default function RobotPanel(props: Props) {
  if (props.mode === 'run') {
    return <RobotPanelRun {...props} />
  }
  return <RobotPanelSetup {...props} />
}
