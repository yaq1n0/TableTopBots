const PLACE_RE = /^PLACE\s+\d+\s*,\s*\d+\s*,\s*(NORTH|SOUTH|EAST|WEST)$/i
const MOVE_RE = /^MOVE(?:\s+\d+)?$/i
const LEFT_RE = /^LEFT(?:\s+\d+)?$/i
const RIGHT_RE = /^RIGHT(?:\s+\d+)?$/i
const REPORT_RE = /^REPORT$/i

export function isValidCommand(command: string): boolean {
  const s = command.trim()
  return (
    PLACE_RE.test(s) ||
    MOVE_RE.test(s) ||
    LEFT_RE.test(s) ||
    RIGHT_RE.test(s) ||
    REPORT_RE.test(s)
  )
}
