# Advanced: Enterprise-Grade Hugging Face MLOps Platform

This folder contains the core platform standard and templates for building a scalable, auditable AI model pipeline across enterprise teams.

## Folder Structure

```
advanced/
├── docs/
│   └── PLATFORM_STANDARD.md          # Core contract: repo structure, workflows, gates, metadata
├── schemas/
│   ├── metrics_schema.json           # JSON schema for evaluation metrics contract
│   ├── artifact_metadata_schema.json # JSON schema for release artifact metadata
├── templates/
│   ├── quality_gates.yaml            # Template quality gates config
│   └── README.md                     # This file
└── README.md
```

## What This Is

The **core platform standard** for all Hugging Face model training and release pipelines across AI teams.

It defines:
1. **Mandatory repo structure** — so teams can read each other's code
2. **Workflow stages** — so pipelines are predictable (train → evaluate → release)
3. **Quality gates** — so only approved models are released
4. **Metric contract** — so gates work across all teams
5. **Artifact metadata** — so releases are auditable and reproducible
6. **Release policy** — so deployments are safe and immutable

## Who Should Use This

- **Platform teams**: Building internal standards for AI organizations
- **ML ops teams**: Scaling model training across multiple teams
- **Governance/compliance**: Ensuring audit trails and reproducibility
- **AI teams onboarding**: Starting with a proven structure

## Quick Start

### Step 1: Read the Standard
Start with [docs/PLATFORM_STANDARD.md](docs/PLATFORM_STANDARD.md).

This is the source of truth. It answers:
- What must my repo look like?
- What are the required workflow stages?
- What metrics must my models emit?
- What metadata must releases contain?

### Step 2: Review the Schemas
- [schemas/metrics_schema.json](schemas/metrics_schema.json) — defines evaluation metric fields
- [schemas/artifact_metadata_schema.json](schemas/artifact_metadata_schema.json) — defines release artifact metadata

These are machine-readable contracts that enable:
- Automatic validation in CI/CD
- Integration with dashboards and approval systems
- Regression detection across versions

### Step 3: Use the Templates
- [templates/quality_gates.yaml](templates/quality_gates.yaml) — copy into your `configs/` and customize thresholds

## Implementation Roadmap

**Phase 1: Core Platform (Current)**
- ✅ Define repo structure
- ✅ Define workflow stages
- ✅ Define metric and artifact schemas
- ✅ Define quality gate policy
- ⏭️ **Next: Implement schema validation in gate checker**

**Phase 2: Reusable Workflows**
- Build shared GitHub Actions workflows
- Centralize train/evaluate/publish logic
- Enable teams to use `.github/workflows/build.yml` from the platform

**Phase 3: Task-Specific Templates**
- Create overlays for text classification, token tagging, QA, etc.
- Each overlay extending the core standard with task-specific metrics

**Phase 4: Observability & Promotion**
- Model registry with version history
- Gate pass rates and trend analysis
- Automated promotion rules (e.g., "release if gates pass + manual approval")
- Rollback history and audit logs

**Phase 5: Compliance & Governance**
- Immutable release storage with retention policies
- PII detection and masking
- Team access controls
- Audit trail dashboards

## Key Design Principles

1. **Standardization Without Restrictions**: Teams can customize metrics and gates, but the shape (schema) is standardized.

2. **Immutability**: Once released, artifacts never change. Rollback is always a forward operation (new release).

3. **Traceability**: Every release includes lineage: git commit, run ID, approver, timestamp.

4. **Fail Fast**: Quality gates use strict validation. Missing a required field fails the build.

5. **Auditability**: Release decisions are logged, not implicit.

## How to Adapt This for Your Organization

### Minimal Adoption
1. Copy the repo structure to all team repos
2. Use the metric schema in your gate checker
3. Add one approval step before release

### Medium Adoption
1. Do the above
2. Build shared train/evaluate GitHub workflows
3. Create a central model registry (e.g., Artifactory or Hugging Face Hub)
4. Add automated gates and promotion rules

### Full Adoption
1. Do the above
2. Implement task-specific templates
3. Build observability dashboard
4. Automate rollback detection and emergency releases

## Common Questions

**Q: What if my task has different metrics (e.g., BLEU for summarization)?**

A: Update `schemas/metrics_schema.json` to add your metric in `additional_metrics`. The core fields (accuracy, f1_macro, etc.) stay the same as the baseline.

**Q: Can teams use different base models?**

A: Yes. The standard is task-agnostic. Just update `configs/train.yaml` and release artifact will capture which model was used.

**Q: What if a team wants to skip gates?**

A: Set `gate_enforcement_level: disabled` in `configs/quality_gates.yaml`, but this triggers audit alerts. Not recommended for production.

**Q: How do we handle breaking changes to the schema?**

A: Use semantic versioning. `metric_contract_version` in every metrics.json. When you bump to 2.0.0, teams have 2 release cycles to migrate.

## Next Steps

1. **Implement schema validation**: Update [check_gates.py](../../scripts/check_gates.py) to validate metrics.json against schema
2. **Add provenance fields**: Update [evaluate.py](../../scripts/evaluate.py) to emit required lineage fields
3. **Create shared workflows**: Build reusable `.github/workflows/` for train/evaluate/publish
4. **Build a registry UI**: Create dashboard to browse released models, their metrics, and approval history

## References

- [PLATFORM_STANDARD.md](docs/PLATFORM_STANDARD.md) — Full specification
- [Hugging Face Model Hub](https://huggingface.co/models) — Reference for model versioning
- [MLOps.community](https://mlops.community) — Discussion on enterprise ML practices
- [Semantic Versioning](https://semver.org) — Version scheme recommendation
