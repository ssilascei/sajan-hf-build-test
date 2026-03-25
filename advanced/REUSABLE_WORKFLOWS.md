# Reusable GitHub Workflows

This directory contains the canonical, enterprise-grade reusable workflow for Hugging Face model training, evaluation, packaging, and publishing to JFrog Artifactory.

## Overview

The **single reusable workflow** `hf-mlops-pipeline.yml` implements the complete 4-stage training pipeline specified in [PLATFORM_STANDARD.md](../docs/PLATFORM_STANDARD.md):

1. **Train** — Fine-tune model on training data
2. **Evaluate** — Run evaluation and quality gates
3. **Release** — Package approved model
4. **Publish** — Upload to JFrog Artifactory with approval

All 4 stages run as separate **jobs** within the same workflow, enabling:
- Artifact reuse across jobs (train outputs model → evaluate downloads model → release downloads model)
- Single approval gate for entire pipeline
- Centralized logic updates
- Clear job dependencies and conditional execution

## Why One Workflow Instead of Four?

### ✅ Single Source of Truth
- All logic lives in one place: `advanced/.github/workflows/hf-mlops-pipeline.yml`
- No duplication across 4 separate files
- Bug fixes and improvements update everywhere automatically

### ✅ Automatic Updates
- Teams **reference** the workflow, don't copy it
- Platform team updates once; all teams benefit
- No manual migration needed (teams call the same workflow)

### ✅ Clear Orchestration
- All 4 stages are jobs in one file with clear dependencies
- Easy to understand flow: train → evaluate → release → publish
- Conditional logic for skipping release/publish on CI runs

### ✅ Simplified for Teams
- Teams call **one workflow** from their `build.yml`
- One set of inputs/outputs to learn
- Fewer decisions about workflow orchestration

---

## Reusable Workflow Reference: `hf-mlops-pipeline.yml`

Complete MLOps pipeline orchestration with 4 stages as separate jobs that run sequentially.

### How to Use

Teams copy this workflow into their `.github/workflows/` directory and call it from their build workflow:

```yaml
# Example: .github/workflows/build.yml
name: build

on:
  workflow_dispatch:
    inputs:
      model_version:
        description: "Model version (v1.0.0)"
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

Or call from an external platform repo using cross-repo reference:

```yaml
# Example: Team's build.yml calling platform repo workflow
jobs:
  pipeline:
    uses: org/platform-repo/.github/workflows/hf-mlops-pipeline.yml@main
    with:
      config_path: configs/train.yaml
      model_version: ${{ github.event.inputs.model_version }}
    secrets:
      JFROG_URL: ${{ secrets.JFROG_URL }}
      JFROG_REPO: ${{ secrets.JFROG_REPO }}
      JFROG_TOKEN: ${{ secrets.JFROG_TOKEN }}
```

### Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `config_path` | string | `configs/train.yaml` | ❌ | Path to training config |
| `train_script_path` | string | `scripts/train.py` | ❌ | Path to training script |
| `evaluate_script_path` | string | `scripts/evaluate.py` | ❌ | Path to evaluation script |
| `check_gates_script_path` | string | `scripts/check_gates.py` | ❌ | Path to quality gates checker script |
| `package_script_path` | string | `scripts/package_model.py` | ❌ | Path to packaging script |
| `skip_release` | boolean | `false` | ❌ | Skip release/publish (useful for CI on PRs) |
| `model_version` | string | `""` | ❌ if skip_release=true | Model version (v1.0.0, 20260325.1, etc.). Required for release stage |
| `python_version` | string | `3.11` | ❌ | Python version |
| `runs_on` | string | `ubuntu-latest` | ❌ | Runner label (ubuntu-latest or self-hosted,gpu) |
| `model_artifact_dir` | string | `artifacts/model` | ❌ | Directory where model is saved |
| `train_metrics_path` | string | `artifacts/metrics/train_metrics.json` | ❌ | Training metrics JSON path |
| `eval_metrics_path` | string | `artifacts/metrics/eval_metrics.json` | ❌ | Evaluation metrics JSON path |
| `schema_path` | string | `advanced/schemas/metrics_schema.json` | ❌ | Path to metrics schema JSON |

### Secrets

| Name | Required | Description |
|------|----------|-------------|
| `JFROG_URL` | ❌ (if skip_release=true) | JFrog Artifactory base URL |
| `JFROG_REPO` | ❌ (if skip_release=true) | JFrog target repository |
| `JFROG_TOKEN` | ❌ (if skip_release=true) | JFrog API token (Bearer auth) |

### Job Flow

```
┌─────────────────────────────────────────────────────────────┐
│ TRAIN (🤖)                                                  │
│ • Runs training script                                      │
│ • Uploads: trained-model, train-metrics (5-day retention)   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ EVALUATE (🔍)                                               │
│ • Downloads trained model                                   │
│ • Validates schema (11 required metric fields)              │
│ • Checks thresholds (accuracy, f1_macro)                    │
│ • Detects regressions (vs baseline)                         │
│ • Uploads: eval-metrics (5-day retention)                   │
│ • FAILS if any gate fails (fail-fast)                       │
└──────────────────┬──────────────────────────────────────────┘
                   │ (only if model_version != "" and skip_release=false)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ RELEASE (📦)                                                │
│ • Downloads model + eval metrics                            │
│ • Re-checks gates (safety redundancy)                       │
│ • Packages into versioned tarball                           │
│ • Uploads: release-package (30-day retention)               │
└──────────────────┬──────────────────────────────────────────┘
                   │ (only if model_version != "" and skip_release=false)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ PUBLISH (🚀) -- environment: production                     │
│ • REQUIRES APPROVAL (GitHub UI)                             │
│ • Downloads release package                                 │
│ • Uploads to JFrog Artifactory                              │
│ • Uploads SHA256 checksum                                   │
└─────────────────────────────────────────────────────────────┘
```

### Stage Details

#### Stage 1: TRAIN (🤖)

Trains model using `scripts/train.py`.

**Outputs:**
- `trained-model` artifact (5-day retention)
- `train_metrics_artifact` artifact (5-day retention)

**Environment:**
- Python version: configurable
- Runner: configurable
- Caches pip dependencies across runs

**Script requirements:**
- `scripts/train.py` must emit metrics to `artifacts/metrics/train_metrics.json` with all 11 required fields
- See [Platform Standard: Metric Contract](#predefined-contracts)

#### Stage 2: EVALUATE (🔍)

Evaluates model on test set with strict quality gates.

**Downloads:**
- `trained-model` artifact from train stage

**Validation (fail-fast):**
1. Schema validation: All 11 required metric fields with correct types
2. Threshold gates: accuracy ≥ min_accuracy, f1_macro ≥ min_f1_macro (from `configs/quality_gates.yaml`)
3. Baseline regression: Metrics didn't drop below previous approved baseline (from `configs/baseline_metrics.json`)

**Outputs:**
- `eval-metrics` artifact (5-day retention)

**Script requirements:**
- `scripts/evaluate.py` must emit metrics with all 11 required fields
- `scripts/check_gates.py` must support `--schema` argument for validation

#### Stage 3: RELEASE (📦)

Packages approved model for distribution.

**Downloads:**
- `trained-model` artifact
- `eval-metrics` artifact

**Execution:**
1. Re-checks quality gates (redundant safety check)
2. Runs `scripts/package_model.py --version <version>`
3. Creates tarball: `hf-bert-tiny-<version>.tar.gz`

**Outputs:**
- `release-package` artifact (30-day retention, not auto-deleted)

**Conditional execution:**
- Skips if `skip_release=true` (useful for CI on PRs)
- Skips if `model_version` is empty or null
- Skips if evaluate stage failed

#### Stage 4: PUBLISH (🚀)

Publishes model to JFrog with approval gate.

**Downloads:**
- `release-package` artifact

**Execution:**
1. Validates JFrog secrets (fails if missing)
2. Uploads `hf-bert-tiny-<version>.tar.gz` to JFrog
3. Uploads `hf-bert-tiny-<version>.tar.gz.sha256` checksum

**Environment:**
- Required: `production` environment (GitHub approval gate)
- Manual approval shown in GitHub UI before publishing

**Conditional execution:**
- Skips if `skip_release=true`
- Skips if `model_version` is empty or null
- Requires approval gate to proceed

### Metric Schema

All workflows enforce the metric contract defined in `advanced/schemas/metrics_schema.json`. Metrics must include:

```json
{
  "accuracy": 0.85,
  "f1_macro": 0.83,
  "eval_loss": 0.32,
  "model_name": "prajjwal1/bert-tiny",
  "dataset_name": "ag_news",
  "split": "test",
  "run_id": "123456",
  "git_sha": "abc1234",
  "timestamp_utc": "2026-03-25T14:32:15.123456+00:00",
  "config_hash": "sha256:4f53cda18c169b1fa2cc0b7e8c2f8c69...",
  "metric_contract_version": "1.0.0"
}
```

See `advanced/schemas/metrics_schema.json` for complete schema definition.

### Quality Gates

Evaluate workflow enforces gates specified in `configs/quality_gates.yaml`:

```yaml
min_accuracy: 0.70
min_f1_macro: 0.70
baseline_metrics_path: configs/baseline_metrics.json
```

Metrics must:
1. **Pass threshold gates**: accuracy ≥ 0.70, f1_macro ≥ 0.70
2. **Pass baseline regression gates**: not drop below previous approved baseline
3. **Conform to schema**: all 11 required fields present with correct types

---

## Customization Guide

### Override Inputs per Workflow Call

```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/custom-train.yaml
    python_version: "3.12"
    runs_on: ubuntu-22.04
    skip_release: false
```

### Use Different Runners

```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    runs_on: [self-hosted, gpu-capable]  # Use self-hosted GPU runner
```

### Skip Release on CI Runs

```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/train.yaml
    skip_release: true  # TRAIN + EVALUATE only, no packaging or publishing
```

### Conditional Publishing

```yaml
# Only publish releases from version tags
pipeline:
  if: startsWith(github.ref, 'refs/tags/v')
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    model_version: ${{ github.ref_name }}
```

### Use Custom Script Paths

For teams with different folder structures or script naming conventions:

```yaml
pipeline:
  uses: ./.github/workflows/hf-mlops-pipeline.yml
  with:
    config_path: configs/train.yaml
    train_script_path: ml/train_model.py              # ← Custom train script
    evaluate_script_path: ml/evaluate_model.py        # ← Custom evaluate script
    check_gates_script_path: ml/validate_gates.py     # ← Custom gates script
    package_script_path: ml/package_release.py        # ← Custom package script
```

---

## Common Patterns

### Pattern 1: CI on Pull Requests

Run train + evaluate only (no release/package):

```yaml
name: ci

on:
  pull_request:

jobs:
  pipeline:
    uses: ./.github/workflows/hf-mlops-pipeline.yml
    with:
      config_path: configs/train.yaml
      skip_release: true  # ← Skip release stage
```

### Pattern 2: Manual Release Promotion

```yaml
name: release

on:
  workflow_dispatch:
    inputs:
      version:
        description: Version to release
        required: true

jobs:
  pipeline:
    uses: ./.github/workflows/hf-mlops-pipeline.yml
    with:
      config_path: configs/train.yaml
      model_version: ${{ github.event.inputs.version }}
      skip_release: false
    secrets:
      JFROG_URL: ${{ secrets.JFROG_URL }}
      JFROG_REPO: ${{ secrets.JFROG_REPO }}
      JFROG_TOKEN: ${{ secrets.JFROG_TOKEN }}
```

### Pattern 3: Scheduled Retraining

```yaml
name: scheduled-retrain

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM UTC

jobs:
  pipeline:
    uses: ./.github/workflows/hf-mlops-pipeline.yml
    with:
      config_path: configs/train.yaml
      model_version: ${{ github.run_number }}  # Use run number as version
```

### Pattern 4: Cross-Repo Reference (Platform Pattern)

If the workflow lives in a central platform repo:

```yaml
# Team's repo: .github/workflows/build.yml
name: build

on:
  workflow_dispatch:
    inputs:
      model_version:
        required: false
        type: string

jobs:
  pipeline:
    # Reference platform repo workflow
    uses: org/platform-mlops/.github/workflows/hf-mlops-pipeline.yml@main
    with:
      config_path: configs/train.yaml
      model_version: ${{ github.event.inputs.model_version }}
      skip_release: ${{ github.event.inputs.model_version == '' }}
    secrets:
      JFROG_URL: ${{ secrets.JFROG_URL }}
      JFROG_REPO: ${{ secrets.JFROG_REPO }}
      JFROG_TOKEN: ${{ secrets.JFROG_TOKEN }}
```

---

## Troubleshooting

### Workflow Not Found

**Problem**: `Error: Could not resolve action: ./.github/workflows/hf-mlops-pipeline.yml`

**Solution**: 
- Ensure workflow file exists at `.github/workflows/hf-mlops-pipeline.yml`
- For cross-repo reference, use correct format: `uses: org/repo/.github/workflows/file.yml@ref`
- Do not use `file://` or `vscode://` URIs

### Inputs Not Recognized

**Problem**: `Error: Unexpected input 'config_path'`

**Solution**: 
- Verify input names match exactly (case-sensitive)
- Check [Reusable Workflow Reference](#reusable-workflow-reference-hf-mlops-pipelineyml) for valid inputs
- Ensure `on.workflow_call.inputs` section exists in workflow file

### Secrets Not Available

**Problem**: JFrog token shows as empty/missing

**Solution**:
1. Go to repo Settings → Secrets and variables → Actions
2. Verify `JFROG_URL`, `JFROG_REPO`, `JFROG_TOKEN` exist
3. Pass secrets explicitly in `with:` section:
   ```yaml
   secrets:
     JFROG_URL: ${{ secrets.JFROG_URL }}
     JFROG_REPO: ${{ secrets.JFROG_REPO }}
     JFROG_TOKEN: ${{ secrets.JFROG_TOKEN }}
   ```

### Quality Gates Failing

**Problem**: Evaluate stage fails with "schema validation failed"

**Solution**:
1. Check metrics JSON against schema (all 11 fields required)
2. Verify metrics conform to types (accuracy/f1_macro are numbers 0.0-1.0)
3. Review `configs/quality_gates.yaml` thresholds (not too strict)
4. Check `configs/baseline_metrics.json` baseline values

**Common causes:**
- Missing fields in metrics JSON (see [Metric Contract](#metric-contract))
- Field type mismatch (accuracy as string "0.85" instead of number 0.85)
- Typos in field names (e.g., "model_name_" instead of "model_name")

### Release Stage Skipped

**Problem**: Release/publish stages don't run even though models_version was provided

**Solution**:
1. Check evaluate stage passed (release depends on evaluate)
2. Verify `skip_release: false` in inputs
3. Check `model_version` is not empty string:
   ```yaml
   model_version: ${{ github.event.inputs.model_version }}
   skip_release: ${{ github.event.inputs.model_version == '' }}
   ```

### Publishing Fails with "Missing JFrog secrets"

**Problem**: Publish stage fails with "Missing required JFrog secrets"

**Solution**:
1. Set GitHub secrets (Settings → Secrets and variables → Actions):
   - `JFROG_URL`: e.g., `https://artifactory.yourcompany.com`
   - `JFROG_REPO`: e.g., `ml-models-release`
   - `JFROG_TOKEN`: Bearer token with push permissions
2. Pass secrets to workflow:
   ```yaml
   secrets:
     JFROG_URL: ${{ secrets.JFROG_URL }}
     JFROG_REPO: ${{ secrets.JFROG_REPO }}
     JFROG_TOKEN: ${{ secrets.JFROG_TOKEN }}
   ```

### Publishing Requires Approval But Doesn't Wait

**Problem**: Publish stage runs without approval prompt

**Solution**:
1. Go to repo Settings → Environments
2. Create or select `production` environment
3. Enable required reviewers or deployment branch restrictions
4. Verify workflow requests `environment: production`

---

## Next Steps

1. **Copy reusable workflows** into your `.github/workflows/` directory
2. **Create a calling workflow** (build.yml) that uses them
3. **Set GitHub secrets** for JFrog authentication (in GitHub UI)
4. **Create GitHub environment** named `production` with approval rules
5. **Test locally** with `workflow_dispatch` trigger
6. **Document customizations** in your team's MLOps runbook

---

## References

- [GitHub Reusable Workflows Documentation](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Platform Standard](../docs/PLATFORM_STANDARD.md)
- [Metric Schema](../schemas/metrics_schema.json)
- [Quality Gates Configuration](../../basic/configs/quality_gates.yaml)
