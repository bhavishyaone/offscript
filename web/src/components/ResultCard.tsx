import React from 'react'
import type { CardResponse, AiContent, SearchContent, HumanContent } from '../types/route'

// The site the search summary relies on, e.g. "karnatakatourism.org", or null if unknown.
function citedSite(content: SearchContent): string | null {
  const source = content.summary_source ? content.sources[content.summary_source - 1] : undefined
  if (!source) return null
  try {
    return new URL(source.url).hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}

interface ResultCardProps {
  card: CardResponse
  onGoOffscript: () => void
  onDismiss: () => void
}

export const ResultCard: React.FC<ResultCardProps> = ({ card, onGoOffscript, onDismiss }) => {
  const { route, reason, content } = card

  return (
    <div className="card-container">
      {card.is_mock && (
        <div className="route-badge-row">
          <span className="mock-badge">MOCK</span>
        </div>
      )}

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
              {citedSite(content as SearchContent) && (
                <div className="search-summary-source">
                  According to {citedSite(content as SearchContent)}
                </div>
              )}
              {(content as SearchContent).local_tip && (
                <div className="search-local-tip">
                  💡 <em>{(content as SearchContent).local_tip}</em>
                </div>
              )}
            </div>
          )}

          {!(content as SearchContent).summary &&
            (content as SearchContent).sources &&
            (content as SearchContent).sources.length > 0 && (
              <div className="search-unverified-note">
                <span className="note-icon">ℹ️</span>
                <span>The results don't clearly answer this. Check the sources below.</span>
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
