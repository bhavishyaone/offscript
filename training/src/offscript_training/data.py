"""Loading the training and sealed files, the train/test overlap check, and chat conversions.

uv run python -m offscript_training.data        # check the v1 files before any run
uv run python -m offscript_training.data --v2   # check the v2 files before any v2 run
"""

import json
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from offscript_contract.dataset import LabelledExample, SealedExample, validate_dataset
from offscript_contract.router import ROUTER_PROMPT, build_router_messages

TRAIN_FILE = Path("training/data/train.jsonl")
SEALED_FILE = Path("training/data/test_sealed.jsonl")
NEAR_DUPLICATE = 0.6

V2_TRAIN_FILE = Path("training/data/v2/router_v2.jsonl")
V2_META_FILE = Path("training/data/v2/router_v2_metadata.jsonl")
SEALED_V2_FILE = Path("training/data/test_sealed_v2.jsonl")
# v2 has 1,085 rows that share sentence shapes ("What is the difference between X and Y?"), so
# 0.6 flags many unrelated pairs. A v2 near-copy is 0.8 or more; lower pairs are reviewed by hand
# (see training/data/v2/REVIEW.md).
V2_NEAR_DUPLICATE = 0.8


def refuse_sealed(path: Path) -> None:
    """Training code calls this on every input path: the sealed set must never be trained on."""
    if Path(path).name.startswith("test_sealed"):
        raise SystemExit(f"Refusing to use the sealed test set for training: {path}")


def load_train(path: Path = TRAIN_FILE) -> list[LabelledExample]:
    refuse_sealed(path)
    report = validate_dataset(path, LabelledExample)
    if report.errors:
        raise SystemExit("\n".join([f"{path} is invalid:", *report.errors]))
    return report.examples


def load_eval_rows(path: Path) -> list[dict]:
    """Rows to evaluate: question, context, gold route, kind (outdoor or general)."""
    rows = []
    for line in Path(path).read_text("utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "kind" in row:
            row = SealedExample.model_validate(row).model_dump(mode="json")
        rows.append(
            {
                "id": row["id"],
                "question": row["question"],
                "context": row["context"],
                "route": row["route"],
                "kind": row.get("kind", "outdoor"),
                "expects_action": row.get("expects_action"),
            }
        )
    return rows


def to_conversation(example: LabelledExample, prompt: str = ROUTER_PROMPT) -> dict:
    """One training example in the cookbook's chat format: prompt messages + target reply."""
    messages = build_router_messages(example.question, example.context, prompt=prompt)
    return {"messages": [*messages, {"role": "assistant", "content": example.target_json}]}


def load_v2_metadata(path: Path = V2_META_FILE) -> dict[str, dict]:
    return {
        m["id"]: m
        for m in (
            json.loads(line) for line in Path(path).read_text("utf-8").splitlines() if line.strip()
        )
    }


def family_split(
    examples: list[LabelledExample], metadata: dict[str, dict], fraction: float, seed: int
) -> tuple[list[LabelledExample], list[LabelledExample]]:
    """Hold out whole scenario families for validation. The wordings of one family share a
    target, so a row-level split would put paraphrases of the same answer on both sides."""
    families = sorted({str(metadata[e.id]["seed"]) for e in examples})
    random.Random(seed).shuffle(families)  # noqa: S311 (data shuffling, not security)
    held_out = set(families[: max(1, round(len(families) * fraction))])
    train = [e for e in examples if str(metadata[e.id]["seed"]) not in held_out]
    validation = [e for e in examples if str(metadata[e.id]["seed"]) in held_out]
    # Keep a family's wordings apart in training batches.
    random.Random(seed).shuffle(train)  # noqa: S311 (data shuffling, not security)
    return train, validation


def check_v2() -> list[str]:
    """Problems with the v2 training data, its metadata and the v2 sealed set."""
    problems = []
    train = validate_dataset(V2_TRAIN_FILE, LabelledExample)
    sealed = validate_dataset(SEALED_V2_FILE, SealedExample)
    problems += [f"{V2_TRAIN_FILE}: {error}" for error in train.errors]
    problems += [f"{SEALED_V2_FILE}: {error}" for error in sealed.errors]
    metadata = load_v2_metadata()
    ids = [e.id for e in train.examples]
    if set(ids) != set(metadata):
        problems.append("metadata ids do not match the training rows")
    for e in train.examples:
        expects_step = metadata.get(e.id, {}).get("action") == "step"
        if e.id in metadata and expects_step != (e.outdoor_action is not None):
            problems.append(f"{e.id}: metadata action does not match outdoor_action")
    if any(e.expects_action is None for e in sealed.examples):
        problems.append("every sealed v2 row needs expects_action")
    rows = lambda report: [e.model_dump() for e in report.examples]  # noqa: E731
    for name, other in (
        ("sealed v2", rows(sealed)),
        ("sealed v1", rows(validate_dataset(SEALED_FILE))),
    ):
        for score, train_id, test_id in overlaps(rows(train), other, V2_NEAR_DUPLICATE):
            problems.append(f"{train_id} is a near-copy ({score}) of {name} {test_id}")
    return problems


def _norm(text: str) -> str:
    return re.sub(r"[^a-z ]", "", text.lower())


def overlaps(train: list[dict], sealed: list[dict], threshold: float = NEAR_DUPLICATE):
    """Pairs of (similarity, train id, sealed id) at or above the threshold."""
    hits = []
    for a in train:
        for b in sealed:
            score = SequenceMatcher(None, _norm(a["question"]), _norm(b["question"])).ratio()
            if score >= threshold:
                hits.append((round(score, 2), a["id"], b["id"]))
    return sorted(hits, reverse=True)


def main() -> int:
    if "--v2" in sys.argv[1:]:
        problems = check_v2()
        print(f"v2 check: {len(problems)} problems")
        for problem in problems:
            print(f"  {problem}")
        return 1 if problems else 0
    train = validate_dataset(TRAIN_FILE, LabelledExample)
    sealed = validate_dataset(SEALED_FILE, SealedExample)
    failed = False
    for name, report in (("train", train), ("sealed", sealed)):
        counts = ", ".join(f"{k} {v}" for k, v in sorted(report.counts.items()))
        print(f"{name}: {len(report.examples)} valid rows ({counts})")
        for error in report.errors:
            print(f"  {error}")
        failed |= bool(report.errors)
    rows = lambda report: [e.model_dump() for e in report.examples]  # noqa: E731
    hits = overlaps(rows(train), rows(sealed))
    print(f"train/sealed overlap (similarity >= {NEAR_DUPLICATE}): {hits or 'none'}")
    return 1 if failed or hits else 0


if __name__ == "__main__":
    sys.exit(main())
