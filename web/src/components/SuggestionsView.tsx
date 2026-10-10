import React from 'react'

interface SuggestionItem {
  id: string
  question: string
  category: string
}

const SUGGESTED_QUESTIONS: SuggestionItem[] = [
  {
    id: 's1',
    question: 'How do beginners join games at this outdoor court?',
    category: 'Local Norm',
  },
  {
    id: 's2',
    question: 'Where do students here actually eat between classes?',
    category: 'Local Spot',
  },
  {
    id: 's3',
    question: 'How do I start birdwatching in the park this afternoon?',
    category: 'Know-how',
  },
  {
    id: 's4',
    question: 'Where is a public run club meeting near campus this week?',
    category: 'Live Search',
  },
  {
    id: 's5',
    question: 'What is this campus club like week to week?',
    category: 'Firsthand',
  },
]

interface SuggestionsViewProps {
  onSelectSuggestion: (question: string) => void
  onBack: () => void
}

export const SuggestionsView: React.FC<SuggestionsViewProps> = ({ onSelectSuggestion, onBack }) => {
  return (
    <div className="suggestions-view-container">
      <div className="suggestions-top-nav">
        <button type="button" className="suggestions-back-btn" onClick={onBack}>
          ← Back to question
        </button>
      </div>

      <div className="suggestions-header">
        <h2 className="suggestions-title">Quick Suggestions</h2>
        <p className="suggestions-subtitle">
          Tap any question to explore nearby intentions, or customize it.
        </p>
      </div>

      <div className="suggestions-list">
        {SUGGESTED_QUESTIONS.map((item) => (
          <button
            key={item.id}
            type="button"
            className="suggestion-card"
            onClick={() => onSelectSuggestion(item.question)}
          >
            <div className="suggestion-card-header">
              <span className="suggestion-category-tag">{item.category}</span>
              <span className="suggestion-arrow">→</span>
            </div>
            <div className="suggestion-card-text">{item.question}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
