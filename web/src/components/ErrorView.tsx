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
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
      }}
    >
      <div style={{ fontSize: '20px', fontWeight: '700', color: '#991b1b' }}>
        ⚠️ Unable to get route
      </div>
      <div style={{ fontSize: '15px', color: '#7f1d1d' }}>{message}</div>
      <button className="submit-btn" onClick={onRetry} style={{ marginTop: '8px' }}>
        Try Again →
      </button>
    </div>
  )
}
