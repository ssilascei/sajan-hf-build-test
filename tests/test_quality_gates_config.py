import json

import yaml


def test_quality_gate_config_is_valid():
    with open("configs/quality_gates.yaml", "r", encoding="utf-8") as f:
        gates = yaml.safe_load(f)

    assert 0.0 <= float(gates["min_accuracy"]) <= 1.0
    assert 0.0 <= float(gates["min_f1_macro"]) <= 1.0

    with open(gates["baseline_metrics_path"], "r", encoding="utf-8") as f:
        baseline = json.load(f)

    assert "accuracy" in baseline
    assert "f1_macro" in baseline
