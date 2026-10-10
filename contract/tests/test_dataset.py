import json

import pytest

from offscript_contract.dataset import LabelledExample, main, validate_dataset

GOOD = {
    "id": "t001",
    "question": "What do regulars buy at this stall?",
    "context": "at the outdoor market",
    "route": "HUMAN",
    "reason": "Regulars know what is good here.",
    "who_to_ask": "a regular customer",
    "suggested_question": "What do you usually get here?",
    "outdoor_action": "At the market, ask a willing regular, then try what they suggest.",
}
AI_ROW = {
    "id": "t002",
    "question": "Why does bread go stale?",
    "context": "",
    "route": "AI",
    "reason": "Stable kitchen science.",
    "answer": "Its starch recrystallises and pushes water out.",
    "outdoor_action": "Visit a bakery early and compare a fresh loaf with a day-old one.",
}


def write_rows(tmp_path, rows):
    path = tmp_path / "data.jsonl"
    path.write_text(
        "".join(row if isinstance(row, str) else json.dumps(row) + "\n" for row in rows)
    )
    return path


def test_valid_rows_and_helpers():
    example = LabelledExample.model_validate(GOOD)
    assert example.category == "HUMAN"
    assert example.router_input.context == "at the outdoor market"
    assert example.target_json == (
        '{"route":"HUMAN","reason":"Regulars know what is good here.",'
        '"who_to_ask":"a regular customer","suggested_question":"What do you usually get here?",'
        '"outdoor_action":"At the market, ask a willing regular, then try what they suggest."}'
    )
    assert LabelledExample.model_validate(AI_ROW).target_json.startswith('{"route":"AI"')


@pytest.mark.parametrize(
    "change",
    [
        {"id": "has space"},
        {"question": "  untrimmed question?"},
        {"question": "two\nlines?"},
        {"context": "none"},
        {"context": "at the  market"},
        {"route": "AI"},
        {"route": "human"},
        {"reason": ""},
        {"question": ""},
        {"question": "x" * 301},
        {"answer": "Extra field for HUMAN."},
        {"suggested_question": "Not a question."},
        {"extra": "field"},
        {"fit": "ok"},
        {"outdoor_action": ""},
    ],
)
def test_bad_rows_are_rejected(change):
    with pytest.raises(ValueError):
        LabelledExample.model_validate({**GOOD, **change})


def test_report_lists_every_problem_with_line_numbers(tmp_path):
    path = write_rows(
        tmp_path,
        [
            GOOD,
            {**GOOD, "id": "t002", "suggested_question": None},
            "not json\n",
            "\n",
            {**GOOD, "id": "t001", "question": "Another question here?"},
            {**GOOD, "id": "t003", "question": "what do regulars buy at this stall?"},
            {**AI_ROW, "id": "t004"},
        ],
    )
    report = validate_dataset(path)
    assert len(report.examples) == 4
    joined = "\n".join(report.errors)
    assert "line 2:" in joined
    assert "line 3: not valid JSON" in joined
    assert "line 4: blank line" in joined
    assert "line 5: id 't001' repeats line 1" in joined
    assert "line 6: question and context repeat line 1" in joined
    assert report.counts == {"HUMAN": 3, "AI": 1}


def test_same_question_with_different_context_is_not_a_duplicate(tmp_path):
    pair = {**AI_ROW, "id": "t005", "question": GOOD["question"], "context": ""}
    report = validate_dataset(write_rows(tmp_path, [GOOD, pair]))
    assert report.errors == []


def test_null_outdoor_action_is_kept_in_the_target():
    example = LabelledExample.model_validate({**AI_ROW, "outdoor_action": None})
    assert example.label.outdoor_action is None
    assert example.target_json.endswith(',"outdoor_action":null}')
    without_key = {key: value for key, value in AI_ROW.items() if key != "outdoor_action"}
    with pytest.raises(ValueError):
        LabelledExample.model_validate(without_key)


def test_cli_exit_codes(tmp_path, capsys):
    assert main([str(write_rows(tmp_path, [GOOD]))]) == 0
    bad = tmp_path / "bad.jsonl"
    bad.write_text("not json\n")
    assert main([str(bad)]) == 1
    assert "not valid JSON" in capsys.readouterr().out


SEALED = {
    "id": "s001",
    "question": "Is the stepwell open?",
    "context": "Adalaj",
    "route": "SEARCH",
    "kind": "outdoor",
}


def test_sealed_rows_hold_question_and_route_only(tmp_path):
    from offscript_contract.dataset import SealedExample

    assert SealedExample.model_validate(SEALED).category == "SEARCH/outdoor"
    for change in [{"kind": "other"}, {"answer": "x"}, {"context": "none"}, {"route": "GUARD"}]:
        with pytest.raises(ValueError):
            SealedExample.model_validate({**SEALED, **change})
    sealed = tmp_path / "test_sealed.jsonl"
    sealed.write_text(json.dumps(SEALED) + "\n")
    report = validate_dataset(sealed)
    assert report.errors == [] and report.counts == {"SEARCH/outdoor": 1}


def test_sealed_rows_may_say_whether_a_step_is_expected(tmp_path):
    from offscript_contract.dataset import SealedExample

    row = {"id": "t2-001", "question": "Why does the sea look blue?", "context": "",
           "route": "AI", "kind": "general"}  # fmt: skip
    assert SealedExample.model_validate(row).expects_action is None  # v1 rows stay valid
    assert SealedExample.model_validate({**row, "expects_action": True}).expects_action is True
    with pytest.raises(ValueError):
        SealedExample.model_validate({**row, "expects_action": "maybe"})
