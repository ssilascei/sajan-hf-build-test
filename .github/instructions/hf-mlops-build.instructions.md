---
description: "Use when teaching, designing, or implementing Hugging Face model build pipelines, CI/CD workflows, quality gates, and artifact publishing to JFrog Artifactory."
name: "Hugging Face Build and Release Guidance"
applyTo: "**"
---
# Hugging Face Build and Release Guidance

## Goal
Provide step-by-step guidance for building ML models with Hugging Face using GitHub workflows as the default automation path, while clearly explaining why each step exists.

## Mandatory Behavior
- Explain each major step with two parts: `What to do` and `Why it matters`.
- Prefer GitHub Actions workflows over local manual commands whenever automation is possible.
- Define and enforce quality gates before training promotion or artifact publication.
- Treat model artifacts as release assets and publish approved outputs to JFrog Artifactory.
- Keep guidance reproducible: pin dependencies, set random seeds, and capture run metadata.

## Standard Build Flow
For each phase, explain both execution and rationale.

1. Project setup and environment lock
- Include pinned dependencies and deterministic config.
- Why: prevents environment drift and supports repeatable training.

2. Data validation and schema checks
- Run data checks in CI before training.
- Why: catches bad inputs early to avoid wasted compute and silent model quality issues.

3. Training execution
- Run training through workflow jobs (or reusable workflow) using tracked configs.
- Why: creates auditable, repeatable runs and enables team-wide consistency.

4. Evaluation and threshold gating
- Compare metrics against minimum thresholds in config (for example F1, accuracy, perplexity, latency).
- Compare metrics against the current production baseline model.
- Why: blocks regressions and ensures only acceptable models move forward.

5. Test and quality gateways
- Enforce lint, unit tests, integration tests, and model-level checks in CI.
- Why: verifies both code quality and model behavior before release.

6. Package and sign artifacts
- Bundle model files, config, tokenizer assets, metadata, and checksums.
- Why: creates traceable artifacts suitable for deployment and compliance.

7. Publish to JFrog Artifactory
- Push only from gated branches/tags after successful workflow checks.
- Why: keeps artifact registry trustworthy and avoids publishing unverified models.

## Required Quality Gates
Always propose clear pass/fail gates with measurable criteria.

- Code gate: lint and static analysis must pass.
- Test gate: unit/integration tests must pass.
- Data gate: schema and data quality checks must pass.
- Model gate: metrics must meet configured thresholds.
- Model gate: metrics must also outperform or match the approved production baseline.
- Security gate: dependency and secret scans must pass.
- Release gate: publish is allowed only through manual approval in a protected GitHub environment.

## GitHub Workflow Guidance
When providing implementation details, default to:
- Separate workflows for `ci`, `train`, `evaluate`, and `release`, or use reusable workflows.
- `workflow_dispatch` for controlled training/release runs.
- `pull_request` and `push` triggers for CI quality gates.
- Job dependencies using `needs` so publish jobs cannot run before quality gates pass.
- Environment protection rules for production release jobs.

## JFrog Artifactory Publishing Guidance
When describing publish steps:
- Use least-privilege credentials and GitHub secrets.
- Prefer OIDC-based auth when available; otherwise use short-lived tokens.
- Version artifacts with immutable identifiers (commit SHA, run number, semantic tag).
- Upload metadata files (metrics summary, git SHA, training config, timestamp) with the model artifact.

## Output Format Expectations
When asked for a plan or implementation, provide:
- A pipeline overview.
- Workflow-by-workflow breakdown.
- Quality gate table with thresholds.
- Artifact naming and Artifactory path strategy.
- Rollback or rollback-prevention guidance.
