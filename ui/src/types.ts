// Re-export generated types so components can import from a single stable location.
// The source of truth is src/generated/api.d.ts (generated from the FastAPI OpenAPI schema).
// Run `npm run openapi:generate` to refresh after backend model changes.
import type { components } from './generated/api'

export type Direction = components['schemas']['Direction']
export type Command =
  | components['schemas']['PlaceCommand']
  | components['schemas']['MoveCommand']
  | components['schemas']['LeftCommand']
  | components['schemas']['RightCommand']
  | components['schemas']['ReportCommand']
export type RobotState = components['schemas']['RobotState']
export type CommandResult = components['schemas']['CommandResult']
export type Snapshot = components['schemas']['Snapshot']
export type SimulationRequest = components['schemas']['SimulationRequest']
export type SimulationResponse = components['schemas']['SimulationResponse']
export type ConfigFile = components['schemas']['ConfigFile']
export type ConfigRobot = components['schemas']['ConfigRobot']
