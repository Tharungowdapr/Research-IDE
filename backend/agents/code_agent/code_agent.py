"""
Code Generation Agent — 12-File Runnable Scaffold
Generates complete, runnable research code with HuggingFace, wandb, PyYAML.
"""

import json
import re
from typing import Dict, List, Any
from core.llm_client import LLMClient

CODE_SYSTEM = """You are a senior ML engineer. Generate complete, runnable Python code. \
Use HuggingFace datasets library for data loading. Use wandb for experiment tracking. \
Use PyYAML for config. Every file must be syntactically complete with all imports. \
No placeholder comments like 'add your code here'. \
In the Makefile, recipe lines MUST begin with a tab character, not spaces. \
Return ONLY valid JSON."""

CODE_PROMPT = """Generate a complete runnable code scaffold for this research project.

Idea: {title}
Approach: {approach}
Tech Stack: {tech_stack}
Datasets: {datasets}
Evaluation Metrics: {metrics}
{file_hints_section}
{github_hint}

Return JSON with this structure:
{{
  "files": [
    {{"filename": "main.py", "description": "Entry point with argparse and config loading", "code": "..."}},
    {{"filename": "config.py", "description": "Dataclass Config with all hyperparams", "code": "..."}},
    {{"filename": "experiment_config.yaml", "description": "All hyperparams as YAML", "code": "..."}},
    {{"filename": "model.py", "description": "Model class matching the approach", "code": "..."}},
    {{"filename": "dataset.py", "description": "HuggingFace datasets loader", "code": "..."}},
    {{"filename": "train.py", "description": "Full training loop with wandb", "code": "..."}},
    {{"filename": "evaluate.py", "description": "Load checkpoint, compute metrics", "code": "..."}},
    {{"filename": "utils.py", "description": "Helper functions", "code": "..."}},
    {{"filename": "requirements.txt", "description": "Pinned versions", "code": "..."}},
    {{"filename": "Makefile", "description": "Build targets (use tabs!)", "code": "..."}},
    {{"filename": "tests/test_model.py", "description": "Pytest stubs", "code": "..."}},
    {{"filename": "README.md", "description": "Project documentation", "code": "..."}}
  ],
  "setup_instructions": ["Step 1", "Step 2"],
  "run_command": "python main.py --config experiment_config.yaml"
}}

Generate ALL 12 files with complete, syntactically valid code."""


async def run_code_generation(
    idea: Dict,
    plan: Dict,
    llm: LLMClient,
    file_hints: List[str] = None,
    papers: List[Dict] = None,
) -> Dict:
    """Generate 12-file research code scaffold."""
    tech = plan.get("tech_stack", {})
    datasets = [d.get("name", "") for d in plan.get("datasets", [])]
    metrics = plan.get("evaluation_metrics", [])
    papers = papers or []

    # Build file hints section
    file_hints_section = ""
    if file_hints:
        file_hints_section = "Generate these specific files:\n" + "\n".join(f"- {h}" for h in file_hints)

    # Build github hint
    github_hint = ""
    if papers:
        repo_refs = [p.get("github_url", "") for p in papers[:3] if p.get("github_url")]
        if repo_refs:
            github_hint = (f"Reference implementations exist at: {repo_refs}. "
                          f"Include a comment in dataset.py: # Based on implementation from {repo_refs[0]}")

    prompt = CODE_PROMPT.format(
        title=idea.get("title", "Research Project"),
        approach=idea.get("approach", "ML approach"),
        tech_stack=f"Frameworks: {', '.join(tech.get('frameworks', ['PyTorch']))}",
        datasets=", ".join(datasets) or "custom dataset",
        metrics=", ".join(metrics) or "accuracy, F1",
        file_hints_section=file_hints_section,
        github_hint=github_hint,
    )

    try:
        raw = await llm.complete(prompt, system=CODE_SYSTEM, json_mode=True)
        result = _parse_json(raw)
        if "files" in result:
            result = _postprocess_makefile(result)
            return result
        return _fallback_code(idea, plan)
    except Exception as e:
        print(f"Code generation error: {e}")
        return _fallback_code(idea, plan)


def _postprocess_makefile(result: Dict) -> Dict:
    """Fix Makefile tab characters."""
    for f in result.get("files", []):
        if f.get("filename") == "Makefile":
            lines = f["code"].split("\n")
            fixed = []
            in_recipe = False
            for line in lines:
                stripped = line.lstrip()
                if stripped and ":" in stripped and not stripped.startswith("\t") and not stripped.startswith("#"):
                    in_recipe = True
                    fixed.append(line)
                elif in_recipe and stripped and not stripped.startswith("#") and ":" not in stripped:
                    if not line.startswith("\t"):
                        line = "\t" + stripped
                    fixed.append(line)
                else:
                    if not stripped:
                        in_recipe = False
                    fixed.append(line)
            f["code"] = "\n".join(fixed)
    return result


def _fallback_code(idea: Dict, plan: Dict) -> Dict:
    """Complete 12-file fallback scaffold."""
    title = idea.get("title", "Research Project")
    return {
        "files": [
            {"filename": "main.py", "description": "Entry point with argparse and config loading", "code": f'''"""
{title} — Main Entry Point
Auto-generated by ResearchIDE
"""

import argparse
import yaml
from config import Config
from train import train
from evaluate import evaluate


def main():
    parser = argparse.ArgumentParser(description="{title}")
    parser.add_argument("--config", type=str, default="experiment_config.yaml")
    parser.add_argument("--mode", type=str, default="train", choices=["train", "eval"])
    parser.add_argument("--checkpoint", type=str, default=None)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        cfg_dict = yaml.safe_load(f)
    config = Config(**cfg_dict)

    if args.mode == "train":
        train(config)
    elif args.mode == "eval":
        evaluate(config, checkpoint_path=args.checkpoint)


if __name__ == "__main__":
    main()
'''},
            {"filename": "config.py", "description": "Configuration dataclass", "code": '''"""Configuration"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Config:
    # Model
    model_name: str = "base_model"
    hidden_dim: int = 256
    num_layers: int = 4
    dropout: float = 0.1

    # Training
    learning_rate: float = 1e-4
    batch_size: int = 32
    epochs: int = 50
    weight_decay: float = 0.01
    warmup_steps: int = 500

    # Data
    dataset_name: str = "custom"
    max_length: int = 512
    num_workers: int = 4

    # Experiment
    seed: int = 42
    experiment_name: str = "experiment_1"
    output_dir: str = "./outputs"
    wandb_project: str = "research-ide"
    log_every: int = 100
    eval_every: int = 500
    save_every: int = 1000
'''},
            {"filename": "experiment_config.yaml", "description": "YAML configuration", "code": '''# Experiment Configuration
model_name: "base_model"
hidden_dim: 256
num_layers: 4
dropout: 0.1

# Training
learning_rate: 0.0001
batch_size: 32
epochs: 50
weight_decay: 0.01
warmup_steps: 500

# Data
dataset_name: "custom"
max_length: 512
num_workers: 4

# Experiment
seed: 42
experiment_name: "experiment_1"
output_dir: "./outputs"
wandb_project: "research-ide"
log_every: 100
eval_every: 500
save_every: 1000
'''},
            {"filename": "model.py", "description": "Model architecture", "code": '''"""Model Architecture"""

import torch
import torch.nn as nn


class BaseModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 256,
                 output_dim: int = 10, num_layers: int = 4, dropout: float = 0.1):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for i in range(num_layers):
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        self.encoder = nn.Sequential(*layers)
        self.classifier = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        features = self.encoder(x)
        return self.classifier(features)
'''},
            {"filename": "dataset.py", "description": "Dataset loading and preprocessing", "code": '''"""Dataset Loading"""

import torch
from torch.utils.data import Dataset, DataLoader


class ResearchDataset(Dataset):
    def __init__(self, split="train", max_length=512):
        self.split = split
        self.max_length = max_length
        # Placeholder data — replace with actual dataset
        self.data = torch.randn(1000, 128)
        self.labels = torch.randint(0, 10, (1000,))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]


def get_dataloaders(config):
    train_ds = ResearchDataset(split="train", max_length=config.max_length)
    val_ds = ResearchDataset(split="val", max_length=config.max_length)
    train_loader = DataLoader(train_ds, batch_size=config.batch_size,
                              shuffle=True, num_workers=config.num_workers)
    val_loader = DataLoader(val_ds, batch_size=config.batch_size,
                            shuffle=False, num_workers=config.num_workers)
    return train_loader, val_loader
'''},
            {"filename": "train.py", "description": "Training loop with wandb logging", "code": '''"""Training Loop"""

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm
from model import BaseModel
from dataset import get_dataloaders
from utils import set_seed, get_device, save_checkpoint

try:
    import wandb
except ImportError:
    wandb = None


def train(config):
    set_seed(config.seed)
    device = get_device()

    if wandb:
        wandb.init(project=config.wandb_project, name=config.experiment_name)

    train_loader, val_loader = get_dataloaders(config)
    model = BaseModel(input_dim=128, hidden_dim=config.hidden_dim,
                      num_layers=config.num_layers, dropout=config.dropout).to(device)
    optimizer = AdamW(model.parameters(), lr=config.learning_rate,
                      weight_decay=config.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=config.epochs)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0
    for epoch in range(config.epochs):
        model.train()
        total_loss = 0
        for batch_idx, (x, y) in enumerate(tqdm(train_loader, desc=f"Epoch {epoch+1}")):
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            pred = model(x)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

            if wandb and batch_idx % config.log_every == 0:
                wandb.log({"train/loss": loss.item(), "train/lr": scheduler.get_last_lr()[0]})

        scheduler.step()
        val_loss, val_acc = evaluate_epoch(model, val_loader, criterion, device)
        print(f"Epoch {epoch+1}: train_loss={total_loss/len(train_loader):.4f} val_acc={val_acc:.4f}")

        if wandb:
            wandb.log({"val/loss": val_loss, "val/accuracy": val_acc, "epoch": epoch+1})

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_checkpoint(model, optimizer, epoch, config)

    if wandb:
        wandb.finish()


def evaluate_epoch(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0, 0, 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            pred = model(x)
            total_loss += criterion(pred, y).item()
            correct += (pred.argmax(1) == y).sum().item()
            total += len(y)
    return total_loss / max(len(loader), 1), correct / max(total, 1)
'''},
            {"filename": "evaluate.py", "description": "Evaluation script", "code": '''"""Evaluation — loads checkpoint and computes metrics"""

import json
import torch
from pathlib import Path
from model import BaseModel
from dataset import get_dataloaders
from utils import get_device, set_seed
from sklearn.metrics import accuracy_score, f1_score, classification_report


def evaluate(config, checkpoint_path=None):
    set_seed(config.seed)
    device = get_device()

    _, val_loader = get_dataloaders(config)
    model = BaseModel(input_dim=128, hidden_dim=config.hidden_dim,
                      num_layers=config.num_layers, dropout=config.dropout).to(device)

    if checkpoint_path:
        ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        print(f"Loaded checkpoint: {checkpoint_path}")

    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for x, y in val_loader:
            x = x.to(device)
            pred = model(x).argmax(1).cpu()
            all_preds.extend(pred.tolist())
            all_labels.extend(y.tolist())

    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average="weighted")
    print(f"Accuracy: {acc:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(classification_report(all_labels, all_preds))

    results = {"accuracy": acc, "f1_weighted": f1}
    out_path = Path(config.output_dir) / "results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_path}")
'''},
            {"filename": "utils.py", "description": "Helper functions", "code": '''"""Utility Functions"""

import os
import random
import torch
import numpy as np
from pathlib import Path


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def format_metrics(metrics: dict) -> str:
    return " | ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in metrics.items())


def save_checkpoint(model, optimizer, epoch, config):
    path = Path(config.output_dir) / "checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
    }, path / f"checkpoint_epoch_{epoch}.pt")


def load_checkpoint(path, model, optimizer=None):
    ckpt = torch.load(path, map_location="cpu")
    model.load_state_dict(ckpt["model_state_dict"])
    if optimizer and "optimizer_state_dict" in ckpt:
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    return ckpt.get("epoch", 0)
'''},
            {"filename": "requirements.txt", "description": "Dependencies", "code": "torch>=2.0\ntransformers>=4.35\ndatasets>=2.14\nwandb>=0.15\nscikit-learn>=1.3\nnumpy>=1.24\npyyaml>=6.0\ntqdm>=4.65\nmatplotlib>=3.7\n"},
            {"filename": "Makefile", "description": "Build and run targets", "code": ".PHONY: setup train eval test clean\n\nsetup:\n\tpython -m venv venv && . venv/bin/activate && pip install -r requirements.txt\n\ntrain:\n\tpython main.py --config experiment_config.yaml --mode train\n\neval:\n\tpython main.py --config experiment_config.yaml --mode eval\n\ntest:\n\tpython -m pytest tests/ -v\n\nclean:\n\trm -rf outputs/ __pycache__/ .pytest_cache/\n"},
            {"filename": "tests/test_model.py", "description": "Pytest unit tests", "code": '''"""Unit Tests"""

import torch
import pytest


def test_model_forward():
    from model import BaseModel
    model = BaseModel(input_dim=128, hidden_dim=64, output_dim=10)
    x = torch.randn(4, 128)
    out = model(x)
    assert out.shape == (4, 10)


def test_dataset_loading():
    from dataset import ResearchDataset
    ds = ResearchDataset(split="train")
    assert len(ds) > 0
    x, y = ds[0]
    assert x.shape[0] == 128


def test_config_loading():
    from config import Config
    cfg = Config()
    assert cfg.learning_rate == 1e-4
    assert cfg.batch_size == 32
    assert cfg.seed == 42
'''},
            {"filename": "README.md", "description": "Project documentation", "code": f'''# {title}

Auto-generated research scaffold by ResearchIDE.

## Setup

```bash
make setup
# or manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Train
make train
# or: python main.py --config experiment_config.yaml --mode train

# Evaluate
make eval
# or: python main.py --config experiment_config.yaml --mode eval

# Test
make test
```

## Configuration

Edit `experiment_config.yaml` to change hyperparameters.

## Project Structure

- `main.py` — Entry point
- `config.py` — Configuration dataclass
- `model.py` — Model architecture
- `dataset.py` — Data loading
- `train.py` — Training loop with wandb
- `evaluate.py` — Evaluation and metrics
- `utils.py` — Helper functions
'''},
        ],
        "setup_instructions": [
            "Create virtual environment: python -m venv venv",
            "Activate: source venv/bin/activate",
            "Install dependencies: pip install -r requirements.txt",
            "Configure: edit experiment_config.yaml",
            "Train: make train",
            "Evaluate: make eval",
        ],
        "run_command": "python main.py --config experiment_config.yaml --mode train",
        "_fallback": True,
    }


def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
