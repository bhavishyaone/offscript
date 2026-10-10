"""Evaluation metrics from per-question records. Pure functions, no network.

A record is {"id", "route" (gold), "kind", "predicted" (route or None), "error" (code or None),
"reply" (parsed reply as a dict, or None)}.
"""

from collections import Counter

from offscript_contract.parsing import word_count
from offscript_contract.router import (
    ANSWER_TARGET_WORDS,
    HUMAN_QUESTION_TARGET_WORDS,
    ROUTER_OUTPUT,
    Route,
)
from offscript_training.content_rules import content_problems

ROUTES = [route.value for route in Route]


def _rate(part: int, whole: int) -> float | None:
    return round(part / whole, 3) if whole else None


def routing(records: list[dict]) -> dict:
    correct = sum(r["predicted"] == r["route"] for r in records)
    confusion = {gold: Counter() for gold in ROUTES}
    for r in records:
        confusion[r["route"]][r["predicted"] or "INVALID"] += 1
    predicted_human = [r for r in records if r["predicted"] == "HUMAN"]
    gold_human = [r for r in records if r["route"] == "HUMAN"]
    true_human = sum(r["route"] == "HUMAN" for r in predicted_human)
    inappropriate = [r["id"] for r in predicted_human if r["route"] != "HUMAN"]
    invalid = [r for r in records if r["predicted"] is None]
    return {
        "questions": len(records),
        "accuracy": _rate(correct, len(records)),
        "correct": correct,
        "confusion": {gold: dict(row) for gold, row in confusion.items()},
        "human_precision": _rate(true_human, len(predicted_human)),
        "human_recall": _rate(true_human, len(gold_human)),
        "inappropriate_human_referrals": len(inappropriate),
        "inappropriate_human_ids": inappropriate,
        "invalid_outputs": len(invalid),
        "invalid_rate": _rate(len(invalid), len(records)),
        "invalid_codes": dict(Counter(r["error"] for r in invalid)),
    }


def content(records: list[dict]) -> dict:
    replies = [ROUTER_OUTPUT.validate_python(r["reply"]) for r in records if r["reply"]]
    answers = [word_count(x.answer) for x in replies if x.route is Route.AI]
    questions = [word_count(x.suggested_question) for x in replies if x.route is Route.HUMAN]
    flagged = [p for x in replies for p in content_problems(x)]
    return {
        "valid_replies": len(replies),
        "ai_answer_words_avg": round(sum(answers) / len(answers), 1) if answers else None,
        "ai_answers_within_target": _rate(
            sum(n <= ANSWER_TARGET_WORDS for n in answers), len(answers)
        ),
        "human_questions_within_target": _rate(
            sum(n <= HUMAN_QUESTION_TARGET_WORDS for n in questions), len(questions)
        ),
        "content_rule_problems": dict(Counter(flagged)),
    }


def _step_block(rows: list[dict]) -> dict:
    wanted = [r for r in rows if r["expects_action"]]
    unwanted = [r for r in rows if not r["expects_action"]]
    missed = [r["id"] for r in wanted if r["reply"].get("outdoor_action") is None]
    extra = [r["id"] for r in unwanted if r["reply"].get("outdoor_action") is not None]
    return {
        "expected_step": len(wanted),
        "missed_steps": len(missed),
        "missed_step_rate": _rate(len(missed), len(wanted)),
        "missed_step_ids": missed,
        "expected_none": len(unwanted),
        "false_steps": len(extra),
        "false_step_rate": _rate(len(extra), len(unwanted)),
        "false_step_ids": extra,
    }


def steps(records: list[dict]) -> dict | None:
    """Whether the outdoor step appears exactly when the test row expects one (v2 sets only).
    Only valid replies are scored; invalid ones are counted by routing()."""
    scored = [r for r in records if r.get("expects_action") is not None and r["reply"]]
    if not scored:
        return None
    by_kind = {
        kind: _step_block([r for r in scored if r["kind"] == kind])
        for kind in sorted({r["kind"] for r in scored})
    }
    return {"all": _step_block(scored), "by_kind": by_kind}


def compute(records: list[dict]) -> dict:
    by_kind = {
        kind: routing([r for r in records if r["kind"] == kind])
        for kind in sorted({r["kind"] for r in records})
    }
    result = {"all": routing(records), "by_kind": by_kind, "content": content(records)}
    step_metrics = steps(records)
    if step_metrics is not None:
        result["steps"] = step_metrics
    return result
