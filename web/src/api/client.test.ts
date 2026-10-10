import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { submitRouteRequest } from './client'
import type { CardResponse, GuardResponse } from '../types/route'

describe('submitRouteRequest API client (Task A06)', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('sends correct HTTP POST payload with question and trimmed context', async () => {
    const mockResponse: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'AI',
      reason: 'Know-how route',
      content: {
        answer: 'Take a step forward and introduce yourself.',
        outdoor_action: 'Approach the court and ask.',
      },
      request_id: 'req_test1',
      latency_ms: 12,
    }

    let capturedUrl = ''
    let capturedOptions: RequestInit | undefined

    globalThis.fetch = vi.fn().mockImplementation(async (url: string, options?: RequestInit) => {
      capturedUrl = url
      capturedOptions = options
      return {
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as unknown as Response
    })

    const result = await submitRouteRequest('How do I join?', ' campus court ')

    expect(capturedUrl).toContain('/api/route')
    expect(capturedOptions?.method).toBe('POST')
    expect(capturedOptions?.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(JSON.parse(capturedOptions?.body as string)).toEqual({
      question: 'How do I join?',
      context: 'campus court',
    })
    expect(result).toEqual(mockResponse)
  })

  it('omits context when context is empty or whitespace', async () => {
    const mockResponse: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'AI',
      reason: 'Know-how route',
      content: {
        answer: 'Answer',
        outdoor_action: 'Do this',
      },
      request_id: 'req_test2',
      latency_ms: 10,
    }

    let capturedBody = ''
    globalThis.fetch = vi.fn().mockImplementation(async (_url: string, options?: RequestInit) => {
      capturedBody = options?.body as string
      return {
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as unknown as Response
    })

    await submitRouteRequest('How do I join?', '   ')
    expect(JSON.parse(capturedBody)).toEqual({
      question: 'How do I join?',
    })
  })

  it('successfully returns SEARCH route card with search query and sources', async () => {
    const searchResponse: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'SEARCH',
      reason: 'Fresh public schedule required.',
      content: {
        search_query: 'public run club near campus',
        sources: [{ title: 'Campus Running Club', url: 'https://example.com' }],
        search_url: 'https://www.google.com/search?q=public+run+club',
        outdoor_action: 'Check the start location on the listing and arrive 5 mins early.',
      },
      request_id: 'req_search',
      latency_ms: 18,
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(searchResponse),
    } as unknown as Response)

    const res = await submitRouteRequest('Where is a run club?')
    expect(res.kind).toBe('card')
    if (res.kind === 'card') {
      expect(res.route).toBe('SEARCH')
      expect(res.content).toHaveProperty('search_query')
      expect(res.content).toHaveProperty('sources')
    }
  })

  it('successfully returns HUMAN route card with who_to_ask and suggested_question', async () => {
    const humanResponse: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'HUMAN',
      reason: 'Tacit knowledge held by a local person.',
      content: {
        who_to_ask: 'The vendor, when free',
        suggested_question: 'What do your regulars usually come back for?',
        outdoor_action: 'Walk to the stall and wait for a pause.',
      },
      request_id: 'req_human',
      latency_ms: 15,
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(humanResponse),
    } as unknown as Response)

    const res = await submitRouteRequest('What do regulars buy?')
    expect(res.kind).toBe('card')
    if (res.kind === 'card') {
      expect(res.route).toBe('HUMAN')
      expect(res.content).toHaveProperty('who_to_ask')
      expect(res.content).toHaveProperty('suggested_question')
    }
  })

  it('successfully returns GuardResponse (needs_detail, search_limitation)', async () => {
    const guardResponse: GuardResponse = {
      kind: 'guard',
      fit: 'needs_detail',
      route: null,
      reason: 'Essential detail is missing.',
      message: 'Which campus are you referring to?',
      request_id: 'req_guard',
      latency_ms: 8,
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(guardResponse),
    } as unknown as Response)

    const res = await submitRouteRequest('Where is a good cafe?')
    expect(res.kind).toBe('guard')
    if (res.kind === 'guard') {
      expect(res.fit).toBe('needs_detail')
      expect(res.route).toBeNull()
      expect(res.message).toContain('Which campus')
    }
  })

  it('handles HTTP 422 input validation error with structured message', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      text: async () =>
        JSON.stringify({
          error: {
            code: 'question_empty',
            message: 'Please enter a question.',
          },
        }),
    } as unknown as Response)

    await expect(submitRouteRequest('')).rejects.toThrow('Please enter a question.')
  })

  it('handles HTTP 429 rate limit with friendly error', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      text: async () => JSON.stringify({}),
    } as unknown as Response)

    await expect(submitRouteRequest('Too fast?')).rejects.toThrow(
      'Too many requests. Please wait a moment and try again.',
    )
  })

  it('handles HTTP 504 timeout with informative error', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 504,
      text: async () => JSON.stringify({}),
    } as unknown as Response)

    await expect(submitRouteRequest('Timed out?')).rejects.toThrow(
      'Upstream service timed out. Please try again.',
    )
  })

  it('handles non-JSON error response from proxy or gateway (e.g. 502 HTML)', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      text: async () => '<html><body>502 Bad Gateway</body></html>',
    } as unknown as Response)

    await expect(submitRouteRequest('Gateway error?')).rejects.toThrow(
      'Upstream service error. Please try again.',
    )
  })

  it('handles network disconnect gracefully', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(submitRouteRequest('Network down?')).rejects.toThrow(
      'Network error: Unable to reach the Offscript server.',
    )
  })

  it('propagates AbortError when AbortSignal triggers timeout', async () => {
    const controller = new AbortController()
    controller.abort()

    globalThis.fetch = vi
      .fn()
      .mockRejectedValue(new DOMException('The user aborted a request.', 'AbortError'))

    await expect(submitRouteRequest('Aborted?', undefined, controller.signal)).rejects.toThrow(
      'The user aborted a request.',
    )
  })
})
