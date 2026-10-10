"""LoRA fine-tuning of the router on Tinker with the cookbook's supervised trainer.

Writes the run to training/runs/<name>/: run_config.json (ours: model, prompt version, data,
settings), the cookbook's config.json, metrics.jsonl and checkpoints.jsonl (tinker:// paths, no
weights), and run_summary.json. v2 runs also write split.json (the held-out families).

    uv run --env-file training/.env python -m offscript_training.train --name sft-v1
    uv run --env-file training/.env python -m offscript_training.train --name dry-run --max-steps 2
    uv run --env-file training/.env python -m offscript_training.train --name sft-v2 --dataset v2 \\
        --num-epochs 2 --eval-every 10 --save-every 10
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from tinker_cookbook import hyperparam_utils
from tinker_cookbook.renderers import TrainOnWhat
from tinker_cookbook.supervised import train
from tinker_cookbook.supervised.data import FromConversationFileBuilder
from tinker_cookbook.supervised.types import ChatDatasetBuilderCommonConfig

from offscript_contract.router import (
    BASE_MODEL,
    RENDERER_NAME,
    ROUTER_PROMPT,
    ROUTER_PROMPT_V2,
    router_prompt_version,
)
from offscript_training.data import (
    TRAIN_FILE,
    V2_TRAIN_FILE,
    family_split,
    load_train,
    load_v2_metadata,
    refuse_sealed,
    to_conversation,
)

RUNS = Path("training/runs")
DATASETS = {"v1": (TRAIN_FILE, ROUTER_PROMPT), "v2": (V2_TRAIN_FILE, ROUTER_PROMPT_V2)}
DEFAULTS = {
    "lora_rank": 32,
    "learning_rate": round(hyperparam_utils.get_lr(BASE_MODEL), 6),
    "lr_schedule": "linear",
    "num_epochs": 4,
    "batch_size": 16,
    "validation_rows": 15,  # v1: random rows held out
    "validation_fraction": 0.1,  # v2: share of scenario families held out
    "max_length": 2048,
    "seed": 0,
    "eval_every": 3,
    "save_every": 6,
}


def build_config(
    name: str, train_file: Path, settings: dict, max_steps: int | None, dataset: str = "v1"
):
    refuse_sealed(train_file)
    run_dir = RUNS / name
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = DATASETS[dataset][1]
    examples = load_train(train_file)
    if dataset == "v2":
        # Validation families go first and the cookbook's own shuffle is off, so the first
        # `test_size` rows are exactly the held-out families.
        rows, validation = family_split(
            examples, load_v2_metadata(), settings["validation_fraction"], settings["seed"]
        )
        ordered, test_size, shuffle_seed = validation + rows, len(validation), None
        (run_dir / "split.json").write_text(
            json.dumps({"validation_ids": [e.id for e in validation]}, indent=2) + "\n"
        )
    else:
        ordered, test_size, shuffle_seed = examples, settings["validation_rows"], settings["seed"]
    conversations = run_dir / "train_conversations.jsonl"
    with conversations.open("w", encoding="utf-8") as out:
        for example in ordered:
            out.write(json.dumps(to_conversation(example, prompt), ensure_ascii=False) + "\n")
    record = {
        "base_model": BASE_MODEL,
        "renderer": RENDERER_NAME,
        "dataset": dataset,
        "router_prompt": prompt,
        "router_prompt_version": router_prompt_version(prompt),
        "train_file": str(train_file),
        "train_rows": len(examples),
        "held_out_rows": test_size,
        "max_steps": max_steps,
        **settings,
    }
    (run_dir / "run_config.json").write_text(json.dumps(record, indent=2) + "\n")
    builder = FromConversationFileBuilder(
        file_path=str(conversations),
        test_size=test_size,
        shuffle_seed=shuffle_seed,
        common_config=ChatDatasetBuilderCommonConfig(
            model_name_for_tokenizer=BASE_MODEL,
            renderer_name=RENDERER_NAME,
            max_length=settings["max_length"],
            batch_size=settings["batch_size"],
            train_on_what=TrainOnWhat.LAST_ASSISTANT_MESSAGE,
        ),
    )
    config = train.Config(
        log_path=str(run_dir),
        model_name=BASE_MODEL,
        recipe_name="offscript_router_sft",
        renderer_name=RENDERER_NAME,
        dataset_builder=builder,
        learning_rate=settings["learning_rate"],
        lr_schedule=settings["lr_schedule"],
        num_epochs=settings["num_epochs"],
        lora_rank=settings["lora_rank"],
        eval_every=settings["eval_every"],
        save_every=settings["save_every"],
        # The real run's checkpoints must not expire (the app uses one); a dry run's may.
        ttl_seconds=24 * 3600 if max_steps else None,
        max_steps=max_steps,
    )
    return run_dir, config


def summarise(run_dir: Path) -> dict:
    """Final sampler checkpoint and last metrics, read from the cookbook's log files."""
    checkpoints = [
        json.loads(line)
        for line in (run_dir / "checkpoints.jsonl").read_text().splitlines()
        if line.strip()
    ]
    samplers = [c for c in checkpoints if c.get("sampler_path")]
    samplers.sort(key=lambda c: bool(c.get("final")))  # the final checkpoint wins if present
    metrics = [
        json.loads(line)
        for line in (run_dir / "metrics.jsonl").read_text().splitlines()
        if line.strip()
    ]
    summary = {
        "final_sampler_path": samplers[-1]["sampler_path"] if samplers else None,
        "checkpoints": checkpoints,
        "last_metrics": metrics[-1] if metrics else None,
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", required=True, help="run folder under training/runs/")
    parser.add_argument("--dataset", choices=sorted(DATASETS), default="v1")
    parser.add_argument("--train-file", type=Path, help="defaults to the dataset's file")
    parser.add_argument("--max-steps", type=int, help="stop early (dry run)")
    for key, value in DEFAULTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", type=type(value), default=value)
    args = parser.parse_args(argv)
    settings = {key: getattr(args, key) for key in DEFAULTS}
    train_file = args.train_file or DATASETS[args.dataset][0]
    run_dir, config = build_config(args.name, train_file, settings, args.max_steps, args.dataset)
    if (run_dir / "metrics.jsonl").exists():
        print(f"{run_dir} already has a run; choose a new --name.")
        return 1
    asyncio.run(train.main(config))
    summary = summarise(run_dir)
    print(f"final sampler checkpoint: {summary['final_sampler_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
