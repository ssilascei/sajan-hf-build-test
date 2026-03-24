import argparse
import json
import sys

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate model metrics against quality gates.")
    parser.add_argument("--metrics", default="artifacts/metrics/eval_metrics.json", help="Metrics JSON path.")
    parser.add_argument("--gates", default="configs/quality_gates.yaml", help="Quality gates YAML path.")
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


def main() -> None:
    args = parse_args()
    metrics = load_json(args.metrics)
    gates = load_yaml(args.gates)
    baseline = load_json(gates["baseline_metrics_path"])

    accuracy = float(metrics.get("accuracy", 0.0))
    f1_macro = float(metrics.get("f1_macro", 0.0))

    min_accuracy = float(gates["min_accuracy"])
    min_f1_macro = float(gates["min_f1_macro"])

    if accuracy < min_accuracy:
        fail(f"accuracy {accuracy:.4f} is below min_accuracy {min_accuracy:.4f}")

    if f1_macro < min_f1_macro:
        fail(f"f1_macro {f1_macro:.4f} is below min_f1_macro {min_f1_macro:.4f}")

    baseline_accuracy = float(baseline.get("accuracy", 0.0))
    baseline_f1_macro = float(baseline.get("f1_macro", 0.0))

    if accuracy < baseline_accuracy:
        fail(f"accuracy {accuracy:.4f} is below baseline accuracy {baseline_accuracy:.4f}")

    if f1_macro < baseline_f1_macro:
        fail(f"f1_macro {f1_macro:.4f} is below baseline f1_macro {baseline_f1_macro:.4f}")

    print("ALL QUALITY GATES PASSED")


if __name__ == "__main__":
    main()
