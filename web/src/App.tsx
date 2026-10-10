import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from './api/health'
import { submitRouteRequest } from './api/client'
import type { RouteResponse } from './types/route'

import { Header } from './components/Header'
import { QuestionForm } from './components/QuestionForm'
import { LoadingPage } from './components/LoadingPage'
import { SuggestionsView } from './components/SuggestionsView'
import { ReportResultPage } from './components/ReportResultPage'

type Screen = 'form' | 'loading' | 'suggestions' | 'report'

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [screen, setScreen] = useState<Screen>('form')
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState<RouteResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [lastQuestion, setLastQuestion] = useState<{ q: string; ctx?: string } | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((h) => setHealth(h))
      .catch(() => setHealth(null))
    return () => controller.abort()
  }, [])

  const handleFormSubmit = async (submittedQuestion: string, context?: string) => {
    setScreen('loading')
    setResponse(null)
    setErrorMessage(null)
    setLastQuestion({ q: submittedQuestion, ctx: context })

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 60000) // 60s timeout per AGENTS.md B7

    try {
      const res: RouteResponse = await submitRouteRequest(
        submittedQuestion,
        context,
        controller.signal,
      )
      clearTimeout(timeoutId)
      setResponse(res)
      setScreen('form')
    } catch (err: unknown) {
      clearTimeout(timeoutId)
      const message =
        err instanceof Error
          ? err.name === 'AbortError'
            ? 'Request timed out after 60 seconds. Please try again.'
            : err.message
          : 'Failed to connect to API.'
      setErrorMessage(message)
      setScreen('form')
    }
  }

  const handleReset = () => {
    setScreen('form')
    setQuestion('')
    setResponse(null)
    setErrorMessage(null)
  }

  return (
    <>
      <Header
        version={health?.version || '0.1.0'}
        isModelConfigured={health?.model_configured ?? false}
        isMock={response?.is_mock ?? false}
        onReset={handleReset}
        showReset={Boolean(response || errorMessage || screen !== 'form')}
      />

      <main className="app-content" aria-live="polite" aria-atomic="true">
        {screen === 'loading' && <LoadingPage />}

        {screen === 'suggestions' && (
          <SuggestionsView
            onSelectSuggestion={(selectedQuestion) => {
              setQuestion(selectedQuestion)
              setScreen('form')
            }}
            onBack={() => setScreen('form')}
          />
        )}

        {screen === 'report' && (
          <ReportResultPage
            response={response ?? undefined}
            onBack={() => setScreen('form')}
            onReset={handleReset}
          />
        )}

        {screen === 'form' && (
          <QuestionForm
            question={question}
            setQuestion={setQuestion}
            onSubmit={handleFormSubmit}
            isLoading={false}
            response={response}
            errorMessage={errorMessage}
            onOpenSuggestions={() => setScreen('suggestions')}
            onOpenReport={() => setScreen('report')}
            onRetry={() => {
              if (lastQuestion) {
                handleFormSubmit(lastQuestion.q, lastQuestion.ctx)
              } else {
                handleReset()
              }
            }}
            onAskAnother={handleReset}
          />
        )}
      </main>

      <footer className="app-footer">Offscript · One intention nearby · Get off the screen</footer>
    </>
  )
}

export default App
