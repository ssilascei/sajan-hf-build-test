# Hugging Face MLOps: Core Platform Standard

This document defines the mandatory baseline for all Hugging Face model build pipelines across enterprise teams.

## 1. Repository Structure Contract

Every team repository MUST follow this structure:

```
.
├── .github/
│   ├── workflows/
│   │   └── build.yml          # Main workflow (train → evaluate → release)
│   └── instructions/
│       └── hf-mlops-build.instructions.md
├── configs/
│   ├── train.yaml             # Training config
│   ├── quality_gates.yaml     # Gate thresholds
│   └── baseline_metrics.json  # Baseline for regression check
├── scripts/
│   ├── train.py               # Training entrypoint
│   ├── evaluate.py            # Evaluation entrypoint
│   ├── check_gates.py         # Gate checking with schema validation
│   └── package_model.py       # Release packaging
├── tests/
│   └── test_quality_gates_config.py  # Config validation tests
├── model_cards/
│   └── README.md              # Model documentation
├── data/                       # Small test datasets only
├── src/                        # Optional: domain-specific code
├── artifacts/                  # Generated: models, metrics, packages
├── requirements.txt           # Pinned dependencies
└── README.md                  # Project summary
```

### Why This Structure

- **Consistency**: Teams can read each other's repos at a glance.
- **Automation**: Platform tools know where to find config, metrics, and artifacts.
- **Governance**: Standardized workflows integrate with approval and promotion systems.
- **Scalability**: Onboarding new teams is fast because layout is predictable.

---

## 2. Workflow Stages Contract

All builds MUST pass through these sequential stages:

| Stage | Purpose | Configuration | Pass/Fail Criteria |
|-------|---------|---|---|
| **CI** | Syntax, lint, unit tests | N/A | No lint errors, all tests pass |
| **Train** | Fine-tune base model | `configs/train.yaml` | Training completes without error |
| **Evaluate** | Metric computation + gating | `configs/quality_gates.yaml` | Threshold + baseline gates pass |
| **Package** | Release artifact assembly | `scripts/package_model.py` | Artifact created with valid metadata |
| **Publish** | Push to Artifactory | GitHub `environment: production` | Checksum verified, upload successful |

Each stage MUST produce versioned outputs. No stage may depend on external state; all inputs must be versioned or reconstructible.

---

## 3. Quality Gates Contract

### Gate Thresholds

Teams MUST define gates in `configs/quality_gates.yaml`:

```yaml
metric_contract_version: "1.0.0"

# Absolute thresholds (all metrics must PASS)
min_accuracy: 0.70
min_f1_macro: 0.70

# Baseline regression gates (candidate must not regress vs. baseline)
baseline_metrics_path: configs/baseline_metrics.json
allow_baseline_regression: false  # If true, warn but do not fail

# Gate policy
gate_enforcement_level: strict    # Options: strict | warn | disabled
gate_failure_action: exit         # Options: exit | log
```

### Baseline Metrics

Baselines MUST be stored in `configs/baseline_metrics.json`:

```json
{
  "accuracy": 0.70,
  "f1_macro": 0.70,
  "model_name": "distilbert-base-uncased",
  "dataset_name": "ag_news",
  "timestamp_utc": "2026-03-25T10:00:00Z",
  "git_sha": "abc123def456"
}
```

**Gate Logic**:
1. Candidate metric ≥ min threshold? → PASS
2. Candidate metric ≥ baseline metric? → PASS
3. Else → FAIL

---

## 4. Metric Contract Schema

All evaluation outputs MUST conform to this schema (see `schemas/metrics_schema.json`).

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `accuracy` | float | ✅ | Classification accuracy on eval split |
| `f1_macro` | float | ✅ | Macro-averaged F1 score |
| `eval_loss` | float | ✅ | Average evaluation loss |
| `model_name` | string | ✅ | Base model identifier (e.g., distilbert-base-uncased) |
| `dataset_name` | string | ✅ | Dataset identifier (e.g., ag_news, custom_internal) |
| `split` | string | ✅ | Eval split name (e.g., test, validation) |
| `run_id` | string | ✅ | Unique run identifier (${{ github.run_id }}) |
| `git_sha` | string | ✅ | Commit SHA for reproducibility |
| `timestamp_utc` | string (ISO 8601) | ✅ | When evaluation completed |
| `config_hash` | string | ✅ | SHA256 of training config for regression detection |
| `metric_contract_version` | string | ✅ | Schema version (e.g., "1.0.0") |

### Example Valid Metrics

```json
{
  "accuracy": 0.85,
  "f1_macro": 0.83,
  "eval_loss": 0.32,
  "model_name": "distilbert-base-uncased",
  "dataset_name": "ag_news",
  "split": "test",
  "run_id": "12345",
  "git_sha": "abc123def456",
  "timestamp_utc": "2026-03-25T10:15:30Z",
  "config_hash": "sha256:xyz789",
  "metric_contract_version": "1.0.0"
}
```

---

## 5. Artifact Metadata Schema

All released artifacts MUST contain `metadata.json` (see `schemas/artifact_metadata_schema.json`).

### Required Release Artifact Contents

Every release tarball MUST include:

```
hf-<model-name>-<version>.tar.gz
├── model/                              # Hugging Face model directory
│   ├── config.json
│   ├── pytorch_model.bin (or safetensors)
│   ├── tokenizer.json
│   └── ...
├── metrics/
│   └── eval_metrics.json              # Evaluation metrics (conforming to metric contract)
├── configs/
│   └── train.yaml                     # Training config used
└── metadata/
    └── metadata.json                  # Release metadata
```

### Metadata Schema

```json
{
  "version": "v1.2.0",
  "artifact_name": "hf-bert-tiny",
  "created_at_utc": "2026-03-25T10:30:00Z",
  "created_by": "github-actions",
  
  "model": {
    "base_model": "prajjwal1/bert-tiny",
    "training_dataset": "ag_news",
    "training_split_size": 2000,
    "model_task": "text-classification"
  },
  
  "training": {
    "epochs": 3,
    "learning_rate": 2.0e-5,
    "batch_size": 16,
    "seed": 42,
    "git_sha": "abc123def456"
  },
  
  "evaluation": {
    "accuracy": 0.85,
    "f1_macro": 0.83,
    "eval_loss": 0.32,
    "baseline_accuracy": 0.70,
    "baseline_f1_macro": 0.70,
    "gates_passed": true
  },
  
  "lineage": {
    "github_run_id": "12345",
    "github_run_url": "https://github.com/.../actions/runs/12345",
    "config_sha256": "sha256:xyz789",
    "artifact_sha256": "sha256:abc123def456"
  },
  
  "compliance": {
    "approver": "platform-team",
    "approval_timestamp": "2026-03-25T10:45:00Z",
    "retention_policy": "immutable-7-years",
    "pii_scan_passed": true
  }
}
```

---

## 6. Release Policy

### Immutability

- Once released with a version tag, an artifact is **immutable**.
- No retag, no deletion, no modification to contents.
- If rollback is needed, deploy the previous immutable version.

### Versioning

Teams MUST use one of:

1. **Semantic Versioning**: `v1.2.3` (major.minor.patch)
2. **Build Versioning**: `20260325.001` (date.sequence)
3. **Composite**: `v1.2.3+abc123` (semantic + short SHA)

### Promotion Workflow

```
Train (pass) 
  ↓
Evaluate (pass gates) 
  ↓
Package (create release artifact) 
  ↓
Human Approval (required for production)
  ↓
Publish to Artifactory (immutable release)
  ↓
Deploy (via separate deployment pipeline)
```

### Rollback

Rollback is a **forward-moving operation**:
- Do NOT delete or modify existing release
- Deploy the previous immutable version
- Create a new release for the rollback (e.g., `v1.2.0-rollback-from-v1.2.1`)

---

## 7. Team Responsibilities

### What Each Team MUST Do

1. **Provide**:
   - `configs/train.yaml` with consistent field names
   - `configs/quality_gates.yaml` with thresholds and baseline reference
   - `scripts/train.py` that outputs metrics conforming to the schema
   - `scripts/evaluate.py` that validates and outputs schema-conforming metrics
   - `scripts/check_gates.py` that enforces gates with schema validation

2. **Comply**:
   - All metrics emitted MUST pass schema validation
   - All releases MUST contain required metadata
   - All gates MUST be defined in YAML (not hardcoded in scripts)
   - All commits to main/release branches MUST pass CI

### What the Platform MUST Provide

1. Reusable workflow templates for train/evaluate/publish
2. Shared package for schema validation and metric normalization
3. Centralized Artifactory publishing with immutability guarantees
4. Approval and promotion automation via GitHub environments
5. Observability: release history, gate pass rates, rollback events

---

## 8. Evolution and Versioning

This standard is versioned. Current version: **1.0.0**

### Making Changes

- Changes to repo structure: Requires all teams to migrate (major version bump)
- Adding required metrics: Teams update their scripts (minor version bump)
- Clarifications: No version bump, update docs

### Backward Compatibility

- **Not** backward compatible across major version boundaries
- Teams have 2 release cycles to migrate to a new major version
- Platform maintains runners for N-1 and N versions during transition

---

## 9. Next Steps

1. **Verify Compliance**: Platform validates repo structure, workflow stages, and metrics schema
2. **Create Task-Specific Templates**: Build overlays for classification, token tagging, QA, etc.
3. **Publish Reusable Workflows**: Centralize train/evaluate/publish logic
4. **Build Observability**: Track gate pass rates, model performance over time, deployment frequency
5. **Governance Dashboard**: Visualize team adoption, compliance, and drift

---

## Reference

- Metric Schema: `schemas/metrics_schema.json`
- Artifact Schema: `schemas/artifact_metadata_schema.json`
- Quality Gates Template: `templates/quality_gates.yaml`
- Example Repo: (this repo)
