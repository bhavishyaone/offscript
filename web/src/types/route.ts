export type GuardFit =
  'needs_detail' | 'two_questions' | 'safety_guidance' | 'refusal' | 'search_limitation'

export type Fit = 'ok' | GuardFit

export type Route = 'AI' | 'SEARCH' | 'HUMAN'

export interface SearchSource {
  title: string
  url: string
  snippet?: string
}

export interface AiContent {
  answer: string
  outdoor_action: string
}

export interface SearchContent {
  search_query: string
  sources: SearchSource[]
  search_url: string
  outdoor_action: string
  summary?: string | null
  local_tip?: string | null
}

export interface HumanContent {
  who_to_ask: string
  suggested_question: string
  outdoor_action: string
}

export interface CardResponse {
  kind: 'card'
  fit: 'ok'
  route: Route
  reason: string
  content: AiContent | SearchContent | HumanContent
  request_id: string
  latency_ms: number
  is_mock?: boolean
}

export interface GuardResponse {
  kind: 'guard'
  fit: Fit
  route: null
  reason: string
  message: string
  suggested_question?: string
  search_url?: string
  request_id: string
  latency_ms: number
  is_mock?: boolean
}

export interface ErrorResponse {
  error: {
    code: string
    message: string
  }
}

export type RouteResponse = CardResponse | GuardResponse
