import React, { useState } from 'react'

interface ReturnViewProps {
  onComplete: (didIt: boolean, note?: string) => void
}

export const ReturnView: React.FC<ReturnViewProps> = ({ onComplete }) => {
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
    onComplete(didIt, note.trim() || undefined)
  }

  return (
    <div className="card-container">
      <div className="hero-section">
        <div className="hero-pill">
          <span>📍 Return & Reflect</span>
        </div>
        <h2 className="hero-title">How did your offscript step go?</h2>
        <p className="hero-subtitle">
          Log an honest self-report. This is stored only in your browser.
        </p>
      </div>

      {!submitted ? (
        <div className="return-card-content">
          <div className="form-group">
            <div className="form-label-row">
              <label htmlFor="note-input" className="form-label">
                What did you find? <span className="form-label-subtle">(optional note)</span>
              </label>
              <span className="char-counter">{note.length}/150</span>
            </div>
            <input
              id="note-input"
              type="text"
              className="form-input"
              placeholder="e.g. Regulars were friendly! Next round started in 10 mins."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={150}
            />
          </div>

          <div className="return-actions-grid">
            <button className="return-choice-btn success-btn" onClick={() => handleAction(true)}>
              <span className="choice-emoji">🎉</span>
              <span className="choice-title">I did it!</span>
              <span className="choice-sub">Completed physical step</span>
            </button>

            <button className="return-choice-btn couldn-btn" onClick={() => handleAction(false)}>
              <span className="choice-emoji">🌧️</span>
              <span className="choice-title">Couldn't do it</span>
              <span className="choice-sub">Conditions or timing blocked it</span>
            </button>
          </div>

          <div className="privacy-badge-banner" style={{ marginTop: '16px' }}>
            <span className="privacy-icon">🔒</span>
            <span>Self-report only • Never uploaded or synced anywhere</span>
          </div>
        </div>
      ) : (
        <div className="card-block return-completed-card">
          <div className="return-success-badge">
            <span>{lastChoice ? '🎉 Mission Completed' : '🌧️ Self-Report Logged'}</span>
          </div>
          <h3 className="return-success-title">
            {lastChoice
              ? 'Awesome job getting off the screen!'
              : 'Honest report saved. Every attempt counts.'}
          </h3>
          <p className="return-success-desc">
            Your self-report has been saved locally. Take a breath and ask another question when you
            are ready.
          </p>
        </div>
      )}
    </div>
  )
}
