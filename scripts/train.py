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
    set_seed,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a fast baseline Hugging Face classifier.")
    parser.add_argument("--config", default="configs/train.yaml", help="Path to training config file.")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)

    set_seed(int(cfg["seed"]))

    dataset = load_dataset(cfg["dataset_name"])
    train_ds = dataset["train"].shuffle(seed=cfg["seed"]).select(range(cfg["train_size"]))
    eval_ds = dataset["test"].shuffle(seed=cfg["seed"]).select(range(cfg["eval_size"]))

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"])

    def preprocess(batch: dict) -> dict:
        return tokenizer(
            batch[cfg["text_column"]],
            truncation=True,
            max_length=int(cfg["max_length"]),
        )

    train_ds = train_ds.map(preprocess, batched=True)
    eval_ds = eval_ds.map(preprocess, batched=True)

    train_ds = train_ds.remove_columns([cfg["text_column"]])
    eval_ds = eval_ds.remove_columns([cfg["text_column"]])

    num_labels = len(dataset["train"].features[cfg["label_column"]].names)
    model = AutoModelForSequenceClassification.from_pretrained(cfg["model_name"], num_labels=num_labels)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=1)
        return {
            "accuracy": float(accuracy_score(labels, predictions)),
            "f1_macro": float(f1_score(labels, predictions, average="macro")),
        }

    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=float(cfg["num_train_epochs"]),
        learning_rate=float(cfg["learning_rate"]),
        per_device_train_batch_size=int(cfg["per_device_train_batch_size"]),
        per_device_eval_batch_size=int(cfg["per_device_eval_batch_size"]),
        weight_decay=float(cfg["weight_decay"]),
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=10,
        seed=int(cfg["seed"]),
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    eval_metrics = trainer.evaluate()

    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    metrics_path = Path(cfg["metrics_output_path"])
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_metrics = {
        "accuracy": float(eval_metrics.get("eval_accuracy", 0.0)),
        "f1_macro": float(eval_metrics.get("eval_f1_macro", 0.0)),
        "eval_loss": float(eval_metrics.get("eval_loss", 0.0)),
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(normalized_metrics, f, indent=2)

    print(f"Saved trained model to {output_dir}")
    print(f"Saved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
