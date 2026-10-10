# Offscript v2 router dataset - team handoff

**Status:** Generated review draft, **not approved for training**.
**Product decision:** [Product direction clarification](../OFFSCRIPT_PRODUCT_DIRECTION_CLARIFICATION.md) - general questions are answered; a physical step appears only when it genuinely helps.
**Date:** 10 October 2026.

## Files

| File | Purpose |
|---|---|
| [V2_ROUTER_1000_REVIEW_DRAFT.jsonl](../data/V2_ROUTER_1000_REVIEW_DRAFT.jsonl) | 1,030 full router-target rows for review: question, context, one of AI/SEARCH/HUMAN, route-specific content, and `outdoor_action` as a useful step or `null`. |
| [V2_ROUTER_1000_METADATA.jsonl](../data/V2_ROUTER_1000_METADATA.jsonl) | Parallel review index keyed by ID: topic, field/general segment, wording style, action decision, and seed family. **Do not feed this file to the model.** |
| [V2_GUARD_80_REVIEW_DRAFT.jsonl](../data/V2_GUARD_80_REVIEW_DRAFT.jsonl) | 80 separate safety, refusal, missing-detail, and two-question checks. **Do not mix these into router fine-tuning.** |

The reproducible builders are [build_v2_router_dataset.py](../scripts/build_v2_router_dataset.py) and [build_v2_guard_bank.py](../scripts/build_v2_guard_bank.py). Keep edits in those files and regenerate the JSONL so IDs, metadata, and counts stay aligned.

The router file has **367 AI, 335 SEARCH, and 328 HUMAN** examples. **631** have a physical step; **399** intentionally use `null`. It covers **202 scenario seeds in five wordings each**, plus **10 question pairs where context changes the correct source**. Styles include **150 Hinglish rows**, **202 terse/search-style rows**, **202 contextual rows**, **26 instruction-injection rows**, and other natural/rephrased forms. Topics span everyday knowledge and skills, outdoor activities, current facts, Indian cities and venues, campus/hostel life, local habits, food, transit, access, cultural facts, and social questions.

This is substantial wording coverage, **not 1,030 independent use cases and not every possible question**. Five paraphrases share a scenario and often the same target content. Keep families together during validation; a random row-level split would leak paraphrases into both training and validation.

## Intended v2 target format

Every route keeps its existing route-specific fields. The only new target decision is whether the physical extension is useful:

```json
{"route":"AI","reason":"...","answer":"...","outdoor_action":null}
{"route":"SEARCH","reason":"...","search_query":"...","outdoor_action":"If a current listing confirms access, visit during public hours."}
{"route":"HUMAN","reason":"...","who_to_ask":"a current student","suggested_question":"What is a normal week here like?","outdoor_action":null}
```

`null` means the model should give the useful answer or HUMAN handoff **without inventing an outing**. A string means the step is safe, optional, and connected to the user's question. The three source labels do not change. Safety and missing-context responses remain separate from the router.

**The current repository cannot train or display these targets unchanged.** Its v1 prompt, parser, response contract, and UI require a nonempty action. The team must first allow `null` in the shared model/response contract and render the action section and **Go offscript** control only when a step exists. Its duplicate checker must also key on **question plus context**, because the 10 deliberate context pairs repeat question wording. This is structural handling; the model, trained on the two outcomes, decides whether a step is useful. Because the router prompt is frozen to the v1 checkpoint, changing it requires a new baseline, training run, and evaluation.

## Review before training

1. **Review every row.** Check whether the source actually answers the question, the AI answer is factually correct, a SEARCH query preserves the exact intent, and a HUMAN question asks one natural thing of a plausible person. Fact-check AI answers against reliable sources; do not assume generated text is correct.
2. **Review every action decision.** Reject decorative walks, unnecessary purchases, inaccessible or unsafe steps, and suggestions that claim a person/event/place is available without evidence. For `null` rows, ask whether a truly useful physical extension was missed. Prioritize this review because it is the new skill we want the model to learn.
3. **Review families, not just rows.** The five wording variants must preserve the same intent and target. Check Hinglish with a fluent reviewer. Remove weak or unnatural variants; add genuinely new scenarios in their place. The metadata file identifies families and styles.
4. **Keep evaluation independent.** The repo's 32-question sealed set and 200-question regression set are reference checks, not training data. This draft was screened for near-exact wording overlap with them. An independent teammate should write a **new** sealed set of 100-150 questions after this draft is frozen, including both action and no-action cases. Do not derive that set from these seed families.
5. **Measure the actual new decision.** Report route accuracy and HUMAN precision, plus false physical steps on no-action questions, missed steps on real-world intentions, action relevance/safety judged by people, factual correctness of AI answers, grounded SEARCH behavior, and invalid outputs. Compare v1 and v2 on untouched sets and disclose regressions.

The 80 guard cases are a separate system check. The base guard and backend safety rules must still handle them before the tuned router; router data cannot replace those protections.

## Why this is a review draft

The data is syntactically checked, and all **631 non-null-action rows** pass the repository's current `LabelledExample` format check. The **399 null-action rows** intentionally fail that v1 format because the contract has not yet been updated. The generator and metadata are included for auditability. No human has approved every route, fact, physical step, or Hinglish phrasing, and no v2 training or live-model evaluation has been run on this draft.
