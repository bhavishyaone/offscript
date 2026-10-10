import React from 'react'

interface HeaderProps {
  version?: string
  isModelConfigured?: boolean
  isMock?: boolean
  onReset?: () => void
  showReset?: boolean
}

export const Header: React.FC<HeaderProps> = ({
  version = '0.1.0',
  isModelConfigured = false,
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
        <div
          className="health-status-dot"
          title={isMock ? 'Mock Mode' : isModelConfigured ? 'Model Ready' : 'Live'}
        >
          <span className="dot-indicator" />
          <span className="dot-label">
            {isMock ? 'Mock' : 'Live'} v{version}
          </span>
        </div>
        {showReset && onReset && (
          <button className="header-new-btn" onClick={onReset} title="Start new question">
            + New
          </button>
        )}
      </div>
    </header>
  )
}
