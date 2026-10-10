import React from 'react'
import type {
  AiContent,
  CardResponse,
  HumanContent,
  RouteResponse,
  SearchContent,
} from '../types/route'

interface InlineAnswerProps {
  response: RouteResponse
  onOpenReport?: () => void
  onAskAnother?: () => void
}

export const InlineAnswer: React.FC<InlineAnswerProps> = ({
  response,
  onOpenReport,
  onAskAnother,
}) => {
  if (response.kind === 'guard') {
    return (
      <div className="inline-answer-box guard-answer-box">
        {response.is_mock && <span className="mock-badge">MOCK</span>}
        <div className="inline-answer-text">{response.message}</div>
        {response.reason && (
          <div className="guard-reason-box" style={{ marginTop: '8px' }}>
            <span className="reason-label">Reason:</span> {response.reason}
          </div>
        )}
        {response.search_url && (
          <a
            href={response.search_url}
            target="_blank"
            rel="noreferrer"
            className="search-action-btn"
            style={{ marginTop: '10px' }}
          >
            🔍 Check public search ↗
          </a>
        )}
        {onAskAnother && (
          <button type="button" className="btn-ask-another" onClick={onAskAnother}>
            ← Ask another question
          </button>
        )}
      </div>
    )
  }

  const { route, content } = response

  if (route === 'AI') {
    const ai = content as AiContent
    return (
      <div className="inline-answer-box ai-answer-box">
        {response.is_mock && <span className="mock-badge">MOCK</span>}
        <div className="inline-answer-text">{ai.answer}</div>
        {ai.outdoor_action && (
          <div className="inline-action-card">
            <span className="inline-action-tag">Outdoor Action</span>
            <span className="inline-action-desc">{ai.outdoor_action}</span>
          </div>
        )}
        <div className="inline-answer-actions">
          {onOpenReport && (
            <button type="button" className="inline-report-toggle-btn" onClick={onOpenReport}>
              <span>I'm back (Report Result) →</span>
            </button>
          )}
          {onAskAnother && (
            <button type="button" className="btn-ask-another" onClick={onAskAnother}>
              ← Ask another question
            </button>
          )}
        </div>
      </div>
    )
  }

  if (route === 'SEARCH') {
    const search = content as SearchContent
    return (
      <div className="inline-answer-box search-answer-box">
        {response.is_mock && <span className="mock-badge">MOCK</span>}
        {search.summary && <div className="inline-answer-text">{search.summary}</div>}
        <a
          href={search.search_url}
          target="_blank"
          rel="noreferrer"
          className="search-action-btn"
          style={{ marginTop: '10px' }}
        >
          🔍 Search: {search.search_query} ↗
        </a>
        {search.sources && search.sources.length > 0 && (
          <div className="inline-sources-list">
            {search.sources.map((s, idx) => (
              <a key={idx} href={s.url} target="_blank" rel="noreferrer" className="source-item">
                • {s.title}
              </a>
            ))}
          </div>
        )}
        {search.outdoor_action && (
          <div className="inline-action-card">
            <span className="inline-action-tag">Outdoor Action</span>
            <span className="inline-action-desc">{search.outdoor_action}</span>
          </div>
        )}
        <div className="inline-answer-actions">
          {onOpenReport && (
            <button type="button" className="inline-report-toggle-btn" onClick={onOpenReport}>
              <span>I'm back (Report Result) →</span>
            </button>
          )}
          {onAskAnother && (
            <button type="button" className="btn-ask-another" onClick={onAskAnother}>
              ← Ask another question
            </button>
          )}
        </div>
      </div>
    )
  }

  if (route === 'HUMAN') {
    const human = content as HumanContent
    return (
      <div className="inline-answer-box human-answer-box">
        {response.is_mock && <span className="mock-badge">MOCK</span>}
        <div className="inline-human-ask">
          <span className="human-icon">👤</span>
          <span>Ask {human.who_to_ask}:</span>
        </div>
        <div className="inline-human-quote">“{human.suggested_question}”</div>
        {human.outdoor_action && (
          <div className="inline-action-card">
            <span className="inline-action-tag">Outdoor Action</span>
            <span className="inline-action-desc">{human.outdoor_action}</span>
          </div>
        )}
        <div className="inline-answer-actions">
          {onOpenReport && (
            <button type="button" className="inline-report-toggle-btn" onClick={onOpenReport}>
              <span>I'm back (Report Result) →</span>
            </button>
          )}
          {onAskAnother && (
            <button type="button" className="btn-ask-another" onClick={onAskAnother}>
              ← Ask another question
            </button>
          )}
        </div>
      </div>
    )
  }

  return null
}

interface QuestionFormProps {
  question?: string
  setQuestion?: (q: string) => void
  onSubmit: (question: string, context?: string) => void
  isLoading?: boolean
  response?: RouteResponse | null
  errorMessage?: string | null
  onRetry?: () => void
  onGoOffscript?: (card: CardResponse) => void
  onOpenSuggestions?: () => void
  onOpenReport?: () => void
  onAskAnother?: () => void
}

export const QuestionForm: React.FC<QuestionFormProps> = ({
  question: externalQuestion,
  setQuestion: externalSetQuestion,
  onSubmit,
  isLoading = false,
  response,
  errorMessage,
  onRetry,
  onOpenSuggestions,
  onOpenReport,
  onAskAnother,
}) => {
  const [internalQuestion, setInternalQuestion] = React.useState('')
  const question = externalQuestion !== undefined ? externalQuestion : internalQuestion
  const setQuestion = externalSetQuestion !== undefined ? externalSetQuestion : setInternalQuestion

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return
    onSubmit(question.trim())
  }

  const clearQuestion = () => setQuestion('')

  const handleAskAnother = () => {
    setQuestion('')
    onAskAnother?.()
  }

  return (
    <div className="question-form-container">
      <div className="hero-section">
        <h2 className="hero-title">The answer is out there. Get moving.</h2>
        <p className="hero-subtitle">
          Ask normally. Tell us where you are or plan to go if it matters.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="question-form">
        <div className="form-group">
          <div className="form-label-row">
            <label htmlFor="question-input" className="form-label">
              What do you want to do or find out nearby?
            </label>
            <span className={`char-counter ${question.length >= 280 ? 'warn' : ''}`}>
              {question.length}/300
            </span>
          </div>
          <div className="input-wrapper">
            <textarea
              id="question-input"
              className="form-textarea"
              placeholder="e.g. How do I join a casual pickup game at the court?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isLoading}
              required
              maxLength={300}
              rows={3}
            />
            {question.length > 0 && (
              <button
                type="button"
                className="input-clear-btn"
                onClick={clearQuestion}
                aria-label="Clear question"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <button type="submit" className="submit-btn" disabled={isLoading || !question.trim()}>
          {isLoading ? (
            <span className="btn-loading-content">
              <span className="spinner-inline" /> Routing intention...
            </span>
          ) : (
            <span>Offscript it →</span>
          )}
        </button>
      </form>

      {/* Quick Suggestions Trigger: Subtle, professional entry */}
      {!isLoading && !response && onOpenSuggestions && (
        <div className="quick-suggestions-bar">
          <button type="button" className="quick-suggestions-btn" onClick={onOpenSuggestions}>
            <span className="sparkle-icon">✨</span>
            <span>Quick suggestions</span>
            <span className="arrow-icon">→</span>
          </button>
        </div>
      )}

      {/* Inline Answer rendered below Offscript it button */}
      {!isLoading && response && (
        <InlineAnswer
          response={response}
          onOpenReport={onOpenReport}
          onAskAnother={handleAskAnother}
        />
      )}

      {/* Inline Error rendered below Offscript it button */}
      {!isLoading && errorMessage && (
        <div className="inline-error-box">
          <div className="inline-error-text">{errorMessage}</div>
          {onRetry && (
            <button type="button" className="inline-retry-btn" onClick={onRetry}>
              Try again
            </button>
          )}
        </div>
      )}
    </div>
  )
}
