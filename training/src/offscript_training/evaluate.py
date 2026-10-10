"""Run the base or a tuned router on an evaluation file and save raw replies + metrics.

Base and tuned runs use the identical prompt, renderer and sampling settings (temperature 0).

    uv run --env-file training/.env python -m offscript_training.evaluate --base \\
        --data training/data/test_sealed.jsonl --out training/runs/baseline
    uv run --env-file training/.env python -m offscript_training.evaluate \\
        --model-path tinker://.../sampler_weights/... --out training/runs/<run>/eval
    uv run --env-file training/.env python -m offscript_training.evaluate --base --prompt v2 \\
        --data training/data/test_sealed_v2.jsonl --out training/runs/baseline-v2
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import tinker

from offscript_contract.parsing import ModelOutputError
from offscript_contract.rendering import decode_completion, render_chat_prompt, stop_token_id
from offscript_contract.router import (
    BASE_MODEL,
    MAX_TOKENS,
    ROUTER_PROMPT,
    ROUTER_PROMPT_V2,
    TEMPERATURE,
    build_router_messages,
    parse_router_output,
    router_prompt_version,
)
from offscript_training.data import SEALED_FILE, load_eval_rows
from offscript_training.metrics import compute

CONCURRENCY = 8


PROMPTS = {"v1": ROUTER_PROMPT, "v2": ROUTER_PROMPT_V2}


async def run(
    rows: list[dict], model_path: str | None, router_prompt: str = ROUTER_PROMPT
) -> list[dict]:
    service = tinker.ServiceClient()
    if model_path:
        client = await service.create_sampling_client_async(model_path=model_path)
    else:
        client = await service.create_sampling_client_async(base_model=BASE_MODEL)
    tokenizer = client.get_tokenizer()
    params = tinker.SamplingParams(
        max_tokens=MAX_TOKENS, temperature=TEMPERATURE, stop=[stop_token_id(tokenizer)]
    )
    gate = asyncio.Semaphore(CONCURRENCY)

    async def one(row: dict) -> dict:
        messages = build_router_messages(row["question"], row["context"], prompt=router_prompt)
        prompt = tinker.ModelInput.from_ints(render_chat_prompt(tokenizer, messages))
        async with gate:
            response = await client.sample_async(
                prompt=prompt, num_samples=1, sampling_params=params
            )
        text, complete = decode_completion(tokenizer, response.sequences[0].tokens)
        record = {**row, "raw": text, "complete": complete, "error": None, "reply": None}
        try:
            reply = parse_router_output(text, complete=complete)
            record |= {"predicted": reply.route.value, "reply": reply.model_dump(mode="json")}
        except ModelOutputError as error:
            record |= {"predicted": None, "error": error.code}
        return record

    return await asyncio.gather(*(one(row) for row in rows))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--base", action="store_true", help=f"untuned {BASE_MODEL}")
    which.add_argument("--model-path", help="tinker:// sampler checkpoint path")
    parser.add_argument("--data", type=Path, default=SEALED_FILE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prompt", choices=sorted(PROMPTS), default="v1", help="router prompt")
    args = parser.parse_args(argv)
    prompt = PROMPTS[args.prompt]

    rows = load_eval_rows(args.data)
    records = asyncio.run(run(rows, args.model_path, prompt))
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "raw_outputs.jsonl").open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    metrics = {
        "model": args.model_path or BASE_MODEL,
        "data": str(args.data),
        "router_prompt": prompt,
        "router_prompt_version": router_prompt_version(prompt),
        "sampling": {"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS},
        "evaluated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **compute(records),
    }
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    summary = metrics["all"]
    print(
        f"{metrics['model']}: accuracy {summary['accuracy']} ({summary['correct']}/"
        f"{summary['questions']}), invalid {summary['invalid_outputs']}, "
        f"inappropriate HUMAN {summary['inappropriate_human_referrals']} → {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
