# Hugging Face Build Starter

This project trains a very basic and fast text classifier using Hugging Face with workflow-first automation.

## Selected Starter Model
- Model: `prajjwal1/bert-tiny`
- Dataset: `ag_news`
- Fast setup: train on only 500 samples for 1 epoch

## Quick Local Run
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/train.py --config configs/train.yaml
python scripts/evaluate.py --config configs/train.yaml --model-dir artifacts/model --output artifacts/metrics/eval_metrics.json
python scripts/check_gates.py --metrics artifacts/metrics/eval_metrics.json --gates configs/quality_gates.yaml
```

## Why Each Step Exists
1. Install pinned dependencies
- What to do: install from `requirements.txt`.
- Why it matters: pinned versions reduce environment drift and improve reproducibility.

2. Train with deterministic config
- What to do: run `scripts/train.py` with `configs/train.yaml`.
- Why it matters: tracked config + random seed produce consistent, auditable training runs.

3. Evaluate and export metrics
- What to do: run `scripts/evaluate.py` to produce `eval_metrics.json`.
- Why it matters: metrics become machine-readable inputs for CI/CD quality gates.

4. Enforce quality gates
- What to do: run `scripts/check_gates.py`.
- Why it matters: blocks regressions by requiring both threshold checks and baseline comparison.

5. Package release artifact
- What to do: run `scripts/package_model.py --version <version>`.
- Why it matters: bundles model, config, metrics, metadata, and checksum for traceable release.

## GitHub Workflows
- CI workflow: lint/tests and config checks.
- Train workflow: manual training run with uploaded artifacts.
- Evaluate workflow: manual evaluation and quality-gate enforcement.
- Release workflow: manual approved publish to JFrog Artifactory.
