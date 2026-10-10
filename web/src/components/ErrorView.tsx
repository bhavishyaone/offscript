import React from 'react'

interface ErrorViewProps {
  message: string
  onRetry: () => void
}

export const ErrorView: React.FC<ErrorViewProps> = ({ message, onRetry }) => {
  return (
    <div
      className="card-container"
      style={{
        backgroundColor: 'rgba(239, 68, 68, 0.12)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
      }}
    >
      <div style={{ fontSize: '20px', fontWeight: '700', color: '#f87171' }}>
        ⚠️ Unable to get route
      </div>
      <div style={{ fontSize: '15px', color: '#cbd5e1' }}>{message}</div>
      <button className="submit-btn" onClick={onRetry} style={{ marginTop: '8px' }}>
        Try Again →
      </button>
    </div>
  )
}
