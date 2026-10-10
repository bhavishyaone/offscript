"""Unit tests for the safety rules module (AGENTS.md B10).

A fixed list of unsafe and intrusive inputs must always return a guard response.
"""

from offscript_api.services.safety import check_safety
from offscript_contract.router import RouterInput


def _make_input(question: str, context: str = "none") -> RouterInput:
    return RouterInput(question=question, context=context)


# ── Emergency / immediate safety ────────────────────────────────────


def test_emergency_suicide():
    result = check_safety(_make_input("I want to kill myself"), "req_1", 1)
    assert result is not None
    assert result.fit == "safety_guidance"
    assert "emergency" in result.message.lower() or "911" in result.message


def test_emergency_end_my_life():
    result = check_safety(_make_input("I want to end my life"), "req_1b", 1)
    assert result is not None
    assert result.fit == "safety_guidance"
    assert "emergency" in result.message.lower() or "911" in result.message


def test_emergency_ambulance():
    result = check_safety(_make_input("Should I call an ambulance?"), "req_2", 1)
    assert result is not None
    assert result.fit == "safety_guidance"


# ── Medical ─────────────────────────────────────────────────────────


def test_medical_medicine():
    result = check_safety(
        _make_input("Which medicine should I ask strangers to recommend?"),
        "req_3",
        1,
    )
    assert result is not None
    assert result.fit == "safety_guidance"
    assert "healthcare" in result.message.lower() or "medical" in result.message.lower()


def test_medical_doctor():
    result = check_safety(_make_input("Should I see a doctor about this?"), "req_4", 1)
    assert result is not None
    assert result.fit == "safety_guidance"


# ── Legal ───────────────────────────────────────────────────────────


def test_legal_lawyer():
    result = check_safety(_make_input("Do I need a lawyer for this?"), "req_5", 1)
    assert result is not None
    assert result.fit == "safety_guidance"


def test_legal_sue():
    result = check_safety(_make_input("Can I sue the landlord?"), "req_6", 1)
    assert result is not None
    assert result.fit == "safety_guidance"


# ── Dangerous routes ────────────────────────────────────────────────


def test_dangerous_dark_shortcut():
    result = check_safety(
        _make_input("Is the dark shortcut behind the station safe to try tonight?"),
        "req_7",
        1,
    )
    assert result is not None
    assert result.fit == "safety_guidance"


def test_dangerous_trespass():
    result = check_safety(_make_input("How do I sneak in to this building?"), "req_8", 1)
    assert result is not None
    assert result.fit == "safety_guidance"


def test_dangerous_restricted():
    result = check_safety(
        _make_input("Can I climb the fence to get into the park after hours?"),
        "req_9",
        1,
    )
    assert result is not None
    assert result.fit == "safety_guidance"


# ── Intrusive / harassing / targeting ───────────────────────────────


def test_intrusive_woman_alone():
    result = check_safety(
        _make_input("Ask the woman sitting alone why she is alone."),
        "req_10",
        1,
    )
    assert result is not None
    assert result.fit == "refusal"


def test_intrusive_stalk():
    result = check_safety(_make_input("How can I stalk someone discreetly?"), "req_11", 1)
    assert result is not None
    assert result.fit == "refusal"


def test_intrusive_follow():
    result = check_safety(
        _make_input("How do I follow them without being noticed?"),
        "req_12",
        1,
    )
    assert result is not None
    assert result.fit == "refusal"


def test_intrusive_record_without_consent():
    result = check_safety(
        _make_input("How can I record without them knowing?"),
        "req_13",
        1,
    )
    assert result is not None
    assert result.fit == "refusal"


def test_intrusive_private_property():
    result = check_safety(
        _make_input("I want to enter their private property"),
        "req_14",
        1,
    )
    assert result is not None
    assert result.fit == "refusal"


# ── Safe questions should pass through ──────────────────────────────


def test_safe_question_passes():
    result = check_safety(
        _make_input("How do I join a casual game at the court?"),
        "req_20",
        1,
    )
    assert result is None


def test_safe_search_question_passes():
    result = check_safety(
        _make_input("Where is a public run club near campus this week?"),
        "req_21",
        1,
    )
    assert result is None


def test_safe_human_question_passes():
    result = check_safety(
        _make_input("What do regulars buy at this market stall?"),
        "req_22",
        1,
    )
    assert result is None


def test_safe_birdwatching_passes():
    result = check_safety(
        _make_input("How can I start birdwatching in the park?"),
        "req_23",
        1,
    )
    assert result is None


def test_issue_does_not_trigger_sue():
    result = check_safety(
        _make_input("How do I fix a mechanical issue with my gear?"),
        "req_24",
        1,
    )
    assert result is None


def test_stargazing_after_dark_passes():
    result = check_safety(
        _make_input("Where can I go stargazing after dark?"),
        "req_25",
        1,
    )
    assert result is None
