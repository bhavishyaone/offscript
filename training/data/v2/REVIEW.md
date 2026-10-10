# v2 router dataset: review record

**Result:** `router_v2.jsonl` (1,085 rows) and `router_v2_metadata.jsonl`, built from the unchanged draft (`router_draft.jsonl`, `router_metadata.jsonl`) by `scripts/router_v2_review/apply_review.py`. Re-running the script rebuilds the files exactly.

**Review type:** AI-assisted review by the model owner with Claude, on 10 October 2026. Every row is marked `reviewed_ai_assisted`, not reviewed by an independent person. A human spot-check of the AI answers and Hinglish wording is still worthwhile.

## What was checked, family by family (all 212)

| Check | Result |
|---|---|
| Route fits the source of the missing knowledge | All 212 families kept their route. Cultural facts (Kho-Kho rules, Onam Sadya dishes, concert instruments) stay SEARCH, as agreed |
| AI answers are factually correct (79 distinct answers) | No factual errors found. Answers are short, hedged where needed, and avoid live facts |
| Outdoor step is safe, optional and connected to the question | All 631 steps pass. Steps that depend on a venue or event are conditional ("If … is confirmed") |
| `null` step only where no real-world step genuinely helps | All 399 kept. All are general, screen-only or remote lived-experience questions |
| HUMAN: a plausible type of person and one natural question | All pass, with exactly one "?" each |
| SEARCH: query keeps the intent, in English, no placeholders or guessed years | All pass |
| The five wordings in a family keep the same intent | All pass, after the fixes below |

## What changed

1. **Reasons:** replaced the 32 template sentences with one specific reason per family (213 written), shared by its wordings. Reasons are shown to users.
2. **Contexts:** replaced artificial contexts ("asking for the information itself", "planning to try this in a public place soon") with natural ones that real users would type. AI questions that began "I'm in Pune and want general guidance." now carry the city in the context instead.
3. **Repeated prefixes:** the second Hinglish wording now rotates between five openers (was always "Zara batao:"), and the rephrased wording rotates between four (was always "Could you help me answer this:").
4. **Hinglish casing:** fixed lowercased proper nouns ("lodhi Garden", "iIT Delhi", "rBI").
5. **Near-copies of reference questions:** reworded v2-0691 (golden R11), v2-0811 (golden R14) and context pair 9 (regression Q171).
6. **Awkward wording:** fixed v2-0227 ("respectful way to read a trail sign"), v2-0317 and the tea-stall Hinglish rows (v2-0732, v2-0735).
7. **New families (decision 2):** added 11 general families (55 rows, seeds 203–213) that keep a genuine step, so the model learns the step depends on usefulness, not topic. For example "Why do stars twinkle?" with "compare a star low in the sky with one overhead". Topics were checked against every test set. A first choice of topics repeated test questions (sky colour, lightning, compound interest, the moon near the horizon, ripe mangoes, sunset time) and was replaced.

## Checks on the result

| Check | Result |
|---|---|
| Format (`python -m offscript_contract.dataset`) | 1,085 valid rows: 417 AI, 340 SEARCH, 328 HUMAN |
| Steps | 686 with a step, 399 `null`. Outdoor rows: 0 of 596 `null`. General rows: 90 of 489 keep a step (was 35 of 434) |
| Same question and context twice | 0 |
| Every family has one shared target | Yes (context pairs excepted by design) |
| Near-copies (≥ 0.8 similarity) of the sealed, regression, golden, probe and guard sets | 0 |
| Keyword-shortcut test | 59% (target under 60%) |

## Caveats

- **Wording coverage, not 1,085 independent cases:** the five wordings in a family share one answer. Training and validation must be split by family (`seed` in the metadata), never by row.
- **AI-assisted review:** Claude reviewed the facts and wording. A fluent Hinglish speaker has not checked the Hinglish rows.
- **New sealed test set:** written in the same session as this review (see `test_sealed_v2.jsonl`), so it is not fully independent of the training data. It was screened for overlap, and the evaluation report must state this.
