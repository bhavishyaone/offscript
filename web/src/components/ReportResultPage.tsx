import React, { useState } from 'react'
import type { RouteResponse } from '../types/route'

interface ReportResultPageProps {
  response?: RouteResponse
  onBack: () => void
  onReset: () => void
}

export const ReportResultPage: React.FC<ReportResultPageProps> = ({ onBack, onReset }) => {
  const [note, setNote] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [lastChoice, setLastChoice] = useState<boolean | null>(null)

  const handleAction = (didIt: boolean) => {
    try {
      const history = JSON.parse(localStorage.getItem('offscript_history') || '[]')
      history.push({
        timestamp: new Date().toISOString(),
        completed: didIt,
        note: note.trim() || undefined,
      })
      localStorage.setItem('offscript_history', JSON.stringify(history))
    } catch (e) {
      console.error('Failed to save self-report to localStorage', e)
    }
    setLastChoice(didIt)
    setSubmitted(true)
  }

  return (
    <div className="report-page-container">
      <div className="report-top-nav">
        <button type="button" className="report-back-btn" onClick={onBack}>
          ← Back to answer
        </button>
      </div>

      <div className="report-header">
        <h2 className="report-title">Report & Result</h2>
        <p className="report-subtitle">
          How did your offscript step go? Log an honest self-report.
        </p>
      </div>

      {/* Self-Report Section */}
      <div className="report-form-card">
        {!submitted ? (
          <>
            <div className="form-group">
              <label htmlFor="report-note-input" className="form-label">
                What did you find? <span className="form-label-subtle">(optional note)</span>
              </label>
              <input
                id="report-note-input"
                type="text"
                className="form-input"
                placeholder="e.g. Regulars were friendly! Started in 10 mins."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                maxLength={150}
              />
            </div>

            <div className="report-choices-grid">
              <button
                type="button"
                className="return-choice-btn success-btn"
                onClick={() => handleAction(true)}
              >
                <span className="choice-emoji">🎉</span>
                <span className="choice-title">I did it!</span>
                <span className="choice-sub">Completed physical step</span>
              </button>

              <button
                type="button"
                className="return-choice-btn couldn-btn"
                onClick={() => handleAction(false)}
              >
                <span className="choice-emoji">🌧️</span>
                <span className="choice-title">Couldn't do it</span>
                <span className="choice-sub">Timing or conditions blocked it</span>
              </button>
            </div>
          </>
        ) : (
          <div className="report-completed-section">
            <div className="return-success-badge">
              <span>{lastChoice ? '🎉 Mission Completed' : '🌧️ Self-Report Logged'}</span>
            </div>
            <h3 className="return-success-title">
              {lastChoice
                ? 'Awesome job getting off the screen!'
                : 'Honest report saved. Every attempt counts.'}
            </h3>
            <p className="return-success-desc">
              Your self-report has been saved locally. Take a breath and ask another question when
              ready.
            </p>
            <button
              type="button"
              className="submit-btn restart-action-btn"
              onClick={onReset}
              style={{ marginTop: '16px' }}
            >
              ← Ask another question
            </button>
          </div>
        )}
      </div>

      {!submitted && (
        <button
          type="button"
          className="btn-secondary restart-btn"
          onClick={onReset}
          style={{ marginTop: '8px' }}
        >
          ← Ask another question
        </button>
      )}
    </div>
  )
}
