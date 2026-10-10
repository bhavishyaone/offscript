import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderToString } from 'react-dom/server'
import React from 'react'
import { Header } from './components/Header'
import { QuestionForm } from './components/QuestionForm'
import { SuggestionsView } from './components/SuggestionsView'
import { LoadingPage } from './components/LoadingPage'
import { ReportResultPage } from './components/ReportResultPage'
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
      expect(html).toContain('MOCK')
    })

    it('does not render Live label when isMock is false', () => {
      const html = renderToString(
        React.createElement(Header, {
          version: '0.1.0',
          isModelConfigured: false,
          isMock: false,
        }),
      )
      expect(html).toContain('Offscript')
      expect(html).not.toContain('Live')
      expect(html).not.toContain('MOCK')
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
    it('renders hero title and form inputs without examples', () => {
      const html = renderToString(
        React.createElement(QuestionForm, {
          onSubmit: () => {},
          isLoading: false,
          onOpenSuggestions: () => {},
        }),
      )
      expect(html).toContain('The answer is out there. Get moving.')
      expect(html).toContain('What do you want to do or find out nearby?')
      expect(html).toContain('Offscript it →')
      expect(html).toContain('Quick suggestions')
    })

    it('renders clean loading page with spinner and progressive light text', () => {
      const html = renderToString(React.createElement(LoadingPage))
      expect(html).toContain('loading-page-container')
      expect(html).toContain('Loading...')
      expect(html).toContain('clean-spinner-large')
    })

    it('renders suggestions view with 5 curated questions covering diverse routes', () => {
      const suggestionsHtml = renderToString(
        React.createElement(SuggestionsView, {
          onSelectSuggestion: () => {},
          onBack: () => {},
        }),
      )
      expect(suggestionsHtml).toContain('Quick Suggestions')
      expect(suggestionsHtml).toContain('How do beginners join games at this outdoor court?')
      expect(suggestionsHtml).toContain('Where do students here actually eat between classes?')
      expect(suggestionsHtml).toContain('How do I start birdwatching in the park this afternoon?')
      expect(suggestionsHtml).toContain('Where is a public run club meeting near campus this week?')
      expect(suggestionsHtml).toContain('What is this campus club like week to week?')
    })

    it('renders report result page with self-report choices and without answer box or lock banner', () => {
      const html = renderToString(
        React.createElement(ReportResultPage, {
          onBack: () => {},
          onReset: () => {},
        }),
      )
      expect(html).toContain('Report &amp; Result')
      expect(html).toContain('How did your offscript step go?')
      expect(html).toContain('I did it!')
      expect(html).toContain('t do it')
      expect(html).toContain('← Ask another question')
      expect(html).not.toContain('report-answer-summary-box')
      expect(html).not.toContain('privacy-badge-banner')
    })

    it('renders AI answer directly below the button in a single unified card without two tabs', () => {
      const aiResponse: CardResponse = {
        kind: 'card',
        fit: 'ok',
        route: 'AI',
        reason: 'General knowledge about photography',
        content: {
          answer: 'Start with golden hour lighting just before sunset.',
          outdoor_action: 'Head outside with your camera at 5 PM.',
        },
        request_id: 'req_ai_test',
        latency_ms: 15,
      }

      const html = renderToString(
        React.createElement(QuestionForm, {
          onSubmit: () => {},
          isLoading: false,
          response: aiResponse,
          onOpenReport: () => {},
        }),
      )
      expect(html).toContain('Start with golden hour lighting just before sunset.')
      expect(html).toContain('Outdoor Action')
      expect(html).toContain('Head outside with your camera at 5 PM.')
      expect(html).toContain('inline-answer-box')
      expect(html).toContain('Report Result')
      // Ensure the old separate quote card is not rendered
      expect(html).not.toContain('route-reason-card')
    })

    it('renders HUMAN answer directly below the button', () => {
      const humanResponse: CardResponse = {
        kind: 'card',
        fit: 'ok',
        route: 'HUMAN',
        reason: 'Local norm',
        content: {
          who_to_ask: 'The court coordinator',
          suggested_question: 'Can beginners join the pickup games today?',
          outdoor_action: 'Walk over to the court bench.',
        },
        request_id: 'req_human_test',
        latency_ms: 20,
      }

      const html = renderToString(
        React.createElement(QuestionForm, {
          onSubmit: () => {},
          isLoading: false,
          response: humanResponse,
        }),
      )
      expect(html).toContain('The court coordinator')
      expect(html).toContain('Can beginners join the pickup games today?')
      expect(html).toContain('Outdoor Action')
      expect(html).toContain('← Ask another question')
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
