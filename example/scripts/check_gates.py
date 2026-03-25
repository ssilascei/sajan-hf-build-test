import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, ValidationError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate model metrics against quality gates.")
    parser.add_argument("--metrics", default="artifacts/metrics/eval_metrics.json", help="Metrics JSON path.")
    parser.add_argument("--gates", default="configs/quality_gates.yaml", help="Quality gates YAML path.")
    parser.add_argument("--schema", help="Path to metrics schema (defaults to ../advanced/schemas/metrics_schema.json).")
    return parser.parse_args()


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fail(message: str) -> None:
    print(f"GATE FAILED: {message}")
    sys.exit(1)


def validate_metrics_schema(metrics: dict, schema: dict) -> None:
    """
    Validate metrics against the schema contract.
    Raises ValidationError if validation fails.
    """
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(metrics))
    
    if errors:
        print("SCHEMA VALIDATION FAILED:")
        for error in errors:
            path = " > ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
            print(f"  [{path}] {error.message}")
        
        # Print required fields summary
        if "required" in schema:
            missing = set(schema["required"]) - set(metrics.keys())
            if missing:
                print(f"\nMissing required fields: {', '.join(sorted(missing))}")
        
        fail("Metrics do not conform to schema.")


def main() -> None:
    args = parse_args()
    metrics = load_json(args.metrics)
    gates = load_yaml(args.gates)
    baseline = load_json(gates["baseline_metrics_path"])

    # Determine schema path: use --schema arg or default to ../advanced/schemas/metrics_schema.json
    if args.schema:
        schema_path = args.schema
    else:
        # Try to find schema relative to this script
        script_dir = Path(__file__).parent
        default_schema = script_dir.parent.parent / "advanced" / "schemas" / "metrics_schema.json"
        if default_schema.exists():
            schema_path = str(default_schema)
        else:
            print("WARNING: Schema file not found at default location. Skipping schema validation.")
            schema_path = None
    
    # Validate schema first (fail fast)
    if schema_path:
        schema = load_json(schema_path)
        validate_metrics_schema(metrics, schema)
        print("✓ Metrics schema validation passed")
    
    # Threshold checks
    accuracy = float(metrics.get("accuracy", 0.0))
    f1_macro = float(metrics.get("f1_macro", 0.0))

    min_accuracy = float(gates["min_accuracy"])
    min_f1_macro = float(gates["min_f1_macro"])

    if accuracy < min_accuracy:
        fail(f"accuracy {accuracy:.4f} is below min_accuracy {min_accuracy:.4f}")

    if f1_macro < min_f1_macro:
        fail(f"f1_macro {f1_macro:.4f} is below min_f1_macro {min_f1_macro:.4f}")

    print(f"✓ Accuracy threshold: {accuracy:.4f} >= {min_accuracy:.4f}")
    print(f"✓ F1 macro threshold: {f1_macro:.4f} >= {min_f1_macro:.4f}")

    # Baseline regression checks
    baseline_accuracy = float(baseline.get("accuracy", 0.0))
    baseline_f1_macro = float(baseline.get("f1_macro", 0.0))

    if accuracy < baseline_accuracy:
        fail(f"accuracy {accuracy:.4f} is below baseline accuracy {baseline_accuracy:.4f}")

    if f1_macro < baseline_f1_macro:
        fail(f"f1_macro {f1_macro:.4f} is below baseline f1_macro {baseline_f1_macro:.4f}")

    print(f"✓ Accuracy vs baseline: {accuracy:.4f} >= {baseline_accuracy:.4f}")
    print(f"✓ F1 macro vs baseline: {f1_macro:.4f} >= {baseline_f1_macro:.4f}")

    print("\n" + "="*60)
    print("ALL QUALITY GATES PASSED")
    print("="*60)
    print(f"Model: {metrics.get('model_name', 'N/A')}")
    print(f"Dataset: {metrics.get('dataset_name', 'N/A')}")
    print(f"Run ID: {metrics.get('run_id', 'N/A')}")
    print(f"Git SHA: {metrics.get('git_sha', 'N/A')}")
    print("="*60)


if __name__ == "__main__":
    main()
