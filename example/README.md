# Basic: Simple Hugging Face Model Training & Release

This is your current working setup—a complete, end-to-end example for training, evaluating, packaging, and publishing a Hugging Face classification model.

## Folder Structure

```
basic/
├── .github/workflows/
│   └── build.yml                    # Main workflow: train → evaluate → release
├── scripts/
│   ├── train.py                     # Train a classifier
│   ├── evaluate.py                  # Evaluate trained model
│   ├── check_gates.py              # Validate metrics against thresholds
│   └── package_model.py            # Create release artifact
├── configs/
│   ├── train.yaml                  # Training configuration
│   ├── quality_gates.yaml          # Quality gate thresholds + baseline
│   └── baseline_metrics.json       # Baseline metrics for regression check
├── tests/
│   └── (tests go here)
├── requirements.txt                # Pinned dependencies
└── README.md                       # This file
```

## Usage

### Option 1: Run locally (for testing)
```bash
# Install dependencies
pip install -r requirements.txt

# Train
python scripts/train.py --config configs/train.yaml

# Evaluate
python scripts/evaluate.py --config configs/train.yaml --model-dir artifacts/model --output artifacts/metrics/eval_metrics.json

# Check gates
python scripts/check_gates.py --metrics artifacts/metrics/eval_metrics.json --gates configs/quality_gates.yaml

# Package
python scripts/package_model.py --version v1.0.0
```

### Option 2: Run via GitHub Actions (recommended)
```bash
# Push to GitHub
git push

# In GitHub Actions, click "Run workflow" on build.yml
# Provide model_version input (e.g., v1.0.0)
# Watch the build run through: train → evaluate → release → publish
```

## Workflow Flow

```
input: model_version (e.g., v1.0.0)
  ↓
[train job]
  - Load dataset (ag_news)
  - Train on 2000 samples, eval on 500 samples
  - Upload trained-model artifact
  ↓
[evaluate job]
  - Download trained-model
  - Evaluate on test set
  - Check quality gates (min_accuracy > 0.70, min_f1_macro > 0.70)
  - Check baseline regression (no regression vs. baseline)
  - Upload eval-metrics artifact
  ↓
[release job]
  - Download trained-model + eval-metrics
  - Run second gate check
  - Package into tarball with metadata
  - Upload release-package artifact
  ↓
[publish job]
  - Download release-package
  - Push to JFrog Artifactory (requires GitHub environment approval)
```

## Configuration

### Train Config (`configs/train.yaml`)
- **model**: `prajjwal1/bert-tiny` (4.4M param model, good for demo)
- **dataset**: `ag_news` (4-class topic classification, 120k samples)
- **training**: 3 epochs, 2000 train samples, 500 eval samples
- **batch size**: 16

### Quality Gates (`configs/quality_gates.yaml`)
- **min_accuracy**: 0.70 (must be ≥ 70%)
- **min_f1_macro**: 0.70 (must be ≥ 70%)
- **baseline comparison**: candidate must not regress below baseline

### Baseline (`configs/baseline_metrics.json`)
- Sets the floor for model performance
- Update after a successful release

## Requirements

- Python 3.11+
- GPU/TPU recommended (CPU training is slow but works)
- `transformers`, `torch`, `datasets`, `scikit-learn`, `PyYAML`, `pytest`

## Key Files

- [scripts/train.py](scripts/train.py) — trains on `ag_news` dataset using a small BERT model
- [scripts/evaluate.py](scripts/evaluate.py) — evaluates on held-out test set, computes accuracy + F1
- [scripts/check_gates.py](scripts/check_gates.py) — validates metrics against `configs/quality_gates.yaml`
- [scripts/package_model.py](scripts/package_model.py) — creates versioned release tarball with metadata
- [.github/workflows/build.yml](.github/workflows/build.yml) — orchestrates the full pipeline

## Next Steps

1. **Commit & push** the basic/ folder to GitHub
2. **Set up JFrog secrets** in GitHub Settings → Secrets:
   - `JFROG_URL`
   - `JFROG_REPO`
   - `JFROG_TOKEN`
3. **Run the workflow**:
   - Go to GitHub Actions → build workflow
   - Click "Run workflow"
   - Enter model_version (e.g., `v1.0.0`)
   - Watch it train, evaluate, and release
4. **Check Artifactory** to verify artifact was published

## Understanding the Pipeline

**Why separate jobs instead of one sequential script?**
- If release fails, you re-run only the release job (not retrain)
- If evaluation fails, you fix gates and re-run evaluate
- Artifacts are versioned within the run, not re-downloaded each step

**Why quality gates?**
- Ensures only approved models are released
- Baseline check prevents silent regressions

**Why metadata in the artifact?**
- Audit trail: who, when, what config, what metrics
- Reproducibility: can retrain with the same config
- Compliance: lineage from git commit to release

## Learn More

See `../advanced/docs/PLATFORM_STANDARD.md` for the enterprise version of these ideas.
