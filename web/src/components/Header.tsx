import React from 'react'

interface HeaderProps {
  version?: string
  isModelConfigured?: boolean
  isMock?: boolean
  onReset?: () => void
  showReset?: boolean
}

export const Header: React.FC<HeaderProps> = ({
  version: _version = '0.1.0',
  isModelConfigured: _isModelConfigured = false,
  isMock = false,
  onReset,
  showReset = false,
}) => {
  return (
    <header className="app-header">
      <div
        className="brand-logo"
        onClick={onReset}
        style={{ cursor: showReset ? 'pointer' : 'default' }}
      >
        <div className="brand-icon">
          <span>O</span>
        </div>
        <div className="brand-meta">
          <h1 className="brand-title">Offscript</h1>
          <span className="brand-tagline">One intention nearby</span>
        </div>
      </div>
      <div className="header-actions">
        {isMock && (
          <div className="health-status-dot mock-badge" title="Mock Mode">
            <span className="dot-indicator" />
            <span className="dot-label">MOCK</span>
          </div>
        )}
        {showReset && onReset && (
          <button className="header-new-btn" onClick={onReset} title="Start new question">
            + New
          </button>
        )}
      </div>
    </header>
  )
}
