# Quick Start: Using Reusable Workflows

This guide helps teams set up the enterprise Hugging Face training pipeline using the canonical reusable workflow from the platform standard.

## Key Principle

**One canonical workflow, centrally maintained.** All teams reference the same `hf-mlops-pipeline.yml` from the platform repository. Updates happen automatically—no manual copying of workflow files.

## Prerequisites

- GitHub repository initialized with `.github/workflows/` directory
- `configs/train.yaml` with model, dataset, and hyperparameters
- `scripts/train.py`, `scripts/evaluate.py`, `scripts/check_gates.py` (can copy from `basic/scripts/`)
- `requirements.txt` with pinned dependencies
- JFrog Artifactory instance and API token (for publishing)

## 3-Minute Setup

### 1. Copy the Canonical Workflow to Your Repo

From the platform standard (`advanced/.github/workflows/`), copy to your repo:

```bash
cp advanced/.github/workflows/hf-mlops-pipeline.yml .github/workflows/
```

### 2. Create Your Calling Workflow (`.github/workflows/build.yml`)

```yaml
name: build

on:
  workflow_dispatch:
    inputs:
      model_version:
        description: "Model version (v1.0.0 or 20260325.1)"
        required: false
        type: string

jobs:
  pipeline:
    uses: ./.github/workflows/hf-mlops-pipeline.yml
    with:
      config_path: configs/train.yaml
      model_version: ${{ github.event.inputs.model_version }}
      skip_release: ${{ github.event.inputs.model_version == '' }}
    secrets:
      JFROG_URL: ${{ secrets.JFROG_URL }}
      JFROG_REPO: ${{ secrets.JFROG_REPO }}
      JFROG_TOKEN: ${{ secrets.JFROG_TOKEN }}
```

### 3. Set GitHub Secrets

In your GitHub repo settings (Settings → Secrets and variables → Actions), add:

- **`JFROG_URL`**: Your Artifactory base URL (e.g., `https://artifactory.yourcompany.com`)
- **`JFROG_REPO`**: Target repository name (e.g., `ml-models-release`)
- **`JFROG_TOKEN`**: Bearer token with push permissions

### 4. Create `production` Environment (For Approval Gate)

Optional but recommended for release control:

1. Go to Settings → Environments
2. Create environment `production`
3. Add required reviewers or deployment branch restrictions

### 5. Run Your First Pipeline

1. Go to Actions tab
2. Select "build" workflow
3. Click "Run workflow"
4. Enter model version (e.g., `v1.0.0`) to trigger release stage
5. Watch stages execute: train 🤖 → evaluate 🔍 → release 📦 → publish 🚀

---

## Project Structure

Your repo should have:

```
your-model-repo/
├── .github/
│   └── workflows/
│       ├── train.yml          (reusable, from platform)
│       ├── evaluate.yml       (reusable, from platform)
│       ├── release.yml        (reusable, from platform)
│       ├── publish.yml        (reusable, from platform)
│       └── build.yml          (YOUR calling workflow)
├── configs/
│   ├── train.yaml             (YOUR training config)
│   ├── quality_gates.yaml      (YOUR gate thresholds)
│   └── baseline_metrics.json   (YOUR baseline for regression detection)
├── scripts/
│   ├── train.py               (YOUR training script)
│   ├── evaluate.py            (YOUR evaluation script)
│   ├── check_gates.py         (YOUR gate checker)
│   └── package_model.py       (YOUR packaging script)
├── requirements.txt           (YOUR pinned dependencies)
└── README.md
```

---

## Training Configuration Template

Your `configs/train.yaml` should match this structure:

```yaml
# Model and dataset
model_name: prajjwal1/bert-tiny
dataset_name: ag_news

# Data parameters
train_size: 2000
eval_size: 500
seed: 42
text_column: text
label_column: label

# Training hyperparameters
num_train_epochs: 3
learning_rate: 2.0e-5
per_device_train_batch_size: 32
per_device_eval_batch_size: 32
weight_decay: 0.01

# Output paths
output_dir: artifacts/model
metrics_output_path: artifacts/metrics/train_metrics.json
max_length: 512
```

---

## Quality Gates Configuration Template

Your `configs/quality_gates.yaml`:

```yaml
# Absolute threshold gates
min_accuracy: 0.70
min_f1_macro: 0.70

# Baseline for regression detection
baseline_metrics_path: configs/baseline_metrics.json
```

Your `configs/baseline_metrics.json`:

```json
{
  "accuracy": 0.70,
  "f1_macro": 0.70
}
```

---

## Scripts: What to Implement

### `scripts/train.py`

Should implement:
- Load config from YAML
- Load dataset
- Tokenize text
- Train model with Hugging Face Trainer
- Compute metrics (accuracy, f1_macro, eval_loss)
- **Emit `artifacts/metrics/train_metrics.json` with all 11 required fields** (model_name, dataset_name, split, run_id, git_sha, timestamp_utc, config_hash, metric_contract_version)

```python
# See basic/scripts/train.py for full reference
normalized_metrics = {
    "accuracy": 0.85,
    "f1_macro": 0.83,
    "eval_loss": 0.32,
    "model_name": cfg.get("model_name", "unknown"),
    "dataset_name": cfg.get("dataset_name", "unknown"),
    "split": "train",
    "run_id": os.getenv("GITHUB_RUN_ID", "local"),
    "git_sha": get_git_sha(),  # From git or "unknown"
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "config_hash": compute_config_hash(args.config),
    "metric_contract_version": "1.0.0",
}
```

### `scripts/evaluate.py`

Should implement:
- Load trained model from `artifacts/model`
- Load dataset and test split
- Evaluate on test set
- Compute metrics
- **Emit `artifacts/metrics/eval_metrics.json` with all 11 required fields** (same as train.py, but split="test")

```python
# See basic/scripts/evaluate.py for full reference
normalized_metrics = {
    "accuracy": 0.82,
    "f1_macro": 0.80,
    "eval_loss": 0.48,
    "model_name": cfg.get("model_name", "unknown"),
    "dataset_name": cfg.get("dataset_name", "unknown"),
    "split": "test",
    "run_id": os.getenv("GITHUB_RUN_ID", "local"),
    "git_sha": get_git_sha(),
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "config_hash": compute_config_hash(args.config),
    "metric_contract_version": "1.0.0",
}
```

### `scripts/check_gates.py`

Should implement:
- Load metrics JSON
- Validate schema (all 11 required fields with correct types)
- Check absolute thresholds (accuracy ≥ min_accuracy, etc.)
- Check baseline regression (metrics didn't drop vs previous approved release)
- Exit with code 1 if any check fails

```python
# See basic/scripts/check_gates.py for full reference
parser.add_argument("--metrics", default="artifacts/metrics/eval_metrics.json")
parser.add_argument("--gates", default="configs/quality_gates.yaml")
parser.add_argument("--schema", default="advanced/schemas/metrics_schema.json")
```

### `scripts/package_model.py`

Should implement:
- Create tarball with model files, config, tokenizer, metadata
- Include JSON with git SHA, config hash, metrics, timestamp
- Output versioned tarball: `hf-bert-tiny-{version}.tar.gz`

```python
# See basic/scripts/package_model.py for reference
parser.add_argument("--version", required=True)  # e.g., v1.0.0
```

---

## Schema Requirements

All metrics must conform to `advanced/schemas/metrics_schema.json`. The 11 required fields:

| Field | Type | Format | Example |
|-------|------|--------|---------|
| accuracy | number | 0.0-1.0 | 0.85 |
| f1_macro | number | 0.0-1.0 | 0.83 |
| eval_loss | number | ≥0.0 | 0.32 |
| model_name | string | - | "prajjwal1/bert-tiny" |
| dataset_name | string | - | "ag_news" |
| split | enum | train\|validation\|test | "test" |
| run_id | string | - | "123456" |
| git_sha | string | ^[a-f0-9]{7,40}$ | "abc1234" |
| timestamp_utc | string | ISO 8601 | "2026-03-25T14:32:15.123456+00:00" |
| config_hash | string | ^sha256:[a-f0-9]{64}$ | "sha256:4f53cda..." |
| metric_contract_version | string | semver ^d.d.d | "1.0.0" |

---

## Testing Locally

### Run Training Script Directly

```bash
python scripts/train.py --config configs/train.yaml
# Creates: artifacts/model/, artifacts/metrics/train_metrics.json
```

### Run Evaluation Script Directly

```bash
python scripts/evaluate.py --config configs/train.yaml \
  --model-dir artifacts/model \
  --output artifacts/metrics/eval_metrics.json
```

### Check Quality Gates

```bash
python scripts/check_gates.py \
  --metrics artifacts/metrics/eval_metrics.json \
  --gates configs/quality_gates.yaml \
  --schema advanced/schemas/metrics_schema.json
```

---

## Workflow Anatomy

### Stage 1: Train

- Runs on: `ubuntu-latest` (configurable)
- Python: 3.11 (configurable)
- Outputs: `trained-model` artifact, `train-metrics` artifact (5-day retention)
- Duration: 5-20 minutes (depends on dataset size and hardware)

### Stage 2: Evaluate

- Depends on: Train stage
- Downloads: trained model
- Runs: evaluation + schema validation + threshold gates + baseline regression check
- Outputs: `eval-metrics` artifact (5-day retention)
- Duration: 3-10 minutes
- **Fails if any gate fails** (schema validation fails first, then thresholds, then baseline)

### Stage 3: Release

- Depends on: Evaluate stage
- Only runs: if `model_version` input provided
- Downloads: model, eval metrics
- Re-checks: gates (redundant safety check)
- Runs: packaging script
- Outputs: `release-package` artifact (30-day retention, not auto-deleted)
- Duration: 2-5 minutes

### Stage 4: Publish

- Depends on: Release stage
- Environment: `production` (approval gate in GitHub UI)
- Requires: JFROG secrets
- Uploads: package and checksum to Artifactory
- Duration: 1-2 minutes

---

## Customization Examples

### Use Different Python Version

```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/train.yaml
    model_version: ${{ github.event.inputs.model_version }}
    python_version: "3.12"
```

### Use Self-Hosted GPU Runner

```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/train.yaml
    runs_on: [self-hosted, gpu]
```

### Use Custom Script Paths

For teams with different folder structures or naming conventions:

```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/train.yaml
    train_script_path: ml/train_model.py           # Custom train script
    evaluate_script_path: ml/evaluate_model.py     # Custom evaluate script
    check_gates_script_path: ml/validate_gates.py  # Custom gates script
    package_script_path: ml/package.py             # Custom package script
```

### CI on Pull Requests (Skip Release)

```yaml
# .github/workflows/ci.yml
name: ci-pr

on:
  pull_request:

jobs:
  pipeline:
    uses: ./.github/workflows/hf-mlops-pipeline.yml
    with:
      config_path: configs/train.yaml
      skip_release: true  # Train + evaluate only
```

### Only Publish on Version Tags

```yaml
pipeline:
  if: startsWith(github.ref, 'refs/tags/v')
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/train.yaml
    model_version: ${{ github.ref_name }}
```

---

## Workflow Anatomy

### Default Flow (with release)

```
INPUT: model_version = "v1.0.0"
       skip_release = false

┌──────────────────────┐
│ TRAIN (🤖)           │ Always runs
│ • Run training       │
│ • Emit metrics       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ EVALUATE (🔍)        │ Always runs
│ • Validate schema    │ (Fails if gates fail)
│ • Check gates        │
│ • Detect regression  │
└──────┬───────────────┘
       │
       ▼ (if model_version != "")
┌──────────────────────┐
│ RELEASE (📦)         │ Conditional
│ • Re-check gates     │
│ • Package model      │
└──────┬───────────────┘
       │
       ▼ (requires approval)
┌──────────────────────┐
│ PUBLISH (🚀)         │ Conditional
│ • Upload to JFrog    │ + Approval Gate
└──────────────────────┘

RESULT: ✅ Model trained, evaluated, packaged, and published
```

### CI Flow (skip release)

```
INPUT: model_version = ""
       skip_release = true

┌──────────────────────┐
│ TRAIN (🤖)           │ Always runs
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ EVALUATE (🔍)        │ Always runs
└──────────────────────┘

All metrics preserved in artifacts (5-day retention)
No packaging or publishing

RESULT: ✅ Model trained and evaluated (can test, abandon, or manually release later)
```

---

## Testing Locally

### Run Training Script Directly

```bash
python scripts/train.py --config configs/train.yaml
# Creates: artifacts/model/, artifacts/metrics/train_metrics.json
```

### Run Evaluation Script Directly

```bash
python scripts/evaluate.py \
  --config configs/train.yaml \
  --model-dir artifacts/model \
  --output artifacts/metrics/eval_metrics.json
```

### Check Quality Gates

```bash
python scripts/check_gates.py \
  --metrics artifacts/metrics/eval_metrics.json \
  --gates configs/quality_gates.yaml \
  --schema advanced/schemas/metrics_schema.json
```

---

## Next Steps

1. **Copy canonical workflow** from `advanced/.github/workflows/hf-mlops-pipeline.yml`
2. **Implement your scripts** (train.py, evaluate.py, check_gates.py, package_model.py)
3. **Create configs** (train.yaml, quality_gates.yaml, baseline_metrics.json)
4. **Set GitHub secrets** for JFrog (JFROG_URL, JFROG_REPO, JFROG_TOKEN)
5. **Create production environment** with approval rules
6. **Test locally** with `workflow_dispatch`
7. **Monitor first runs** (check logs for any gate failures)

---

## References

- [Full Reusable Workflow Documentation](./REUSABLE_WORKFLOWS.md)
- [Platform Standard](./docs/PLATFORM_STANDARD.md)
- [Metric Schema](./schemas/metrics_schema.json)
- [Training Script Example](../basic/scripts/train.py)
- [Evaluation Script Example](../basic/scripts/evaluate.py)

---

## FAQ

### Do I need to copy workflows to my repo?

**For now, yes.** Copy `hf-mlops-pipeline.yml` to your repo's `.github/workflows/` folder.

In the future, you can use cross-repo reference without copying:
```yaml
uses: org/platform-repo/.github/workflows/hf-mlops-pipeline.yml@main
```

This way you get automatic updates—no manual copying ever again.

### What if I want to customize the workflow?

**Override inputs instead of modifying the workflow:**
```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/my-custom-train.yaml  # ← Custom config
    python_version: "3.12"                      # ← Custom Python
    runs_on: [self-hosted, gpu]                 # ← Custom runner
```

If you need different logic, submit a feature request to the platform team.

### How do I know if my metrics conform to the schema?

Run check_gates.py locally:

```bash
python scripts/check_gates.py \
  --metrics artifacts/metrics/eval_metrics.json \
  --gates configs/quality_gates.yaml \
  --schema advanced/schemas/metrics_schema.json
```

If you see field validation errors, update your scripts to emit all 11 required fields.
