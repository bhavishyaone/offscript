import React, { useEffect, useState } from 'react'

const LOADING_WORDS = ['Loading...', 'Searching...', 'Fetching...', 'Routing...']

export const LoadingPage: React.FC = () => {
  const [wordIndex, setWordIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % LOADING_WORDS.length)
    }, 3000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="loading-page-container" aria-live="polite">
      <div className="loading-page-content">
        <div className="clean-spinner-large" />
        <div className="clean-loading-word-large">{LOADING_WORDS[wordIndex]}</div>
      </div>
    </div>
  )
}
