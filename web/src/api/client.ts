import type { RouteResponse } from '../types/route'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export async function submitRouteRequest(
  question: string,
  context?: string,
  signal?: AbortSignal,
): Promise<RouteResponse> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        context: context && context.trim() ? context.trim() : undefined,
      }),
      signal,
    })
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err
    }
    if (err instanceof Error && err.name === 'AbortError') {
      throw err
    }
    throw new Error(
      'Network error: Unable to reach the Offscript server. Please check your connection.',
    )
  }

  let data: Record<string, unknown> | null = null
  const text = await response.text()
  if (text) {
    try {
      data = JSON.parse(text) as Record<string, unknown>
    } catch {
      // Non-JSON response (e.g. gateway error HTML)
    }
  }

  if (!response.ok) {
    const errorObj = data?.error as { code?: string; message?: string } | undefined
    const errorMsg =
      errorObj?.message ||
      (response.status === 429
        ? 'Too many requests. Please wait a moment and try again.'
        : response.status === 504
          ? 'Upstream service timed out. Please try again.'
          : response.status === 503
            ? 'Model or checkpoint is currently unavailable. Please try again shortly.'
            : response.status === 502
              ? 'Upstream service error. Please try again.'
              : `Request failed (HTTP ${response.status})`)
    throw new Error(errorMsg)
  }

  if (!data || typeof data !== 'object') {
    throw new Error('Invalid response received from server.')
  }

  return data as unknown as RouteResponse
}
