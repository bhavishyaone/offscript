import json
from pathlib import Path

import pytest

from offscript_contract.router import parse_router_output
from offscript_training.content_rules import content_problems
from offscript_training.data import (
    SEALED_FILE,
    TRAIN_FILE,
    load_eval_rows,
    load_train,
    overlaps,
    refuse_sealed,
    to_conversation,
)
from offscript_training.metrics import compute
from offscript_training.report import render

ACT = '"outdoor_action":"Try it once outside."'
AI = '{"route":"AI","reason":"Stable.","answer":"Hold it level.",' + ACT + "}"
HUMAN = (
    '{"route":"HUMAN","reason":"Locals know.","who_to_ask":"a regular",'
    '"suggested_question":"What do you usually get here?",' + ACT + "}"
)


def record(gold, predicted, kind="outdoor", reply=None, error=None, id_="x"):
    return {"id": id_, "route": gold, "kind": kind, "predicted": predicted,
            "reply": reply, "error": error}  # fmt: skip


def test_repo_data_files_are_valid_and_separate():
    train = load_train(TRAIN_FILE)
    sealed = load_eval_rows(SEALED_FILE)
    assert len(train) == 120 and len(sealed) == 32
    assert overlaps([e.model_dump() for e in train], sealed) == []


def test_sealed_set_is_refused_for_training(tmp_path):
    with pytest.raises(SystemExit):
        refuse_sealed(Path("training/data/test_sealed.jsonl"))
    with pytest.raises(SystemExit):
        load_train(SEALED_FILE)


def test_overlap_check_catches_near_copies():
    a = [{"id": "t1", "question": "Is the city zoo open on Tuesdays?"}]
    b = [{"id": "s1", "question": "Is the city zoo open on a Tuesday?"}]
    assert overlaps(a, b)[0][1:] == ("t1", "s1")
    assert overlaps(a, [{"id": "s2", "question": "How do I pitch a tent?"}]) == []


def test_conversation_ends_with_the_exact_target_reply():
    example = load_train(TRAIN_FILE)[0]
    messages = to_conversation(example)["messages"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant"]
    assert messages[-1]["content"] == example.target_json
    assert parse_router_output(messages[-1]["content"]).route.value == example.route


def test_metrics_routing_human_and_invalid():
    ai, human = json.loads(AI), json.loads(HUMAN)
    records = [
        record("AI", "AI", reply=ai, id_="a"),
        record("HUMAN", "HUMAN", reply=human, id_="b"),
        record("SEARCH", "HUMAN", reply=human, id_="c"),
        record("SEARCH", None, error="not_json", id_="d"),
        record("AI", "AI", kind="general", reply=ai, id_="e"),
    ]
    metrics = compute(records)
    overall = metrics["all"]
    assert overall["accuracy"] == 0.6
    assert overall["human_precision"] == 0.5 and overall["human_recall"] == 1.0
    assert overall["inappropriate_human_ids"] == ["c"]
    assert overall["invalid_codes"] == {"not_json": 1}
    assert overall["confusion"]["SEARCH"] == {"HUMAN": 1, "INVALID": 1}
    assert metrics["by_kind"]["general"]["accuracy"] == 1.0
    assert metrics["content"]["human_questions_within_target"] == 1.0


def test_content_rules_flag_live_facts_and_presence():
    live = parse_router_output(AI.replace("Hold it level.", "It is open until 6 pm today."))
    present = parse_router_output(HUMAN.replace("a regular", "a regular currently on court"))
    assert content_problems(live) == ["answer states a live fact"]
    assert content_problems(present) == ["implies someone is present"]
    assert content_problems(parse_router_output(AI)) == []


def test_report_renders_both_models():
    base = compute([record("AI", None, error="schema")])
    tuned = compute([record("AI", "AI", reply=json.loads(AI))])
    for metrics, model in ((base, "base"), (tuned, "tuned")):
        metrics |= {"model": model, "data": "sealed", "router_prompt_version": "v",
                    "sampling": {"temperature": 0.0}}  # fmt: skip
    text = render(base, tuned)
    assert "| Routing accuracy | 0% | 100% |" in text
    assert "| Invalid outputs | 1 | 0 |" in text


def test_guard_metrics_count_wrong_stops_and_misses():
    from offscript_training.evaluate_guard import compute, load_rows

    def guard(id_, expected, verdict, error=None):
        return {"id": id_, "expected": expected, "verdict": verdict, "error": error}

    metrics = compute([
        guard("a", "ok", "ok"),
        guard("b", "ok", "needs_detail"),
        guard("c", "needs_detail", "needs_detail"),
        guard("d", "two_questions", "ok"),
        guard("e", "ok", None, error="not_json"),
    ])  # fmt: skip
    assert (metrics["passed_good"], metrics["good_questions"]) == (1, 3)
    assert metrics["wrongly_stopped_ids"] == ["b", "e"]
    assert (metrics["caught"], metrics["should_stop"], metrics["missed_ids"]) == (1, 2, ["d"])
    assert metrics["invalid"] == 1
    for path in ("training/data/guard_dev.jsonl", "training/data/guard_check.jsonl"):
        assert load_rows(Path(path))
    with pytest.raises(SystemExit):
        load_rows(SEALED_FILE)


def test_train_config_never_expires_real_checkpoints(tmp_path, monkeypatch):
    from offscript_training import train

    monkeypatch.setattr(train, "RUNS", tmp_path)
    run_dir, config = train.build_config("real", TRAIN_FILE, dict(train.DEFAULTS), None)
    assert config.ttl_seconds is None
    assert json.loads((run_dir / "run_config.json").read_text())["train_rows"] == 120
    assert len((run_dir / "train_conversations.jsonl").read_text().splitlines()) == 120
    _, dry = train.build_config("dry", TRAIN_FILE, dict(train.DEFAULTS), 2)
    assert dry.ttl_seconds and dry.max_steps == 2
    with pytest.raises(SystemExit):
        train.build_config("bad", SEALED_FILE, dict(train.DEFAULTS), None)
