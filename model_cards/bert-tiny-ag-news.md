# Model Card: bert-tiny AG News Starter

## Model Details
- Base model: `prajjwal1/bert-tiny`
- Task: News topic classification (4 classes)
- Fine-tune dataset: `ag_news` subset for quick iteration

## Training Setup
- Train samples: 500
- Eval samples: 200
- Epochs: 1
- Intended use: CI/CD pipeline validation and starter experimentation

## Quality Gates
- Must meet minimum accuracy and macro F1 thresholds
- Must match or exceed configured production baseline metrics

## Limitations
- Tiny subset and short training are not production quality.
- Use this setup only as a fast starting point.
