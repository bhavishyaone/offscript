import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from './api/health'
import { submitRouteRequest } from './api/client'
import type { CardResponse, GuardResponse, RouteResponse } from './types/route'

import { Header } from './components/Header'
import { QuestionForm } from './components/QuestionForm'
import { ResultCard } from './components/ResultCard'
import { PocketCard } from './components/PocketCard'
import { ReturnView } from './components/ReturnView'
import { GuardView } from './components/GuardView'
import { ErrorView } from './components/ErrorView'

type AppState =
  | { type: 'idle' }
  | { type: 'loading' }
  | { type: 'card'; response: CardResponse }
  | { type: 'guard'; response: GuardResponse }
  | { type: 'error'; message: string }
  | { type: 'pocket'; response: CardResponse }
  | { type: 'return'; response: CardResponse }

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [state, setState] = useState<AppState>({ type: 'idle' })
  const [lastQuestion, setLastQuestion] = useState<{ q: string; ctx?: string } | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((h) => setHealth(h))
      .catch(() => setHealth(null))
    return () => controller.abort()
  }, [])

  const handleFormSubmit = async (question: string, context?: string) => {
    setState({ type: 'loading' })
    setLastQuestion({ q: question, ctx: context })

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 60000) // 60s timeout per AGENTS.md B7

    try {
      const res: RouteResponse = await submitRouteRequest(question, context, controller.signal)
      clearTimeout(timeoutId)

      if (res.kind === 'card') {
        setState({ type: 'card', response: res })
      } else {
        setState({ type: 'guard', response: res })
      }
    } catch (err: unknown) {
      clearTimeout(timeoutId)
      const message =
        err instanceof Error
          ? err.name === 'AbortError'
            ? 'Request timed out after 60 seconds. Please try again.'
            : err.message
          : 'Failed to connect to API.'
      setState({ type: 'error', message })
    }
  }

  const handleReset = () => {
    setState({ type: 'idle' })
  }

  return (
    <>
      <Header
        version={health?.version || '0.1.0'}
        isModelConfigured={health?.model_configured ?? false}
        isMock={
          state.type === 'card'
            ? !!state.response.is_mock
            : state.type === 'guard'
              ? !!state.response.is_mock
              : false
        }
        onReset={handleReset}
        showReset={state.type !== 'idle' && state.type !== 'loading'}
      />

      <main className="app-content" aria-live="polite" aria-atomic="true">
        {state.type === 'idle' && <QuestionForm onSubmit={handleFormSubmit} isLoading={false} />}

        {state.type === 'loading' && (
          <div className="loading-box">
            <div className="radar-spinner">
              <div className="radar-circle" />
              <div className="radar-core" />
            </div>
            <div className="loading-text">Finding best physical route...</div>
            <div className="loading-steps">
              <span className="step-item active">⚡ Practical know-how</span>
              <span className="step-separator">•</span>
              <span className="step-item active">🔍 Public listings</span>
              <span className="step-separator">•</span>
              <span className="step-item active">👥 Local norms</span>
            </div>
          </div>
        )}

        {state.type === 'card' && (
          <ResultCard
            card={state.response}
            onGoOffscript={() => setState({ type: 'pocket', response: state.response })}
            onDismiss={handleReset}
          />
        )}

        {state.type === 'pocket' && (
          <PocketCard
            card={state.response}
            onReturn={() => setState({ type: 'return', response: state.response })}
          />
        )}

        {state.type === 'return' && (
          <ReturnView
            onComplete={() => {
              // Return completed
            }}
          />
        )}

        {state.type === 'guard' && <GuardView guard={state.response} onReset={handleReset} />}

        {state.type === 'error' && (
          <ErrorView
            message={state.message}
            onRetry={() => {
              if (lastQuestion) {
                handleFormSubmit(lastQuestion.q, lastQuestion.ctx)
              } else {
                handleReset()
              }
            }}
          />
        )}

        {(state.type === 'return' || state.type === 'guard') && (
          <button
            className="btn-secondary restart-btn"
            onClick={handleReset}
            style={{ marginTop: '20px' }}
          >
            ← Ask another question
          </button>
        )}
      </main>

      <footer className="app-footer">Offscript · One intention nearby · Get off the screen</footer>
    </>
  )
}

export default App
