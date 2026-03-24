import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained Hugging Face classifier.")
    parser.add_argument("--config", default="configs/train.yaml", help="Path to training config file.")
    parser.add_argument("--model-dir", default="artifacts/model", help="Path to trained model directory.")
    parser.add_argument("--output", default="artifacts/metrics/eval_metrics.json", help="Path to output metrics json.")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)

    dataset = load_dataset(cfg["dataset_name"])
    eval_ds = dataset["test"].shuffle(seed=cfg["seed"]).select(range(cfg["eval_size"]))

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)

    def preprocess(batch: dict) -> dict:
        return tokenizer(
            batch[cfg["text_column"]],
            truncation=True,
            max_length=int(cfg["max_length"]),
        )

    eval_ds = eval_ds.map(preprocess, batched=True)
    eval_ds = eval_ds.remove_columns([cfg["text_column"]])

    model = AutoModelForSequenceClassification.from_pretrained(args.model_dir)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=1)
        return {
            "accuracy": float(accuracy_score(labels, predictions)),
            "f1_macro": float(f1_score(labels, predictions, average="macro")),
        }

    trainer = Trainer(
        model=model,
        args=TrainingArguments(output_dir="artifacts/eval_tmp", report_to=[]),
        eval_dataset=eval_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    eval_metrics = trainer.evaluate()
    normalized_metrics = {
        "accuracy": float(eval_metrics.get("eval_accuracy", 0.0)),
        "f1_macro": float(eval_metrics.get("eval_f1_macro", 0.0)),
        "eval_loss": float(eval_metrics.get("eval_loss", 0.0)),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized_metrics, f, indent=2)

    print(f"Saved evaluation metrics to {out_path}")


if __name__ == "__main__":
    main()
