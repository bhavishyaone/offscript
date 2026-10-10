import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderToString } from 'react-dom/server'
import React from 'react'
import { Header } from './components/Header'
import { QuestionForm } from './components/QuestionForm'
import { PocketCard } from './components/PocketCard'
import { GuardView } from './components/GuardView'
import { ErrorView } from './components/ErrorView'
import { ReturnView } from './components/ReturnView'
import type { CardResponse, GuardResponse } from './types/route'

describe('Frontend Component & View Integrations (Task A06)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  describe('Header component', () => {
    it('renders Mock label only when isMock is true', () => {
      const html = renderToString(
        React.createElement(Header, {
          version: '0.1.0',
          isModelConfigured: false,
          isMock: true,
        }),
      )
      expect(html).toContain('Offscript')
      expect(html).toContain('Mock')
      expect(html).toContain('0.1.0')
    })

    it('renders Live label when isMock is false even if model_configured is false', () => {
      const html = renderToString(
        React.createElement(Header, {
          version: '0.1.0',
          isModelConfigured: false,
          isMock: false,
        }),
      )
      expect(html).toContain('Live')
      expect(html).toContain('0.1.0')
    })

    it('renders Live label when model_configured is true', () => {
      const html = renderToString(
        React.createElement(Header, {
          version: '0.2.0',
          isModelConfigured: true,
        }),
      )
      expect(html).toContain('Live')
      expect(html).toContain('0.2.0')
    })

    it('renders + New button when showReset is true', () => {
      const html = renderToString(
        React.createElement(Header, {
          version: '0.1.0',
          isModelConfigured: true,
          showReset: true,
          onReset: () => {},
        }),
      )
      expect(html).toContain('+ New')
    })
  })

  describe('QuestionForm component', () => {
    it('renders hero title and canonical examples with HUMAN prominence', () => {
      const html = renderToString(
        React.createElement(QuestionForm, {
          onSubmit: () => {},
          isLoading: false,
        }),
      )
      expect(html).toContain('The answer is out there. Get moving.')
      expect(html).toContain('What do you want to do or find out nearby?')
      expect(html).toContain('What do regulars buy at this market stall?')
      expect(html).toContain('What is this college club actually like before I go to its meeting?')
      expect(html).toContain('Where is a public run club meeting near campus this week?')
      expect(html).toContain('How do I join a casual pickup game at the court?')
      expect(html).toContain('No GPS tracking')
    })
  })

  describe('PocketCard component', () => {
    it('renders target step and offline-ready indicator for AI card', () => {
      const aiCard: CardResponse = {
        kind: 'card',
        fit: 'ok',
        route: 'AI',
        reason: 'Know-how',
        content: {
          answer: 'Wait for game break and ask.',
          outdoor_action: 'Approach court and wait for timeout.',
        },
        request_id: 'req_1',
        latency_ms: 10,
      }

      const html = renderToString(
        React.createElement(PocketCard, {
          card: aiCard,
          onReturn: () => {},
        }),
      )
      expect(html).toContain('Offline Ready')
      expect(html).toContain('Approach court and wait for timeout.')
      expect(html).toContain('Wait for game break and ask.')
      expect(html).toContain('back (Report Result)')
    })

    it('renders who_to_ask and suggested question with fallback note for HUMAN route', () => {
      const humanCard: CardResponse = {
        kind: 'card',
        fit: 'ok',
        route: 'HUMAN',
        reason: 'Local norm',
        content: {
          who_to_ask: 'The court coordinator or regular players',
          suggested_question: 'Do you run a list or just call next?',
          outdoor_action: 'Walk over between games and ask the coordinator.',
        },
        request_id: 'req_2',
        latency_ms: 12,
      }

      const html = renderToString(
        React.createElement(PocketCard, {
          card: humanCard,
          onReturn: () => {},
        }),
      )
      expect(html).toContain('The court coordinator or regular players')
      expect(html).toContain('Do you run a list or just call next?')
      expect(html).toContain('If no one suitable is available, try later or skip.')
    })
  })

  describe('GuardView component', () => {
    it('renders needs_detail message and ask another question button', () => {
      const guard: GuardResponse = {
        kind: 'guard',
        fit: 'needs_detail',
        route: null,
        reason: 'Essential detail is missing',
        message: 'Which campus are you referring to?',
        request_id: 'req_3',
        latency_ms: 5,
      }

      const html = renderToString(
        React.createElement(GuardView, {
          guard,
          onReset: () => {},
        }),
      )
      expect(html).toContain('More Detail Needed')
      expect(html).toContain('Which campus are you referring to?')
      expect(html).toContain('Essential detail is missing')
      expect(html).toContain('Ask another question')
    })

    it('renders search_limitation with fallback search link', () => {
      const guard: GuardResponse = {
        kind: 'guard',
        fit: 'search_limitation',
        route: null,
        reason: 'Search results conflicting',
        message: 'Could not verify listing.',
        search_url: 'https://www.google.com/search?q=open+hours',
        request_id: 'req_4',
        latency_ms: 6,
      }

      const html = renderToString(
        React.createElement(GuardView, {
          guard,
          onReset: () => {},
        }),
      )
      expect(html).toContain('Search Limitation')
      expect(html).toContain('Open External Search Link')
      expect(html).toContain('https://www.google.com/search?q=open+hours')
    })
  })

  describe('ErrorView component', () => {
    it('renders error message and retry button', () => {
      const html = renderToString(
        React.createElement(ErrorView, {
          message: 'Unable to connect to the server.',
          onRetry: () => {},
        }),
      )
      expect(html).toContain('Unable to get route')
      expect(html).toContain('Unable to connect to the server.')
      expect(html).toContain('Try Again')
    })
  })

  describe('ReturnView component', () => {
    it('renders self-report actions and privacy banner', () => {
      const html = renderToString(
        React.createElement(ReturnView, {
          onComplete: () => {},
        }),
      )
      expect(html).toContain('How did your offscript step go?')
      expect(html).toContain('I did it!')
      expect(html).toContain('t do it')
      expect(html).toContain('Self-report only')
    })
  })
})
