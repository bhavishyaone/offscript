"""Format and validation for labelled router examples (training data and the sealed test set).

Check a file before committing it (the sealed test set is detected by its file name):

    uv run python -m offscript_contract.dataset training/data/train.jsonl
    uv run python -m offscript_contract.dataset training/data/test_sealed.jsonl
"""

import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from offscript_contract.router import (
    NO_CONTEXT,
    ROUTER_OUTPUT,
    AIOutput,
    HumanOutput,
    InputError,
    Route,
    RouterInput,
    SearchOutput,
    normalize_input,
    to_target_json,
)

ROUTE_FIELDS = ("answer", "search_query", "who_to_ask", "suggested_question", "outdoor_action")


def _check_clean_input(question: str, context: str) -> None:
    """Rows store input exactly as the model will see it after normalize_input."""
    try:
        cleaned = normalize_input(question, context)
    except InputError as error:
        raise ValueError(str(error)) from None
    if cleaned.question != question:
        raise ValueError("question has extra spaces, line breaks or control characters")
    if context and cleaned.context != context:
        raise ValueError("context has extra spaces, line breaks or control characters")
    if context.lower() == NO_CONTEXT:
        raise ValueError('leave context as "" instead of writing "none"')


class LabelledExample(BaseModel):
    """One JSONL row: the input, the route, a reason and only that route's fields.

    `context` is "" when there is none. Text must already be clean, so every file stores
    questions exactly as the model will see them.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    question: str
    context: str
    route: Route
    reason: str
    answer: str | None = None
    search_query: str | None = None
    who_to_ask: str | None = None
    suggested_question: str | None = None
    outdoor_action: str | None  # required key; null when no real-world step helps

    @model_validator(mode="after")
    def _clean_and_consistent(self) -> "LabelledExample":
        _check_clean_input(self.question, self.context)
        _ = self.label  # validates the route's fields with the router's own rules
        return self

    @property
    def router_input(self) -> RouterInput:
        return normalize_input(self.question, self.context)

    @property
    def label(self) -> AIOutput | SearchOutput | HumanOutput:
        payload = {
            "route": self.route.value,
            "reason": self.reason,
            "outdoor_action": self.outdoor_action,  # kept even when null
        }
        payload |= {name: getattr(self, name) for name in ROUTE_FIELDS if getattr(self, name)}
        return ROUTER_OUTPUT.validate_python(payload)

    @property
    def target_json(self) -> str:
        return to_target_json(self.label)

    @property
    def category(self) -> str:
        return self.route.value


class SealedExample(BaseModel):
    """One sealed-test row: the input and its correct route only. Content fields are not
    scored against a reference; they are checked by rules during evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    question: str
    context: str
    route: Route
    kind: Literal["outdoor", "general"]
    # v2 sets: whether a useful real-world step is expected (true) or the answer should have
    # outdoor_action null (false). Absent in the v1 sealed set.
    expects_action: bool | None = None

    @model_validator(mode="after")
    def _clean(self) -> "SealedExample":
        _check_clean_input(self.question, self.context)
        return self

    @property
    def router_input(self) -> RouterInput:
        return normalize_input(self.question, self.context)

    @property
    def category(self) -> str:
        return f"{self.route.value}/{self.kind}"


@dataclass
class DatasetReport:
    examples: list[LabelledExample | SealedExample] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def counts(self) -> Counter[str]:
        return Counter(example.category for example in self.examples)


def validate_dataset(path: str | Path, row_model: type[BaseModel] | None = None) -> DatasetReport:
    """Check every line; report each problem with its line number. Never stops early.

    Files named `test_sealed*.jsonl` are checked as SealedExample, everything else as
    LabelledExample, unless `row_model` is given.
    """
    if row_model is None:
        row_model = SealedExample if Path(path).name.startswith("test_sealed") else LabelledExample
    report = DatasetReport()
    seen_ids: dict[str, int] = {}
    seen_questions: dict[tuple[str, str], int] = {}
    for number, line in enumerate(Path(path).read_text("utf-8").splitlines(), start=1):
        if not line.strip():
            report.errors.append(f"line {number}: blank line")
            continue
        try:
            example = row_model.model_validate(json.loads(line))
        except json.JSONDecodeError as error:
            report.errors.append(f"line {number}: not valid JSON ({error.msg})")
            continue
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(str(part) for part in problem['loc']) or 'row'}: {problem['msg']}"
                for problem in error.errors()
            )
            report.errors.append(f"line {number}: {details}")
            continue
        if example.id in seen_ids:
            report.errors.append(
                f"line {number}: id {example.id!r} repeats line {seen_ids[example.id]}"
            )
        seen_ids.setdefault(example.id, number)
        # The same question with a different context is a deliberate pair, not a duplicate.
        key = (example.question.casefold(), example.context.casefold())
        if key in seen_questions:
            report.errors.append(
                f"line {number}: question and context repeat line {seen_questions[key]}"
            )
        seen_questions.setdefault(key, number)
        report.examples.append(example)
    return report


def main(paths: list[str]) -> int:
    failed = False
    for path in paths:
        report = validate_dataset(path)
        counts = ", ".join(f"{name} {count}" for name, count in sorted(report.counts.items()))
        print(f"{path}: {len(report.examples)} valid rows ({counts or 'none'})")
        for error in report.errors:
            print(f"  {error}")
        failed = failed or bool(report.errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
