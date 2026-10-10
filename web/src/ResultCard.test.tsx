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

  const searchCard = (summary: string | null, summarySource: number | null): CardResponse => ({
    kind: 'card',
    fit: 'ok',
    route: 'SEARCH',
    reason: 'Opening hours change.',
    content: {
      search_query: 'lalbagh open republic day',
      sources: [
        { title: 'Lalbagh timings', url: 'https://www.karnatakatourism.org/lalbagh' },
        { title: 'Flower show', url: 'https://traveltwosome.com/lalbagh' },
      ],
      search_url: 'https://www.google.com/search?q=lalbagh+open+republic+day',
      outdoor_action: 'If it is open, visit during its listed hours.',
      summary,
      summary_source: summarySource,
    },
    request_id: 'req_cite',
    latency_ms: 30,
  })

  const render = (card: CardResponse) =>
    renderToString(
      React.createElement(ResultCard, { card, onGoOffscript: () => {}, onDismiss: () => {} }),
    )

  it('names the site the SEARCH summary relies on', () => {
    const html = render(searchCard('Open 7 AM to 6 PM on Republic Day.', 1))
    expect(html).toContain('According to <!-- -->karnatakatourism.org')
    expect(html).not.toContain('clearly answer')
  })

  it('says so when the results do not clearly answer the question', () => {
    const html = render(searchCard(null, null))
    expect(html).toContain('The results don&#x27;t clearly answer this. Check the sources below.')
    expect(html).not.toContain('According to')
  })
})
