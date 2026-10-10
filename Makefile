.DEFAULT_GOAL := help
.PHONY: help install dev dev-api dev-web health smoke-test check-data baseline train evaluate report check-data-v2 baseline-v2 train-v2 evaluate-v2 report-v2 evaluate-guard test test-live test-py test-web lint format

API_PORT ?= 8000

help: ## List commands
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## Install all Python (uv) and web (npm) dependencies + git hooks
	uv sync --all-packages
	cd web && npm ci
	uv run pre-commit install

dev: ## Run API and web together
	$(MAKE) -j2 dev-api dev-web

dev-api: ## Run the API with reload on :$(API_PORT)
	cd api && uv run uvicorn offscript_api.main:app --reload --port $(API_PORT)

dev-web: ## Run the web dev server on :5173
	cd web && npm run dev

health: ## Check the running API's /health
	curl -fsS http://localhost:$(API_PORT)/health && echo

smoke-test: ## Live Tinker check: sample, tiny train, save (needs training/.env, costs cents)
	uv run --env-file training/.env python -m offscript_training.smoke_test

RUN ?= sft-v1
TRAIN_ENV = uv run --env-file training/.env python -m offscript_training

check-data: ## Validate train + sealed files and check they don't overlap
	uv run python -m offscript_training.data

baseline: ## Untuned model on the sealed set → training/runs/baseline (costs cents)
	$(TRAIN_ENV).evaluate --base --out training/runs/baseline

train: ## LoRA fine-tune → training/runs/$(RUN) (costs about $$1)
	$(TRAIN_ENV).train --name $(RUN)

evaluate: ## Tuned model on the sealed set (MODEL_PATH=tinker://...) → training/runs/$(RUN)/eval
	$(TRAIN_ENV).evaluate --model-path $(MODEL_PATH) --out training/runs/$(RUN)/eval

report: ## Base vs tuned comparison → training/runs/REPORT.md
	uv run python -m offscript_training.report training/runs/baseline training/runs/$(RUN)/eval > training/runs/REPORT.md

check-data-v2: ## Validate the v2 data, metadata and v2 sealed set; check overlaps
	uv run python -m offscript_training.data --v2

baseline-v2: ## Untuned model with the v2 prompt on both sealed sets → training/runs/baseline-v2 (costs cents)
	$(TRAIN_ENV).evaluate --base --prompt v2 --data training/data/test_sealed_v2.jsonl --out training/runs/baseline-v2/sealed-v2
	$(TRAIN_ENV).evaluate --base --prompt v2 --data training/data/test_sealed.jsonl --out training/runs/baseline-v2/sealed-v1

train-v2: ## LoRA fine-tune on the v2 data (family split) → training/runs/$(RUN) (costs a few dollars)
	$(TRAIN_ENV).train --name $(RUN) --dataset v2 --num-epochs 2 --eval-every 10 --save-every 10

evaluate-v2: ## Tuned v2 model on both sealed sets (MODEL_PATH=tinker://...) → training/runs/$(RUN)/eval-*
	$(TRAIN_ENV).evaluate --model-path $(MODEL_PATH) --prompt v2 --data training/data/test_sealed_v2.jsonl --out training/runs/$(RUN)/eval-sealed-v2
	$(TRAIN_ENV).evaluate --model-path $(MODEL_PATH) --prompt v2 --data training/data/test_sealed.jsonl --out training/runs/$(RUN)/eval-sealed-v1

report-v2: ## Base vs tuned v2 on the v2 sealed set → training/runs/REPORT_V2.md
	uv run python -m offscript_training.report training/runs/baseline-v2/sealed-v2 training/runs/$(RUN)/eval-sealed-v2 > training/runs/REPORT_V2.md

evaluate-guard: ## Guard check on the dev and held-out guard sets → training/runs/guard/$(RUN) (costs cents)
	$(TRAIN_ENV).evaluate_guard --data training/data/guard_dev.jsonl --out training/runs/guard/$(RUN)/dev
	$(TRAIN_ENV).evaluate_guard --data training/data/guard_check.jsonl --out training/runs/guard/$(RUN)/check

test: test-py test-web ## Run all tests

test-live: ## Network tests: renderer/tokenizer parity with Tinker (needs training/.env)
	uv run --env-file training/.env pytest -m live training

test-py:
	uv run pytest api contract training

test-web:
	cd web && npm test

lint: ## Lint + format check + type check
	uv run ruff check .
	uv run ruff format --check .
	cd web && npm run lint && npm run format:check && npm run typecheck

format: ## Auto-format Python and web
	uv run ruff check --fix .
	uv run ruff format .
	cd web && npm run format
