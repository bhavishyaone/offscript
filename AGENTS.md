# AGENTS.md: Offscript

Read this fully before planning or writing code. It applies to every person and every coding agent on this repo.

# Part A: Product

## A0. Spec sources

- **Feature List (F01–F36)** defines what the product has.
- **S01 Product Behavior v2.0** guides behaviour, **except** its physical-world-only scope (sections 2, 3 and 11) and its field-card lines ("Only out there", "Do this"). Its routing rules (§6), safety and privacy (§7) and base-vs-tuned comparison (§9) still apply.
- These documents are shared by the team and are not in the repo yet. If this file and those documents disagree, ask before building.

## A1. What Offscript is

- Offscript is a mobile-first web app. The user asks **any question**, plus optional typed context (area, situation, intent). There is **no GPS**.
- A fine-tuned open-weight model (`Qwen/Qwen3.5-9B` on Tinker) picks **one** source and writes that route's content:
  - `AI`: answer it directly.
  - `SEARCH`: look it up on the live web (SerpApi) and show sources.
  - `HUMAN`: ask a real person nearby. One type of person plus one natural question.
- The app shows **one result**, with a one-sentence reason for the chosen source.
- One request in, one response out. No chat.
- HUMAN is the signature route: it encourages the user to leave the screen and talk to someone (F20, "Go offscript").

## A2. Routes

There are exactly three route labels. Never add a fourth.

| Route | Use when the question needs... | Feature List |
|---|---|---|
| `AI` | Stable, general, non-time-sensitive knowledge a model can answer directly | F06 |
| `SEARCH` | Current or publicly verifiable information: opening hours, recent results, events, rankings, business information | F07 |
| `HUMAN` | Firsthand, local, lived, tacit or personal experience, or a real person's permission, that generic AI output or online rankings can't reliably give | F08 |

**Rules** (S01 §6, F10, F12):
- Choose by the **source of the missing knowledge**, not by keywords. "How", "best", "nearby" and "ask" decide nothing on their own.
- Use the user's intent and context to tell similar questions apart (F10).
- **Never:**
  - Route to HUMAN just because the wording is subjective.
  - Route to HUMAN because search failed.
  - Turn model uncertainty into a HUMAN referral.
  - Let AI guess live facts: today's hours, live conditions, recent scores or changing local information. Those go to SEARCH (F12).

**Boundary pairs:**

| Question | Route | Why |
|---|---|---|
| "What is photosynthesis?" | `AI` | Stable knowledge |
| "Who won yesterday's match?" | `SEARCH` | Recent result |
| "Which cafe is highest-rated?" | `SEARCH` | Public ranking (F10) |
| "Where do students here actually eat?" | `HUMAN` | Local lived preference (F10) |
| "How do I ask to join any pickup game?" | `AI` | Generic etiquette |
| "How do beginners join games at this court?" (while there) | `HUMAN` | Local norm |
| "Is the museum open today?" | `SEARCH` | Live opening hours |

## A3. The result

Every result has the **route** and a one-sentence **reason** (F09), plus the route's fields (F31):

| Route | Fields | Rules |
|---|---|---|
| `AI` | `answer` | Concise, written by the fine-tuned model. No live facts (F11, F12) |
| `SEARCH` | `search_query`, `sources`, `search_url` | The model writes the query. The backend runs SerpApi, shows source titles and original links, and a short summary **only** where the results support it (F13–F15). Fallback search link on failure (F16) |
| `HUMAN` | `who_to_ask`, `suggested_question` | One **type** of person, never a specific or present individual (F17). One short, respectful question, under 20 words (F18). The reason says what firsthand knowledge adds (F19) |

- **HUMAN results** end with a clear step away from the screen ("Go offscript"), and the user can skip without pressure (F20). Optional "I asked" / "Skip" feedback is stored only in the browser (F21).
- **"Ask another question"** is available after every result (F04).
- **`outdoor_action`** is one concrete, optional step outside related to the question (conditional for SEARCH), **or `null` when no real-world step genuinely helps** (for example a cover letter or an exchange rate). The key is always present. The UI hides the step section when it is `null`, and keeps "Go offscript" on every HUMAN result. The current v1 checkpoint always returns a step; v2 learns when to leave it out. Card layout is the frontend team's call; S01's "Only out there" line is not used.

## A4. Guards (no result card)

| Guard | When | Decided by |
|---|---|---|
| `safety_guidance` | Medical, mental-health, legal, emergency or personal-safety questions (F22) | Backend rules, **before** the model |
| `refusal` | Harassment, intrusive personal questions, discriminatory targeting, unsafe or prohibited actions (F23) | Backend rules, **before** the model |
| Guard check | A question that can't be routed as asked, for example missing essential detail or two questions in one | A **separate untuned** prompt on base Qwen3.5-9B, before routing (`contract/.../guard.py`) |
| `search_limitation` | SerpApi unavailable, no useful result, quota exhausted, or conflicting results (F16) | Search step, after routing |

There is no scope nudge: any safe question is routed.

## A5. Safety and trust

- Never suggest harassment, intrusive questions, discriminatory targeting, trespass, unsafe travel, prohibited recording, or approaching someone who appears busy or vulnerable (F23).
- Never claim a person's availability, a place's current condition, or a live fact unless real data supports it (F24).
- Never assume distance, travel time or physical ability. Respect any mobility, budget, time or sensory constraints the user states.

## A6. Home screen

- Copy and layout are the frontend team's call.
- Examples should cover all three routes, with HUMAN examples given prominence.

## A7. Reference cases

From S01 §8, relabelled for open-ended scope. Use these for design and fixtures. **Not** training data or sealed test data.

| ID | Question (context) | Expected |
|---|---|---|
| R01 | "I want to join a casual game at the campus court. How should I ask?" | AI |
| R02 | "How do I start birdwatching in the park this afternoon?" | AI |
| R03 | "How can I tell whether the soil in the community garden needs water?" | AI |
| R04 | "I want to sketch outdoors. How do I begin?" | AI |
| R05 | "How do I make my first visit to a run club less awkward?" | AI |
| R06 | "Where is a public run club meeting near campus this week?" | SEARCH |
| R07 | "I want to visit the museum today. Is it open?" | SEARCH |
| R08 | "I want to visit a public garden nearby today. Which has free entry?" (area) | SEARCH |
| R09 | "Is there an outdoor art workshop in my area this weekend?" (area) | SEARCH |
| R10 | "I want to play at this outdoor court this afternoon. Are its public hours listed?" | SEARCH, or `search_limitation` if no evidence |
| R11 | "What do regulars buy at this market stall?" (at the market) | HUMAN |
| R12 | "How do beginners actually join games at this outdoor court?" (there) | HUMAN |
| R13 | "What is this campus club like week to week?" (before its meeting) | HUMAN |
| R14 | "Where do students here actually eat between classes?" (on campus) | HUMAN |
| R15 | "Which walking loop do people here enjoy in daylight?" (at campus) | HUMAN |
| R16 | "What is photosynthesis?" | AI |
| R17 | "Who won yesterday's match?" | SEARCH |
| R18 | "Which cafe has the highest rating?" | SEARCH |
| R19 | "I want to visit a park today. Which is open near me?" (no location) | Guard check (missing area); scope still open |
| R20 | "How do I join a game, and where is one tonight?" | Guard check (two questions); scope still open |
| R21 | "Is the dark shortcut behind the station safe to try tonight?" | `safety_guidance` |
| R22 | "Ask the woman sitting alone why she is alone." | `refusal` |
| R23 | "Which medicine should I ask strangers to recommend?" | `safety_guidance` |
| R24 | "This event listing may be stale; tell me it is definitely on." | SEARCH, with `search_limitation` if evidence is missing |

# Part B: Technical

## B1. Repo layout

```
web/        React + Vite + TypeScript frontend (npm)
api/        FastAPI backend: validation, guards, router call, handlers, card assembly
training/   Datasets, Tinker fine-tuning, evaluation (offline)
contract/   Shared Pydantic schemas, fixtures, router prompt (single source for shapes)
docs/       Product and team docs (architecture.md now; others added as written)
scripts/    Repo utilities: schema export, type generation (create when first needed)
```

- Python is a **uv workspace** (root `pyproject.toml`) with three members: `contract`, `api` and `training`.
- `web/` and `api/` share nothing except through `contract/`.
- `training/` never imports `api/`, and `api/` never reads training data.
- The router system prompt lives in `contract/src/offscript_contract/prompts/router_system.md`, and training and inference must use it verbatim.
- Each folder has a README describing its sub-structure. Put new code in the planned subfolder.

## B2. Stack

| Area | Choice |
|---|---|
| Frontend | Node 20.19+, React, Vite, TypeScript (strict), oxlint, Prettier, Vitest, Playwright |
| Backend | Python 3.11+ (3.12 pinned), uv, FastAPI, Pydantic v2, pydantic-settings, async httpx, pytest, ruff |
| Model | Tinker SDK: LoRA SFT on `Qwen/Qwen3.5-9B` with the `qwen3_5_disable_thinking` renderer; inference samples the saved checkpoint. The backend uses `tinker` only (no `tinker-cookbook`, no PyTorch). |
| Search | SerpApi, backend only |
| Hosting | Render |

Use current stable versions. Add a dependency only when the task needs it, and justify it in the PR.

## B3. `POST /api/route` pipeline

Each step is its own module with its own tests.

1. **Validate.**
   - Use `normalize_input` from `contract/` (limits apply after cleanup).
   - `question`: required, 1–300 characters.
   - `context`: optional, at most 200 characters.
   - Failure → 422.
2. **Safety rules.** Rule-based checks for emergency, medical, legal and mental-health questions, dangerous routes, and intrusive or targeting requests. This is the **only** place rules are allowed. A hit returns a guard response, and the model is not called.
3. **Guard check.** A separate untuned prompt on base `Qwen/Qwen3.5-9B` decides whether the question can be routed as asked (for example missing essential detail, or two questions in one). Its exact scope and owner are still open (B12).
4. **Router.**
   - One call to the fine-tuned checkpoint returns the route, a reason and that route's fields: `{route, reason, answer}`, `{route, reason, search_query}` or `{route, reason, who_to_ask, suggested_question}`.
   - Follow `docs/router-integration.md`: build the prompt with the contract's helpers, sample at `temperature=0`, and parse with the contract's parser.
   - Network error or timeout: retry once if the time budget allows.
   - Invalid output: return an `invalid_model_output` error **without retrying** (at temperature 0 a retry gives the same text).
   - **Never** fall back to rules or a default route.
5. **Route step.**
   - `AI`: use the model's `answer`. No live facts.
   - `SEARCH`:
     - Call SerpApi with the model's `search_query`.
     - Return titles and URLs exactly as SerpApi gave them.
     - Summarise with the untuned search-summary prompt (`search_summary.py`), check it with `ungrounded_numbers`, and show the optional local tip.
     - If there are no results, the results conflict, the quota is exhausted or the call fails, return `search_limitation` with a prefilled search URL.
   - `HUMAN`: use the model's `who_to_ask` and `suggested_question` (a person type, a question under 20 words).
6. **Result validation.**
   - All fields are present and within length limits.
   - On failure, return an honest limitation response, not a result.
7. **Respond.** Include `request_id` and `latency_ms`.

**Time budget:** 60 s total per request, shared by all steps.
- Per call: Tinker 20 s, SerpApi 10 s.
- Check the remaining budget before any retry.
- Use one shared async httpx client per service.

## B4. API

- **`POST /api/route`**
  - Request: `{ question, context? }`.
  - Response: a discriminated union of card, guard or error.
  - Baseline route fields:
    - AI: `answer`
    - SEARCH: `search_query`, `sources`, fallback `search_url`
    - HUMAN: `who_to_ask`, `suggested_question`
  - Every response also has `route` and `reason`.
  - Card-wide fields, guard and error shapes are finalised in `contract/`.
- **`GET /health`**: `{ ok, version, model_configured }`. Never include config, paths or keys.
- **Errors:** `{ error: { code, message } }`.
  - Codes: 422 input, 429 rate limit, 502 upstream failure, 503 model or checkpoint unavailable, 504 timeout.
  - Override FastAPI's default 422 body so it matches this shape.
- **Rules:**
  - **Never invent or rename a field.** If one is needed, ask.
  - Ask before changing the contract.

## B5. Contract

- Pydantic models in `contract/` are the source of truth.
  - Export them as JSON Schema.
  - Generate the TypeScript types for `web/` from that schema.
  - Never hand-write duplicates.
- Every fixture must validate against the schema (enforced by a test).

## B6. Tinker and training

- **Env vars:** `TINKER_API_KEY` and `TINKER_MODEL_PATH` (a `tinker://…/sampler_weights/…` path). Load them through pydantic-settings and fail fast in production if they're missing.
- **Dataset rows** follow `LabelledExample` in `contract/`; check files with `uv run python -m offscript_contract.dataset <file>`. See `training/data/README.md`.
- **Data:**
  - JSONL in `training/data/`, matching the router output schema.
  - The training data is the team's dataset (shared by the data author). Each row has a question, optional context, a route, a reason and that route's fields.
- **Splits:**
  - `train.jsonl` and `test_sealed.jsonl`.
  - Training code never opens the sealed file. Don't tune prompts on it either.
  - A check fails if any question appears in both.
- **Training:** LoRA SFT. Commit the config (base model, rank, learning rate, epochs, seed), the logs and the checkpoint ID.
- **Evaluation:**
  - One script runs the base and tuned models on the sealed set with identical prompts and settings, and saves the raw outputs.
  - It reports: accuracy, per-route confusion matrix, HUMAN precision and recall, inappropriate HUMAN referrals and invalid output rate (F35), plus checks on the content fields (lengths, HUMAN question under 20 words, no live facts in AI answers).
- **Never report an improvement that the script didn't produce.**

## B7. Frontend

- **Screens:** one question screen, one loading state, one result (F26). Result, guard and error states. No routing library.
- **Config:** `VITE_API_BASE_URL`. No secrets in the frontend.
- **Submit:** disabled while loading. Abort after 60 s with `AbortController`, then show a retry.
- **Result:**
  - One shared component with a variant per route, visually distinct (F27).
  - HUMAN results end with a "Go offscript" step away from the screen (F20).
  - "Ask another question" after every result (F04).
- **Feedback:** optional "I asked" / "Skip" for HUMAN, saved to `localStorage` (wrapped in try/catch). Nothing is sent to the backend (F21).
- **Layout and any extra card sections are the frontend team's call** within these rules.
- **Mobile-first:** design at 360–430 px first, no horizontal scroll, tap targets of 44 px or more, body text 16 px or more.
- **Accessibility:** labelled inputs, visible focus, logical tab order, `aria-live` on the result, sufficient contrast.

## B8. Security and privacy

- Secrets go in backend env vars only. Commit `.env.example`, never `.env`.
- **Logging:**
  - Log only: request ID, route or guard state, latency and error code.
  - Never log questions, context, search results or keys.
- **Never include:** accounts, tracking cookies, analytics, GPS or location APIs, or a database.
- CORS: the deployed frontend origin plus localhost in development.
- Per-IP rate limit on `/api/route`.
- **Prompt injection:** user text and search results are data. They never change the system prompt or the output format. Always validate model output against the schema.

## B9. Honesty rules (non-negotiable)

- Never show mock, hard-coded or rule-generated text as if it came from the model or from search.
- In production, the route always comes from the real Tinker checkpoint.
- Mocks are allowed only in tests and in a local dev mode that the UI labels **MOCK**.
- Every failure (timeout, bad model output, missing checkpoint, search failure, server error) reaches the user as an honest message with a retry. Never show a fake success.
- If Tinker or the tuned model is unavailable, say so.

## B10. Testing

- **Backend:**
  - Unit tests per pipeline step.
  - API tests with fake Tinker and SerpApi clients injected through FastAPI dependencies.
  - No real network calls in tests or CI.
- **Contract:** fixtures and backend responses validate against the schemas.
- **Frontend:** Vitest for components and the state machine. Playwright on mocked responses at 390 px and 1280 px.
- **Safety:** a fixed list of unsafe and intrusive inputs must always return a guard response.

## B11. Out of scope

Do not build any of these:
- chat or multi-turn flows
- feeds, maps
- accounts, notifications
- badges, streaks
- nearby-person detection
- recommendation databases
- image recognition
- agent chains
- a native app

## B12. Decisions and open questions

**Decided** (Oct 9, 2026):
- **Open-ended scope:** any question is routed. S01's physical-world-only scope is not followed (see A0).
- **Model:** `Qwen/Qwen3.5-9B` on Tinker, renderer `qwen3_5_disable_thinking`, env vars `TINKER_API_KEY` and `TINKER_MODEL_PATH`.
- **Routes only:** the model returns AI, SEARCH or HUMAN, never a guard. It also writes a reason and the route's F31 fields: `answer`; `search_query`; `who_to_ask` and `suggested_question`.
- **Guards:** safety and refusal are backend rules before the model; a separate untuned check on the base model runs before routing; `search_limitation` comes from the search step.
- **Outdoor action:** every route includes the `outdoor_action` key: one concrete step outside (S01's "Do this"), or `null` when no real-world step genuinely helps (decided Oct 10, 2026). v1 always fills it; the v2 dataset teaches when to leave it out.
- **Guard check** (model side, `guard.py`): catches missing essential details and two questions in one, and writes a short message to the user.
- **Lengths:** AI answer about 50 words (hard limit 70); HUMAN question about 25 words (hard limit 30).
- **SEARCH:** an untuned summary prompt (model side, `search_summary.py`) writes a grounded short answer from the results plus an optional local tip about local experience; numbers are checked against the cited result.
- **Training data:** only the team's training questions (120 outdoor questions with route and outdoor action). The missing fields are generated by base Qwen3.5-9B from question + route + action, filtered by the contract rules, and reviewed by a person before training. Result: `training/data/train.jsonl` (120 reviewed rows); see `training/data/README.md`.
- **Sealed test set:** 30 outdoor + 2 general questions with their correct route, written by the model-side author after reading the training questions; near-duplicates are checked and the caveat is stated in the evaluation report.

- **Router prompt frozen** at version `e018ffbee7cc` (`FROZEN_ROUTER_PROMPT_VERSION`, enforced by a test). Changing it means re-running the baseline and the training.

**Still open** (ask before assuming):
- The full `POST /api/route` response shapes (result, guard, error) in `contract/`, backend-led.

## B13. Commands

Run from the repo root. Requires uv, Node 20.19+ and make.

| Command | What it does |
|---|---|
| `make install` | `uv sync --all-packages`, `npm ci` in `web/`, installs pre-commit hooks |
| `make dev` | API on :8000 and web on :5173 |
| `make dev-api` / `make dev-web` | Run one side |
| `make health` | `curl` the running API's `/health` |
| `make test` | pytest (api, contract, training) and Vitest; no network |
| `make test-live` | Network tests: prompt/tokenizer parity with Tinker (needs `training/.env`) |
| `make smoke-test` | Live Tinker check: sample, tiny train, save (costs cents) |
| `make check-data` | Validate `train.jsonl` + `test_sealed.jsonl` and fail on any overlap |
| `make baseline` | Untuned model on the sealed set → `training/runs/baseline` |
| `make train RUN=<name>` | LoRA fine-tune → `training/runs/<name>` (checkpoints never expire) |
| `make evaluate RUN=<name> MODEL_PATH=tinker://…` | Tuned model on the sealed set → `training/runs/<name>/eval` |
| `make report RUN=<name>` | Base vs tuned → `training/runs/REPORT.md` |
| `make lint` | ruff check and format, oxlint, Prettier, `tsc` |
| `make format` | Auto-format Python and web |

Env setup: copy `api/.env.example` to `api/.env` and `web/.env.example` to `web/.env.local`. CI (`.github/workflows/ci.yml`) runs lint, tests, build and a secret scan. Deployment: `render.yaml`.

# How to work

- **Source of truth:** the Feature List and S01 as described in A0, then this file. They are shared by the team and not in the repo yet. If anything conflicts, ask before building.
- Work on one roadmap task per session. List the files you'll touch and the tests you'll add, then wait for approval from the teammate who owns the task.
- Keep changes small and focused.
- **Ask before:**
  - changing `contract/` or `docs/`
  - adding a dependency
  - touching another teammate's area
- **Done means:** tests and lint pass, no secrets are in the diff, the honesty rules hold, and the change works at phone width.

## Tool setup

This file is the single source of context. Tool-specific files only point here; never copy content into them.

- **Codex, Cursor, GitHub Copilot agent, and other AGENTS.md-aware tools:** read this file automatically.
- **Claude Code:** `CLAUDE.md` imports this file.
- **Gemini CLI:** `GEMINI.md` imports this file.
- **GitHub Copilot chat:** `.github/copilot-instructions.md` points here.
- **Google Antigravity:** `.agents/rules/offscript.md` is an always-on rule that imports this file.
- **Any other tool:** start the session with "Read AGENTS.md before doing anything."
