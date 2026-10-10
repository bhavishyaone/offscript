import React from 'react'
import type { CardResponse, AiContent, SearchContent, HumanContent } from '../types/route'

interface ResultCardProps {
  card: CardResponse
  onGoOffscript: () => void
  onDismiss: () => void
}

export const ResultCard: React.FC<ResultCardProps> = ({ card, onGoOffscript, onDismiss }) => {
  const { route, reason, content } = card

  const routeConfig: Record<string, { label: string; icon: string; description: string }> = {
    AI: {
      label: 'AI / Know how',
      icon: '💡',
      description: 'Stable practical know-how',
    },
    SEARCH: {
      label: 'SEARCH / Find where or when',
      icon: '🔍',
      description: 'Public listing & schedule',
    },
    HUMAN: {
      label: 'HUMAN / Ask someone',
      icon: '👥',
      description: 'Local tacit knowledge',
    },
  }

  const currentRoute = routeConfig[route] || {
    label: route,
    icon: '⚡',
    description: 'Routing decision',
  }

  return (
    <div className="card-container">
      {/* Route Header Badge Row */}
      <div className="route-badge-row">
        <div className={`route-pill ${route}`}>
          <span className="route-pill-icon">{currentRoute.icon}</span>
          <span className="route-pill-text">{currentRoute.label}</span>
          {card.is_mock && <span className="mock-badge">MOCK</span>}
        </div>
        <div className="card-latency-chip">
          <span>⚡ {card.latency_ms}ms</span>
        </div>
      </div>

      {/* Editorial Route Reason */}
      <div className="route-reason-card">
        <span className="reason-quote-mark">“</span>
        <p className="route-reason-text">{reason}</p>
      </div>

      {/* Route Specific Content */}
      {route === 'AI' && (
        <div className="card-block ai-block">
          <div className="block-title">
            <span className="block-icon">💡</span> Know how
          </div>
          <div className="block-body know-how-text">{(content as AiContent).answer}</div>
        </div>
      )}

      {route === 'SEARCH' && (
        <div className="card-block search-block">
          <div className="block-title">
            <span className="block-icon">🔍</span> Public details
          </div>
          <div className="search-query-container">
            <span className="search-query-label">Search query:</span>
            <div className="search-query-chip">
              <strong>{(content as SearchContent).search_query}</strong>
            </div>
          </div>

          {(content as SearchContent).summary && (
            <div className="search-summary-container">
              <div className="search-summary-text">{(content as SearchContent).summary}</div>
              {(content as SearchContent).local_tip && (
                <div className="search-local-tip">
                  💡 <em>{(content as SearchContent).local_tip}</em>
                </div>
              )}
            </div>
          )}

          {(content as SearchContent).sources && (content as SearchContent).sources.length > 0 ? (
            <div className="sources-container">
              <span className="sources-label">Grounded results:</span>
              <div className="source-links">
                {(content as SearchContent).sources.map((src, i) => (
                  <a
                    key={i}
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    className="source-link"
                  >
                    ↗ {src.title}
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <div className="search-unverified-note">
              <span className="note-icon">ℹ️</span>
              <span>Direct web search action ready. Confirm live hours & listings below:</span>
            </div>
          )}

          {(content as SearchContent).search_url && (
            <a
              href={(content as SearchContent).search_url}
              target="_blank"
              rel="noreferrer"
              className="search-action-btn"
            >
              🔍 Open Web Search ↗
            </a>
          )}
        </div>
      )}

      {route === 'HUMAN' && (
        <div className="card-block human-block">
          <div className="block-title">
            <span className="block-icon">👤</span> Person to ask
          </div>
          <div className="human-target-badge">
            <span className="avatar-icon">🧑</span>
            <span className="who-to-ask-text">{(content as HumanContent).who_to_ask}</span>
          </div>
          <div className="human-question-box">
            <div className="question-bubble-header">Suggested spoken question:</div>
            <div className="question-bubble-text">
              “{(content as HumanContent).suggested_question}”
            </div>
          </div>
        </div>
      )}

      {/* Target Physical Step: Outdoor Action */}
      <div className="do-this-block">
        <div className="do-this-header">
          <span className="do-this-badge">🎯 Outdoor Action</span>
          <span className="do-this-subtitle">Follow your goal</span>
        </div>
        <div className="do-this-body">{content.outdoor_action}</div>
      </div>

      {/* Mobile Ergonomic Action Dock */}
      <div className="card-actions">
        <button className="submit-btn offscript-primary-btn" onClick={onGoOffscript}>
          Go offscript →
        </button>
        <button className="btn-secondary not-now-btn" onClick={onDismiss}>
          Not now
        </button>
      </div>
    </div>
  )
}
