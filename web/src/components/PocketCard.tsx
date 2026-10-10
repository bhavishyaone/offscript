import React from 'react'
import type { AiContent, CardResponse, HumanContent, SearchContent } from '../types/route'

interface PocketCardProps {
  card: CardResponse
  onReturn: () => void
}

export const PocketCard: React.FC<PocketCardProps> = ({ card, onReturn }) => {
  const { content, route } = card

  return (
    <div className="pocket-wrapper">
      {/* Outdoor HUD Status Header */}
      <div className="pocket-header-row">
        <div className="pocket-badge">
          <span className="pocket-dot" />
          <span>⚡ Offscript Active</span>
        </div>
        <div className="pocket-offline-tag">
          <span>📶 Offline Ready</span>
        </div>
      </div>

      {/* Target Step: Bold & Sun-readable */}
      <div className="pocket-action-card">
        <div className="pocket-action-title">Outdoor Action</div>
        <div className="pocket-action-text">{content.outdoor_action}</div>
      </div>

      {/* Route Specific Pocket Helper */}
      {route === 'AI' && (
        <div className="pocket-details-card">
          <div className="block-title">💡 Know how takeaway</div>
          <div className="pocket-knowhow-body">{(content as AiContent).answer}</div>
        </div>
      )}

      {route === 'SEARCH' && (
        <div className="pocket-details-card">
          <div className="block-title">🔍 Quick Web Search</div>
          <a
            href={(content as SearchContent).search_url}
            target="_blank"
            rel="noreferrer"
            className="search-action-btn pocket-search-btn"
          >
            ↗ Check {(content as SearchContent).search_query}
          </a>
        </div>
      )}

      {route === 'HUMAN' && (
        <div className="pocket-details-card">
          <div className="block-title">👤 Ask this person</div>
          <div className="pocket-person-type">{(content as HumanContent).who_to_ask}</div>
          <div className="human-question-box pocket-question-box">
            💬 "{(content as HumanContent).suggested_question}"
          </div>
          <div className="pocket-fallback-note">
            ℹ️ If no one suitable is available, try later or skip.
          </div>
        </div>
      )}

      {/* Return to App Action */}
      <div className="pocket-return-section">
        <button className="submit-btn pocket-back-btn" onClick={onReturn}>
          <span>I'm back (Report Result) →</span>
        </button>
        <span className="pocket-footnote">Screen stayed asleep while you were out</span>
      </div>
    </div>
  )
}
