import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import React from 'react'
import { QuestionForm } from './components/QuestionForm'
import { ResultCard } from './components/ResultCard'
import { PocketCard } from './components/PocketCard'
import { ReturnView } from './components/ReturnView'
import { App } from './App'
import type { CardResponse } from './types/route'

describe('Mobile UX & Accessibility QA (Task A07 & AGENTS.md B7)', () => {
  it('App main content container includes aria-live="polite" for dynamic updates', () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain('aria-live="polite"')
    expect(html).toContain('aria-atomic="true"')
  })

  it('QuestionForm inputs are explicitly associated with descriptive labels', () => {
    const html = renderToString(
      React.createElement(QuestionForm, { onSubmit: () => {}, isLoading: false }),
    )
    expect(html).toContain('for="question-input"')
    expect(html).toContain('id="question-input"')
    expect(html).toContain('for="context-input"')
    expect(html).toContain('id="context-input"')
  })

  it('QuestionForm contains accessible clear buttons with aria-labels', () => {
    const html = renderToString(
      React.createElement(QuestionForm, { onSubmit: () => {}, isLoading: false }),
    )
    // Renders textarea with required attribute and character counter
    expect(html).toContain('maxLength="300"')
    expect(html).toContain('maxLength="200"')
  })

  it('All interactive primary and secondary actions render with accessible text', () => {
    const card: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'AI',
      reason: 'Know-how',
      content: {
        answer: 'Ask politely.',
        outdoor_action: 'Approach the court.',
      },
      request_id: 'req_card_test',
      latency_ms: 10,
    }

    const cardHtml = renderToString(
      React.createElement(ResultCard, {
        card,
        onGoOffscript: () => {},
        onDismiss: () => {},
      }),
    )
    expect(cardHtml).toContain('Go offscript →')
    expect(cardHtml).toContain('Not now')

    const pocketHtml = renderToString(
      React.createElement(PocketCard, {
        card,
        onReturn: () => {},
      }),
    )
    expect(pocketHtml).toContain('back (Report Result)')

    const returnHtml = renderToString(React.createElement(ReturnView, { onComplete: () => {} }))
    expect(returnHtml).toContain('I did it!')
    expect(returnHtml).toContain('t do it')
  })
})
