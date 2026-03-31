import createClient from 'openapi-fetch'
import type { components, paths } from './generated/api'

export type SimulationRequest = components['schemas']['SimulationRequest']
export type SimulationResponse = components['schemas']['SimulationResponse']
export type ValidationResponse = components['schemas']['ValidationResponse']
export type ParseFileResponse = components['schemas']['ParseFileResponse']

const client = createClient<paths>({ baseUrl: 'http://localhost:8000' })

export async function simulate(
  request: SimulationRequest,
): Promise<SimulationResponse> {
  const { data, error } = await client.POST('/simulate', { body: request })
  if (error) throw new Error('Simulation failed')
  return data
}

export async function validateCommand(
  command: string,
): Promise<ValidationResponse> {
  const { data, error } = await client.POST('/validate', {
    body: { command },
  })
  if (error) throw new Error('Validation request failed')
  return data
}

export async function parseFile(file: File): Promise<string[]> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('http://localhost:8000/parse-file', {
    method: 'POST',
    body: form,
  })
  const data: ParseFileResponse = await res.json()
  return data.commands
}

// --- Config files ---

export type ConfigFile = components['schemas']['ConfigFile']

export async function listConfigs(): Promise<string[]> {
  const { data, error } = await client.GET('/data/configs')
  if (error) throw new Error('Failed to list configs')
  return data.files
}

export async function loadConfig(name: string): Promise<ConfigFile> {
  const { data, error } = await client.GET('/data/configs/{name}', {
    params: { path: { name } },
  })
  if (error) throw new Error('Failed to load config')
  return data as ConfigFile
}

export async function saveConfig(
  name: string,
  config: ConfigFile,
): Promise<void> {
  const { error } = await client.POST('/data/configs/{name}', {
    params: { path: { name } },
    body: config,
  })
  if (error) throw new Error('Failed to save config')
}

// --- Instruction files ---

export async function listInstructions(): Promise<string[]> {
  const { data, error } = await client.GET('/data/instructions')
  if (error) throw new Error('Failed to list instructions')
  return data.files
}

export async function loadInstructions(name: string): Promise<string[]> {
  const { data, error } = await client.GET('/data/instructions/{name}', {
    params: { path: { name } },
  })
  if (error) throw new Error('Failed to load instructions')
  return data.commands
}

export async function saveInstructions(
  name: string,
  commands: string[],
): Promise<void> {
  const { error } = await client.POST('/data/instructions/{name}', {
    params: { path: { name } },
    body: { commands },
  })
  if (error) throw new Error('Failed to save instructions')
}
