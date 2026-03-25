# Hugging Face MLOps: Complete Guide

This repository demonstrates a complete, scalable approach to building, evaluating, and releasing Hugging Face models.

It is organized into two learning paths:

## 📍 Folder Organization

### [`basic/`](basic/) — Learn By Example
**Your current working setup. A complete end-to-end example.**

What you'll find:
- Working GitHub Actions workflow (`build.yml`)
- Training script that trains on AG News dataset
- Evaluation and quality gate checking
- Release packaging and Artifactory publishing

Best for:
- Understanding how the pipeline works (no abstractions)
- Running locally or via GitHub Actions
- Using as a template for a new project
- Learning by doing

**Use this to:**
1. Commit it to GitHub
2. Run the build workflow manually
3. Watch train → evaluate → release in action
4. Understand each step's purpose

---

### [`advanced/`](advanced/) — Build an Enterprise Platform
**The core standard for scaling across multiple teams.**

What you'll find:
- `docs/PLATFORM_STANDARD.md` — defines mandatory repo structure, workflow stages, quality gates, metric schema, artifact schema, release policy
- `schemas/metrics_schema.json` — JSON schema enforcing metric field names and types
- `schemas/artifact_metadata_schema.json` — JSON schema enforcing release artifact contents
- `templates/quality_gates.yaml` — template config for gate thresholds

Best for:
- Understanding what an enterprise-grade standard looks like
- Building platform tools (CI/CD enforcement, validation, dashboards)
- Scaling to multiple teams with consistent quality gates
- Learning MLOps theory and best practices

**Use this to:**
1. Read [advanced/docs/PLATFORM_STANDARD.md](advanced/docs/PLATFORM_STANDARD.md) to understand the design
2. Review the JSON schemas to see formal contracts
3. Use as the basis for your team's standards
4. Build tooling around the schemas

---

## 🚀 Quick Start

### Step 1: Learn the Basics
```bash
cd basic/
cat README.md  # Understand the structure
```

### Step 2: Understand the Standard
```bash
cd ../advanced/
cat docs/PLATFORM_STANDARD.md  # Read the platform contract
cat schemas/metrics_schema.json  # See formal validation rules
```

### Step 3: Run It
```bash
cd ../basic/

# Install dependencies
pip install -r requirements.txt

# Train locally
python scripts/train.py --config configs/train.yaml

# Check gates
python scripts/evaluate.py --config configs/train.yaml --model-dir artifacts/model --output artifacts/metrics/eval_metrics.json
python scripts/check_gates.py --metrics artifacts/metrics/eval_metrics.json --gates configs/quality_gates.yaml
```

Or run via GitHub Actions (recommended):
1. Push to GitHub
2. Go to GitHub Actions → build workflow
3. Click "Run workflow" → enter version → watch it run

---

## 📚 Learning Path

### For MLOps/Platform Teams
1. Read [basic/README.md](basic/README.md) — understand the working example
2. Read [advanced/docs/PLATFORM_STANDARD.md](advanced/docs/PLATFORM_STANDARD.md) — understand the standard
3. Review [advanced/schemas/](advanced/schemas/) — understand the contracts
4. Implement schema validation in basic/scripts/check_gates.py
5. Build reusable GitHub workflows

### For ML Teams
1. Read [basic/README.md](basic/README.md) to understand your workflow
2. Copy [basic/](basic/) as your project template
3. Update config files and scripts for your task
4. Run locally, then on GitHub Actions

### For Governance/Compliance
1. Read [advanced/docs/PLATFORM_STANDARD.md](advanced/docs/PLATFORM_STANDARD.md) section 7 (Team Responsibilities)
2. Check [advanced/schemas/artifact_metadata_schema.json](advanced/schemas/artifact_metadata_schema.json) for release audit trail
3. Set up approval workflows in GitHub environments
4. Track gate pass rates and model lineage

---

## 🎯 Key Concepts

### The Workflow (from `basic/`)
```
Train (outputs model artifact)
  ↓
Evaluate (computes metrics, checks gates)
  ↓
Package (creates release tarball)
  ↓ 
Publish (uploads to Artifactory, requires approval)
```

Each stage produces versioned outputs. If one fails, fix it and re-run just that stage.

### The Standard (from `advanced/`)
1. **Repo structure** — every team repo has the same layout
2. **Workflow stages** — every build follows the same stages
3. **Metric contract** — metrics must have required fields (accuracy, f1_macro, git_sha, timestamp, etc.)
4. **Artifact metadata** — releases must include lineage and compliance info
5. **Quality gates** — thresholds + baseline regression prevention
6. **Release policy** — immutable versioning, human approval, forward-only rollback

### Why Both?

- **Basic** shows you how it works in practice
- **Advanced** shows you how to scale it across teams
- Together, they form a complete MLOps platform

---

## 📋 Repository Structure

```
.
├── basic/                              # Working example
│   ├── .github/workflows/
│   │   └── build.yml                   # Full pipeline: train → evaluate → release → publish
│   ├── scripts/
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   ├── check_gates.py
│   │   └── package_model.py
│   ├── configs/
│   │   ├── train.yaml
│   │   ├── quality_gates.yaml
│   │   └── baseline_metrics.json
│   ├── requirements.txt
│   └── README.md
│
├── advanced/                           # Enterprise platform standard
│   ├── docs/
│   │   └── PLATFORM_STANDARD.md        # Full specification
│   ├── schemas/
│   │   ├── metrics_schema.json         # Metric field validation
│   │   └── artifact_metadata_schema.json # Release artifact validation
│   ├── templates/
│   │   └── quality_gates.yaml          # Gate template
│   └── README.md
│
└── README.md                           # This file
```

---

## 🔧 Customization

### Want to use a different model?
Edit [basic/configs/train.yaml](basic/configs/train.yaml):
```yaml
model_name: bert-base-uncased  # Change from prajjwal1/bert-tiny
```

### Want to customize metrics?
Update [advanced/schemas/metrics_schema.json](advanced/schemas/metrics_schema.json):
```json
"properties": {
  "custom_metric": { "type": "number", ... }
}
```

### Want different gate thresholds?
Edit [basic/configs/quality_gates.yaml](basic/configs/quality_gates.yaml):
```yaml
min_accuracy: 0.85    # Stricter!
min_f1_macro: 0.85
```

---

## 🤝 Contributing

To extend this platform:

1. **Add a task-specific template** (e.g., token classification, QA)
   - Copy `basic/` as a starting point
   - Update scripts and config for your task
   - Place in a new folder like `task-templates/token-classification/`

2. **Add observability** (dashboards, model registry)
   - Use the standard as the data contract
   - Build tools on top of the schemas

3. **Implement schema validation**
   - Update `basic/scripts/check_gates.py` to validate against [`advanced/schemas/metrics_schema.json`](advanced/schemas/metrics_schema.json)
   - Make validation failures clear and actionable

---

## 📖 Reference

- [basic/README.md](basic/README.md) — how to use the working example
- [advanced/docs/PLATFORM_STANDARD.md](advanced/docs/PLATFORM_STANDARD.md) — what the standard requires
- [advanced/schemas/metrics_schema.json](advanced/schemas/metrics_schema.json) — metric field validation
- [advanced/schemas/artifact_metadata_schema.json](advanced/schemas/artifact_metadata_schema.json) — release metadata validation

---

## ❓ FAQ

**Q: Should I use `basic/` or `advanced/` for my project?**

A: Start with `basic/`. Copy it as your project. As you onboard more teams, adopt the `advanced/` standard as your governance layer.

**Q: What if I don't want quality gates?**

A: You can, but you'll lose regression detection and approval enforcement. Not recommended for production.

**Q: Can I customize the metric schema?**

A: Yes, but breaking changes require all teams to migrate. Use semantic versioning for schema changes.

**Q: How do I handle rollback?**

A: Never delete a release. Deploy the previous version as a new release (forward-only rollback).

---

## 🎓 Next Steps

1. **Study**: Read [advanced/docs/PLATFORM_STANDARD.md](advanced/docs/PLATFORM_STANDARD.md)
2. **Experiment**: Run [basic/](basic/) locally and on GitHub Actions
3. **Implement**: Add schema validation to check_gates.py
4. **Extend**: Create task-specific templates
5. **Scale**: Use the standard across your team

---

Enjoy! 🚀
