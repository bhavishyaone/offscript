# Model integration (backend)

How the API calls the three model prompts so the fine-tuned router sees exactly what it was trained on. Everything named here lives in `contract/src/offscript_contract/`. Use it; don't reimplement it.

## Pipeline

```
question (+ context)
  1. normalize_input          → InputError → 422 with its message
  2. safety rules (backend)   → safety_guidance / refusal (no model call)
  3. guard check              → base Qwen3.5-9B, guard.py
       needs_detail / two_questions → show its message, stop
  4. router                   → fine-tuned checkpoint, router.py
       AI      → show `answer` + `outdoor_action` (if not null)
       SEARCH  → SerpApi(search_query) → search summary (step 5)
       HUMAN   → show `who_to_ask`, `suggested_question`, `outdoor_action` (if not null), "Go offscript"
  5. search summary (SEARCH only) → base Qwen3.5-9B, search_summary.py
```

Every model call is built and read the same way:

| Step | Use |
|---|---|
| Messages | `build_guard_messages`, `build_router_messages` or `build_summary_messages` (they all clean input with `normalize_input`) |
| Tokens | `render_chat_prompt(tokenizer, messages)` → `tinker.ModelInput.from_ints(...)` |
| Sample | `temperature=0`, `stop=[stop_token_id(tokenizer)]`, `max_tokens` = `GUARD_MAX_TOKENS`, `MAX_TOKENS` or `SUMMARY_MAX_TOKENS` |
| Decode | `decode_completion(tokenizer, tokens)` → `(text, complete)` |
| Parse | `parse_guard_output`, `parse_router_output` or `parse_summary_output` with `complete=complete` |

At startup, once: create two sampling clients, `base_model=BASE_MODEL` (guard check and summary) and `model_path=TINKER_MODEL_PATH` (router). Get the tokenizer with `get_tokenizer()`. Log the three prompt versions (`guard_prompt_version()`, `router_prompt_version()`, `summary_prompt_version()`) and the checkpoint path.

The backend needs `tinker` only, not `tinker-cookbook`, so PyTorch is never installed on Render. `make test-live` proves the contract's prompts match the cookbook token for token.

## Router replies

| Route | Fields | Limits |
|---|---|---|
| `AI` | `reason`, `answer` | Answer about 50 words, hard limit 70; plain text or short bullet lines |
| `SEARCH` | `reason`, `search_query` | Query on one line, up to 200 characters |
| `HUMAN` | `reason`, `who_to_ask`, `suggested_question` | One person type; one question ending in "?", about 25 words, hard limit 30 |

Every route also has the `outdoor_action` key: one concrete, optional step outside related to the question (one line, about 35 words at most; conditional for SEARCH), or `null` when no real-world step genuinely helps (a cover letter, an exchange rate). The key is always present.

How the UI uses it:

| `outdoor_action` | Route | Show |
|---|---|---|
| a step | any | The step section, and "Go offscript" |
| `null` | AI or SEARCH | No step section and no "Go offscript": the answer is complete on screen |
| `null` | HUMAN | No step section, but keep "Go offscript": asking the person is the real-world step. The pocket card shows who to ask and the question |

The backend never invents a step: whatever the model returns is passed through. The v1 checkpoint always returns a step; `null` appears once v2 is live.

The reason is one line, up to 160 characters. Fields for other routes, or any extra field, make the reply invalid.

## SEARCH results

1. Call SerpApi with `search_query`. On an error, quota exhausted or no results, return `search_limitation` with a prefilled search link (F16).
2. Pass up to `MAX_RESULTS` results (title, snippet, link) to the summary call.
3. `answered` → run `ungrounded_numbers(summary, results)`. Any number in the summary missing from the cited result means treat it as `unclear`.
4. Show the summary with "according to" the cited site, all source links, and `local_tip` if present. On `unclear`, say the results don't clearly answer it, show the links and the search link.

`local_tip` is only about local experience (crowds, best time, what to see). It never asks people to confirm official facts.

## Failures

| Failure | Response |
|---|---|
| Network error or timeout | Retry once if the request's 60 s budget allows, then 504 |
| `ModelOutputError` (any code) from any of the three calls | Honest error, **no retry**: at temperature 0 a retry returns the same text |
| Key rejected or checkpoint missing | 503 model unavailable |
| Any failure | Never fall back to a default route, rules, or a made-up answer |

Log only the guard verdict, route, latency and error codes; never the question, context, search results or model text.

## Mocks

Only when `OFFSCRIPT_MODE=mock` (the API refuses to start with mock in production). Use the raw replies in `contract/fixtures/router/`, `contract/fixtures/guard/` and `contract/fixtures/search_summary/`, passed through the same parsers. The `invalid` cases test error handling. Responses are labelled mock.

To test a result with no outdoor step in mock mode, ask a question containing:

| Words in the question | Mock reply |
|---|---|
| "cover letter", "email" or "convert" | AI, `outdoor_action: null` |
| "exchange rate", "usd to inr" or "dollar rate" | SEARCH, `outdoor_action: null` |
| "hostel life", "what is it like to live" or "work culture" | HUMAN, `outdoor_action: null` |

Every other mock question returns a step, as before.

## Versions and handover

- A checkpoint is valid only with the router prompt it was trained on. Every handover gives **both** `TINKER_MODEL_PATH` and `router_prompt_version()`.
- Each system prompt goes first and is identical on every call, so Tinker's cached-prefill discount applies.
- Cost on Qwen3.5-9B is about $0.0006 per call and about 2–3 s. A SEARCH question uses three calls.
- Golden check at integration: the route must match the evaluation output exactly; text fields may differ in wording.
