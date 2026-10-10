"""Router contract shared by training and the backend.

One definition of the router's input (cleanup, limits, messages), its output (one reply per
route: AI, SEARCH or HUMAN, with the Feature List fields) and how raw model text is parsed.
Training, evaluation, the live API and the mock router all go through these functions, so they
cannot drift apart.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from hashlib import sha256
from importlib.resources import files
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator

from offscript_contract.parsing import ModelOutputError, check_text, parse_model_json

BASE_MODEL = "Qwen/Qwen3.5-9B"
RENDERER_NAME = "qwen3_5_disable_thinking"
TEMPERATURE = 0.0
MAX_TOKENS = 350
STOP_TOKEN = "<|im_end|>"  # noqa: S105 (a chat marker, not a secret)

QUESTION_MAX = 300
CONTEXT_MAX = 200
NO_CONTEXT = "none"

REASON_MAX_CHARS = 160
ANSWER_TARGET_WORDS = 50  # prompt and evaluation target
ANSWER_MAX_WORDS = 70  # hard limit: longer replies are invalid
ANSWER_MAX_CHARS = 700
SEARCH_QUERY_MAX_CHARS = 200
WHO_TO_ASK_MAX_CHARS = 80
HUMAN_QUESTION_TARGET_WORDS = 25
HUMAN_QUESTION_MAX_WORDS = 30
HUMAN_QUESTION_MAX_CHARS = 220
OUTDOOR_ACTION_MAX_WORDS = 35
OUTDOOR_ACTION_MAX_CHARS = 240


class Route(StrEnum):
    AI = "AI"
    SEARCH = "SEARCH"
    HUMAN = "HUMAN"


class _RouterReply(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reason: str
    # One concrete step outside, or null when no real-world step genuinely helps. The key is
    # always present, so the model states the decision explicitly.
    outdoor_action: str | None

    @field_validator("reason")
    @classmethod
    def _reason(cls, value: str) -> str:
        return check_text(value, max_chars=REASON_MAX_CHARS)

    @field_validator("outdoor_action")
    @classmethod
    def _outdoor_action(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return check_text(
            value, max_chars=OUTDOOR_ACTION_MAX_CHARS, max_words=OUTDOOR_ACTION_MAX_WORDS
        )


class AIOutput(_RouterReply):
    route: Literal[Route.AI]
    answer: str

    @field_validator("answer")
    @classmethod
    def _answer(cls, value: str) -> str:
        return check_text(
            value, max_chars=ANSWER_MAX_CHARS, max_words=ANSWER_MAX_WORDS, multiline=True
        )


class SearchOutput(_RouterReply):
    route: Literal[Route.SEARCH]
    search_query: str

    @field_validator("search_query")
    @classmethod
    def _query(cls, value: str) -> str:
        return check_text(value, max_chars=SEARCH_QUERY_MAX_CHARS)


class HumanOutput(_RouterReply):
    route: Literal[Route.HUMAN]
    who_to_ask: str
    suggested_question: str

    @field_validator("who_to_ask")
    @classmethod
    def _who(cls, value: str) -> str:
        return check_text(value, max_chars=WHO_TO_ASK_MAX_CHARS)

    @field_validator("suggested_question")
    @classmethod
    def _question(cls, value: str) -> str:
        check_text(value, max_chars=HUMAN_QUESTION_MAX_CHARS, max_words=HUMAN_QUESTION_MAX_WORDS)
        if not value.endswith("?") or value.count("?") != 1:
            raise ValueError("must be exactly one question ending with '?'")
        return value


RouterOutput = Annotated[AIOutput | SearchOutput | HumanOutput, Field(discriminator="route")]
ROUTER_OUTPUT = TypeAdapter(RouterOutput)
_FIELD_ORDER = {
    Route.AI: ("route", "reason", "answer", "outdoor_action"),
    Route.SEARCH: ("route", "reason", "search_query", "outdoor_action"),
    Route.HUMAN: ("route", "reason", "who_to_ask", "suggested_question", "outdoor_action"),
}


def to_target_json(output: AIOutput | SearchOutput | HumanOutput) -> str:
    """Canonical training answer: compact, fixed key order, characters kept as written."""
    data = output.model_dump(mode="json")
    payload = {key: data[key] for key in _FIELD_ORDER[output.route]}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


# --- Input -----------------------------------------------------------------------------


class InputError(ValueError):
    """User input the router must never see. `code` is stable for the API's 422 response."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RouterInput:
    question: str
    context: str  # NO_CONTEXT when the user gave none


# Strings the Qwen3.5 tokenizer treats as control tokens. The cookbook renderer encodes them as
# real control tokens even inside user text, so they are removed before any rendering.
CONTROL_TOKEN_PATTERN = re.compile(
    r"<\|[^<>|\s]{1,40}\|>|</?(?:think|tool_call|tool_response)>|<tts_[a-z_]{1,30}>"
)


def clean_text(text: str) -> str:
    """NFC-normalise, remove control-token strings and control characters, and collapse all
    whitespace to single spaces.

    Collapsing newlines also stops a user from faking a second "Context:" line.
    """
    text = unicodedata.normalize("NFC", text)
    text = CONTROL_TOKEN_PATTERN.sub(" ", text)
    text = "".join(ch for ch in text if ch.isspace() or unicodedata.category(ch) != "Cc")
    return " ".join(text.split())


def normalize_input(question: str, context: str | None = None) -> RouterInput:
    """Clean question and context, then enforce limits on the cleaned text."""
    question = clean_text(question)
    context = clean_text(context or "")
    if not question:
        raise InputError("question_empty", "Please enter a question.")
    if len(question) > QUESTION_MAX:
        raise InputError("question_too_long", f"Keep the question under {QUESTION_MAX} characters.")
    if len(context) > CONTEXT_MAX:
        raise InputError("context_too_long", f"Keep the context under {CONTEXT_MAX} characters.")
    return RouterInput(question=question, context=context or NO_CONTEXT)


def format_user_message(router_input: RouterInput) -> str:
    return f"Question: {router_input.question}\nContext: {router_input.context}"


@cache
def load_prompt(name: str) -> str:
    return files("offscript_contract").joinpath(f"prompts/{name}.md").read_text("utf-8")


def prompt_version(name: str) -> str:
    """Short hash of a prompt file. A checkpoint is only valid with the router prompt it was
    trained on, so the router's version travels with every checkpoint handover."""
    return sha256(load_prompt(name).encode("utf-8")).hexdigest()[:12]


def load_system_prompt() -> str:
    return load_prompt("router_system")


def router_prompt_version() -> str:
    return prompt_version("router_system")


# Frozen before the baseline run: the baseline, the training data and the tuned checkpoint all
# use this exact prompt. Changing it means re-running the baseline and the fine-tuning.
FROZEN_ROUTER_PROMPT_VERSION = "e018ffbee7cc"


def build_router_messages(question: str, context: str | None = None) -> list[dict[str, str]]:
    router_input = normalize_input(question, context)
    return [
        {"role": "system", "content": load_system_prompt()},
        {"role": "user", "content": format_user_message(router_input)},
    ]


# --- Output ----------------------------------------------------------------------------

RouterOutputError = ModelOutputError


def parse_router_output(
    text: str, *, complete: bool = True
) -> AIOutput | SearchOutput | HumanOutput:
    """Parse raw router text strictly into one route's reply. See parsing.parse_model_json."""
    return parse_model_json(text, ROUTER_OUTPUT, complete=complete)
