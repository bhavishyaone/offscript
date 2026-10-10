import React from 'react'
import type { GuardResponse } from '../types/route'

interface GuardViewProps {
  guard: GuardResponse
  onReset: () => void
}

export const GuardView: React.FC<GuardViewProps> = ({ guard, onReset }) => {
  const { fit, message, reason, search_url } = guard

  const guardMeta: Record<string, { label: string; icon: string; themeClass: string }> = {
    needs_detail: {
      label: 'More Detail Needed',
      icon: '📍',
      themeClass: 'context',
    },
    two_questions: {
      label: 'Two Questions in One',
      icon: '🔀',
      themeClass: 'split',
    },
    safety_guidance: {
      label: 'Safety Guidance',
      icon: '🛡️',
      themeClass: 'safety',
    },
    refusal: {
      label: 'Request Refused',
      icon: '⛔',
      themeClass: 'refusal',
    },
    search_limitation: {
      label: 'Search Limitation',
      icon: '🔍',
      themeClass: 'search-limit',
    },
  }

  const meta = guardMeta[fit] || {
    label: fit,
    icon: 'ℹ️',
    themeClass: 'default',
  }

  return (
    <div className={`guard-container guard-theme-${meta.themeClass}`}>
      <div className="guard-top-row">
        <span className="guard-pill">
          <span>{meta.icon}</span>
          <span>{meta.label}</span>
        </span>
        <span className="guard-policy-tag">Product Boundary</span>
      </div>

      <div className="guard-message">{message}</div>

      <div className="guard-reason-box">
        <span className="reason-label">Reason:</span>
        <span className="reason-text">"{reason}"</span>
      </div>

      {search_url && (
        <div className="guard-search-link-box">
          <p className="guard-search-help">Check public listings directly via search:</p>
          <a
            href={search_url}
            target="_blank"
            rel="noreferrer"
            className="search-action-btn"
            style={{ width: '100%' }}
          >
            🔍 Open External Search Link ↗
          </a>
        </div>
      )}

      <button
        className="submit-btn guard-reset-btn"
        onClick={onReset}
        style={{ marginTop: '16px' }}
      >
        <span>Ask another question →</span>
      </button>
    </div>
  )
}
