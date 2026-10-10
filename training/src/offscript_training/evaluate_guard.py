"""Run the guard check (untuned base model) on a guard file and save raw replies + metrics.

Each row has the verdict our rules expect: "ok" (let it through to the router), "needs_detail"
or "two_questions". The key numbers are how many good questions the guard wrongly stops, and how
many questions it should stop that it lets through.

    uv run --env-file training/.env python -m offscript_training.evaluate_guard \\
        --data training/data/guard_dev.jsonl --out training/runs/guard/dev
"""

import argparse
import asyncio
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import tinker

from offscript_contract.guard import (
    GUARD_MAX_TOKENS,
    build_guard_messages,
    guard_prompt_version,
    parse_guard_output,
)
from offscript_contract.parsing import ModelOutputError
from offscript_contract.rendering import decode_completion, render_chat_prompt, stop_token_id
from offscript_contract.router import BASE_MODEL, TEMPERATURE
from offscript_training.data import refuse_sealed

CONCURRENCY = 8
VERDICTS = ("ok", "needs_detail", "two_questions")


def load_rows(path: Path) -> list[dict]:
    refuse_sealed(path)
    rows = [json.loads(line) for line in Path(path).read_text("utf-8").splitlines() if line.strip()]
    for row in rows:
        if row["expected"] not in VERDICTS:
            raise SystemExit(f"{path}: {row['id']} has unknown expected verdict {row['expected']}")
    return rows


async def run(rows: list[dict]) -> list[dict]:
    service = tinker.ServiceClient()
    client = await service.create_sampling_client_async(base_model=BASE_MODEL)
    tokenizer = client.get_tokenizer()
    params = tinker.SamplingParams(
        max_tokens=GUARD_MAX_TOKENS, temperature=TEMPERATURE, stop=[stop_token_id(tokenizer)]
    )
    gate = asyncio.Semaphore(CONCURRENCY)

    async def one(row: dict) -> dict:
        messages = build_guard_messages(row["question"], row["context"] or None)
        prompt = tinker.ModelInput.from_ints(render_chat_prompt(tokenizer, messages))
        async with gate:
            response = await client.sample_async(
                prompt=prompt, num_samples=1, sampling_params=params
            )
        text, complete = decode_completion(tokenizer, response.sequences[0].tokens)
        record = {**row, "raw": text, "verdict": None, "message": None, "error": None}
        try:
            output = parse_guard_output(text, complete=complete)
            record |= {"verdict": output.verdict.value, "message": output.message}
        except ModelOutputError as error:
            record["error"] = error.code
        return record

    return await asyncio.gather(*(one(row) for row in rows))


def compute(records: list[dict]) -> dict:
    should_pass = [r for r in records if r["expected"] == "ok"]
    should_stop = [r for r in records if r["expected"] != "ok"]
    confusion = {
        expected: dict(
            Counter(r["verdict"] or "invalid" for r in records if r["expected"] == expected)
        )
        for expected in VERDICTS
    }
    return {
        "questions": len(records),
        "passed_good": sum(r["verdict"] == "ok" for r in should_pass),
        "good_questions": len(should_pass),
        "wrongly_stopped_ids": [r["id"] for r in should_pass if r["verdict"] != "ok"],
        "caught": sum(r["verdict"] == r["expected"] for r in should_stop),
        "should_stop": len(should_stop),
        "missed_ids": [r["id"] for r in should_stop if r["verdict"] != r["expected"]],
        "invalid": sum(r["error"] is not None for r in records),
        "confusion": confusion,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    records = asyncio.run(run(load_rows(args.data)))
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "raw_outputs.jsonl").open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    metrics = {
        "model": BASE_MODEL,
        "data": str(args.data),
        "guard_prompt_version": guard_prompt_version(),
        "sampling": {"temperature": TEMPERATURE, "max_tokens": GUARD_MAX_TOKENS},
        "evaluated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **compute(records),
    }
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(
        f"guard {metrics['guard_prompt_version']}: good questions passed "
        f"{metrics['passed_good']}/{metrics['good_questions']}, should-stop caught "
        f"{metrics['caught']}/{metrics['should_stop']}, invalid {metrics['invalid']} → {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
