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


def test_v2_family_split_never_puts_a_family_on_both_sides():
    from offscript_training.data import V2_TRAIN_FILE, family_split, load_v2_metadata

    examples, metadata = load_train(V2_TRAIN_FILE), load_v2_metadata()
    train_rows, validation = family_split(examples, metadata, 0.1, 0)
    family = lambda rows: {str(metadata[e.id]["seed"]) for e in rows}  # noqa: E731
    assert family(train_rows).isdisjoint(family(validation))
    assert len(train_rows) + len(validation) == len(examples)
    assert 0.07 < len(family(validation)) / len(family(examples)) < 0.13
    again = family_split(examples, metadata, 0.1, 0)
    assert [e.id for e in again[1]] == [e.id for e in validation]  # deterministic


def test_v2_run_uses_the_v2_prompt_and_puts_validation_first(tmp_path, monkeypatch):
    from offscript_contract.router import FROZEN_ROUTER_PROMPT_V2_VERSION, load_system_prompt
    from offscript_training import train

    monkeypatch.setattr(train, "RUNS", tmp_path)
    run_dir, config = train.build_config(
        "v2", train.V2_TRAIN_FILE, dict(train.DEFAULTS), None, dataset="v2"
    )
    record = json.loads((run_dir / "run_config.json").read_text())
    assert record["router_prompt_version"] == FROZEN_ROUTER_PROMPT_V2_VERSION
    validation_ids = json.loads((run_dir / "split.json").read_text())["validation_ids"]
    assert record["held_out_rows"] == len(validation_ids) > 0
    lines = (run_dir / "train_conversations.jsonl").read_text().splitlines()
    assert len(lines) == record["train_rows"] == 1085
    first = json.loads(lines[0])["messages"]
    assert first[0]["content"] == load_system_prompt("router_system_v2")
    assert config.dataset_builder.test_size == len(validation_ids)
    assert config.dataset_builder.shuffle_seed is None


def test_step_metrics_count_missed_and_false_steps():
    def row(id_, kind, expects, action):
        reply = {**json.loads(AI), "outdoor_action": action}
        return {**record("AI", "AI", kind=kind, reply=reply, id_=id_), "expects_action": expects}

    metrics = compute([
        row("a", "outdoor", True, "Try it."),
        row("b", "outdoor", True, None),
        row("c", "general", False, None),
        row("d", "general", False, "Take a walk."),
        row("e", "general", False, None),
    ])  # fmt: skip
    steps = metrics["steps"]["all"]
    assert (steps["missed_steps"], steps["expected_step"], steps["missed_step_ids"]) == (
        1,
        2,
        ["b"],
    )
    assert (steps["false_steps"], steps["expected_none"], steps["false_step_ids"]) == (1, 3, ["d"])
    assert metrics["steps"]["by_kind"]["general"]["false_step_rate"] == 0.333
    text_metrics = {**metrics, "model": "m", "data": "training/data/test_sealed_v2.jsonl",
                    "router_prompt_version": "v", "sampling": {"temperature": 0.0}}  # fmt: skip
    text = render(text_metrics, text_metrics)
    assert "| False steps (no step was expected) | 1/3 (33%) | 1/3 (33%) |" in text
    assert "v2 sealed set was written" in text
    assert "steps" not in compute([record("AI", "AI", reply=json.loads(AI))])  # v1 sets


def test_repo_v2_data_passes_its_check():
    from offscript_training.data import check_v2

    assert check_v2() == []
