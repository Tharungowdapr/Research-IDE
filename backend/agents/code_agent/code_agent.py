"""Code Generation Agent - generates starter code for the research idea."""

import json, re
from typing import Dict, Any
from core.llm_client import LLMClient

CODE_SYSTEM = "You are a senior ML engineer. Generate clean, well-commented Python code. Return ONLY valid JSON."

CODE_PROMPT = """Generate starter code for this research project.

Idea: {title}
Approach: {approach}
Tech Stack: {tech_stack}
Datasets: {datasets}
Evaluation Metrics: {metrics}

Return JSON with this structure:
{{
  "files": [
    {{
      "filename": "main.py",
      "description": "Main entry point",
      "code": "# Full Python code here\\nimport torch\\n..."
    }},
    {{
      "filename": "model.py",
      "description": "Model architecture",
      "code": "..."
    }},
    {{
      "filename": "dataset.py",
      "description": "Dataset loading and preprocessing",
      "code": "..."
    }},
    {{
      "filename": "train.py",
      "description": "Training loop",
      "code": "..."
    }},
    {{
      "filename": "requirements.txt",
      "description": "Python dependencies",
      "code": "torch\\ntransformers\\nnumpy\\nscikit-learn\\nwandb\\n"
    }}
  ],
  "setup_instructions": ["Step 1", "Step 2"],
  "run_command": "python main.py --config config.yaml"
}}"""


async def run_code_generation(idea: Dict, plan: Dict, llm: LLMClient) -> Dict:
    tech = plan.get("tech_stack", {})
    datasets = [d.get("name", "") for d in plan.get("datasets", [])]
    metrics = plan.get("evaluation_metrics", [])

    prompt = CODE_PROMPT.format(
        title=idea.get("title", "Research Project"),
        approach=idea.get("approach", "ML approach"),
        tech_stack=f"Frameworks: {', '.join(tech.get('frameworks', ['PyTorch']))}",
        datasets=", ".join(datasets) or "custom dataset",
        metrics=", ".join(metrics) or "accuracy, F1",
    )

    try:
        raw = await llm.complete(prompt, system=CODE_SYSTEM, json_mode=True)
        result = _parse_json(raw)
        if "files" in result:
            return result
        return _fallback_code(idea, plan)
    except Exception as e:
        return _fallback_code(idea, plan)


def _fallback_code(idea: Dict, plan: Dict) -> Dict:
    title = idea.get("title", "Research Project")
    return {
        "files": [
            {
                "filename": "main.py",
                "description": "Main entry point",
                "code": f'''"""
{title}
Auto-generated starter code by ResearchIDE
"""

import argparse
import torch
import numpy as np
from pathlib import Path

def main(args):
    print(f"Starting experiment: {title}")
    print(f"Device: {{torch.device('cuda' if torch.cuda.is_available() else 'cpu')}}")
    
    # TODO: Load your dataset
    # dataset = load_dataset(args.data_path)
    
    # TODO: Initialize model
    # model = YourModel()
    
    # TODO: Train
    # train(model, dataset, args)
    
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, default="./data")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()
    main(args)
''',
            },
            {
                "filename": "model.py",
                "description": "Model architecture",
                "code": '''"""Model Architecture"""

import torch
import torch.nn as nn

class BaseModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )
        self.classifier = nn.Linear(hidden_dim // 2, output_dim)

    def forward(self, x):
        features = self.encoder(x)
        return self.classifier(features)
''',
            },
            {
                "filename": "train.py",
                "description": "Training loop",
                "code": '''"""Training Loop"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for batch in loader:
        x, y = batch
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        pred = model(x)
        loss = criterion(pred, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0, 0, 0
    with torch.no_grad():
        for batch in loader:
            x, y = batch
            x, y = x.to(device), y.to(device)
            pred = model(x)
            total_loss += criterion(pred, y).item()
            correct += (pred.argmax(1) == y).sum().item()
            total += len(y)
    return total_loss / len(loader), correct / total
''',
            },
            {
                "filename": "requirements.txt",
                "description": "Dependencies",
                "code": "torch>=2.0\ntransformers>=4.35\nnumpy>=1.24\nscikit-learn>=1.3\nwandb\nmatplotlib\ntqdm\n",
            },
        ],
        "setup_instructions": [
            "Create virtual environment: python -m venv venv",
            "Activate: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)",
            "Install dependencies: pip install -r requirements.txt",
            "Add your data to ./data/ directory",
            "Run: python main.py",
        ],
        "run_command": "python main.py --epochs 20 --lr 1e-4",
        "_fallback": True,
    }


def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
