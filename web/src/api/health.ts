// Hand-written until contract types are generated into src/contract/generated (AGENTS.md B5).
export type HealthResponse = {
  ok: boolean
  version: string
  model_configured: boolean
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, { signal })
  if (!response.ok) throw new Error(`Health check failed: HTTP ${response.status}`)
  return (await response.json()) as HealthResponse
}
