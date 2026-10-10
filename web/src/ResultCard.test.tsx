import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import React from 'react'
import { ResultCard } from './components/ResultCard'
import type { CardResponse } from './types/route'

describe('ResultCard AI and SEARCH actions (Task A03)', () => {
  it('renders AI know-how answer and physical step', () => {
    const aiCard: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'AI',
      reason: 'Stable know-how for joining something.',
      content: {
        answer: 'Wait for a pause between games, approach politely, and ask to join next.',
        outdoor_action: 'Walk up to the court side and wait for the game to pause.',
      },
      request_id: 'req_123',
      latency_ms: 15,
    }

    const html = renderToString(
      React.createElement(ResultCard, {
        card: aiCard,
        onGoOffscript: () => {},
        onDismiss: () => {},
      }),
    )

    expect(html).toContain('AI / Know how')
    expect(html).toContain('Wait for a pause between games')
    expect(html).toContain('Walk up to the court side')
    expect(html).toContain('Go offscript')
  })

  it('renders SEARCH with web-search action link and honest status when no sources', () => {
    const searchCard: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'SEARCH',
      reason: 'Fresh public schedule required.',
      content: {
        search_query: 'public run club near campus',
        sources: [],
        search_url: 'https://www.google.com/search?q=public+run+club+near+campus',
        outdoor_action: 'Open search link to check schedule, then head to the start point.',
      },
      request_id: 'req_456',
      latency_ms: 22,
    }

    const html = renderToString(
      React.createElement(ResultCard, {
        card: searchCard,
        onGoOffscript: () => {},
        onDismiss: () => {},
      }),
    )

    expect(html).toContain('SEARCH / Find where or when')
    expect(html).toContain('public run club near campus')
    expect(html).toContain('Open Web Search ↗')
    expect(html).toContain('https://www.google.com/search?q=public+run+club+near+campus')
    expect(html).toContain('Direct web search action ready')
  })

  it('renders SEARCH with grounded sources when available', () => {
    const searchCardWithSources: CardResponse = {
      kind: 'card',
      fit: 'ok',
      route: 'SEARCH',
      reason: 'Fresh public schedule required.',
      content: {
        search_query: 'campus museum hours',
        sources: [{ title: 'Campus Museum Hours & Admission', url: 'https://museum.edu/hours' }],
        search_url: 'https://www.google.com/search?q=campus+museum+hours',
        outdoor_action: 'Head to the main hall entrance during open hours.',
        summary: 'According to Campus Museum Hours & Admission, open 10am to 5pm.',
        local_tip: 'Quietest on weekday mornings.',
      },
      request_id: 'req_789',
      latency_ms: 30,
    }

    const html = renderToString(
      React.createElement(ResultCard, {
        card: searchCardWithSources,
        onGoOffscript: () => {},
        onDismiss: () => {},
      }),
    )

    expect(html).toContain('Campus Museum Hours &amp; Admission')
    expect(html).toContain('https://museum.edu/hours')
    expect(html).toContain('According to Campus Museum Hours')
    expect(html).toContain('Quietest on weekday mornings.')
    expect(html).toContain('Open Web Search ↗')
  })
})
