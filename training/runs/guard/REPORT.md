# Guard check: before vs after

The guard check runs on the untuned base model (`Qwen/Qwen3.5-9B`, temperature 0) before the router. It should stop only questions that can't be answered as asked, and let everything else through.

- Before: guard prompt `69afb551f854`
- After: guard prompt `924793c432cd`

| Set | Measure | Before | After |
|---|---|---|---|
| Dev (`training/data/guard_dev.jsonl`, 190) | Good questions let through | 122/176 (69%) | **165/176 (94%)** |
| | Questions that should be stopped, caught | 14/14 | 14/14 |
| Held-out (`training/data/guard_check.jsonl`, 34) | Good questions let through | 16/24 (67%) | **24/24 (100%)** |
| | Questions that should be stopped, caught | 10/10 | 10/10 |
| Golden reference cases (19) | Let through | 8/19 | **13/19** |
| All sets | Invalid replies | 0 | 0 |

## What changed in the prompt

- The person is often already at the place: "this" or "here" plus a context that says where they are is specific enough.
- A named place, team, festival, college or area is specific enough.
- "Today", "tomorrow", "yesterday" and "this weekend" need no date.
- Never ask about preferences, budget, dates, or which of several similar places.

## Caveats

- The prompt was tuned on the dev set, so its dev score is optimistic. The held-out set was written before any change and scored once; it is the fairer number, but it has only 34 questions.
- Expected verdicts are our own labels. Of the 11 dev questions still stopped, several have no place at all ("good momos near me", "Where can I play football?"), which AGENTS.md reference case R19 says should be stopped; they are still counted as errors here.
- Golden questions still stopped: R06, R13, R17, R18, R24 ask for a campus, club, sport, city or event that the question never names, and R08 is wrongly split into two questions.
- The guard runs at temperature 0, but Tinker's output can still vary slightly between runs.

Re-run with `make evaluate-guard RUN=<name>` (needs `training/.env`).
