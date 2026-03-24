import argparse
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package model and metadata into a release artifact.")
    parser.add_argument("--model-dir", default="artifacts/model", help="Path to model directory.")
    parser.add_argument("--metrics", default="artifacts/metrics/eval_metrics.json", help="Path to metrics file.")
    parser.add_argument("--config", default="configs/train.yaml", help="Path to train config file.")
    parser.add_argument("--version", required=True, help="Artifact version (tag or release id).")
    parser.add_argument("--output-dir", default="artifacts/package", help="Output directory for package.")
    return parser.parse_args()


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()

    model_dir = Path(args.model_dir)
    metrics_path = Path(args.metrics)
    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "version": args.version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_dir": str(model_dir),
        "metrics_path": str(metrics_path),
        "config_path": str(config_path),
    }

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    package_name = f"hf-bert-tiny-{args.version}.tar.gz"
    package_path = output_dir / package_name

    with tarfile.open(package_path, "w:gz") as tar:
        tar.add(model_dir, arcname="model")
        tar.add(metrics_path, arcname="metrics/eval_metrics.json")
        tar.add(config_path, arcname="configs/train.yaml")
        tar.add(metadata_path, arcname="metadata/metadata.json")

    checksum = sha256_of_file(package_path)
    checksum_path = output_dir / f"{package_name}.sha256"
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {package_name}\n")

    print(f"Created package: {package_path}")
    print(f"Created checksum: {checksum_path}")


if __name__ == "__main__":
    main()
