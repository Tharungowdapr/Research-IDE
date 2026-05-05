"""
Build Guide Agent — replaces code generation.
Produces a detailed, step-by-step implementation guide that a developer
can follow to build the chosen research project from scratch.
"""

from typing import Dict, Any, List, Optional
from core.llm_client import LLMClient
from core.utils import safe_parse_llm_json, truncate_text

GUIDE_SYSTEM = (
    "You are a senior researcher and domain expert. "
    "Write clear, detailed, actionable execution/build guides for research projects. "
    "DO NOT ASSUME THIS IS A SOFTWARE/AI PROJECT unless the domain is software/AI. "
    "If it is biology, chemistry, engineering, social science, etc., outline the laboratory protocols, "
    "experimental setups, hardware fabrication, surveys, or mathematical modeling steps instead. "
    "Return ONLY valid JSON."
)

GUIDE_PROMPT = """Write a complete step-by-step build guide for this research project.

Project Title: {title}
Description: {description}
Technical Approach: {approach}
Domain: {domain}
Constraints: {constraints}
Suggested Methods: {methods}
Suggested Datasets: {datasets}
Evaluation Metrics: {metrics}
Time Estimate: {time_estimate}
Difficulty: {difficulty}

The guide must cover everything a developer needs from zero to working prototype.

Return a JSON object with this structure:
{{
  "project_name": "string",
  "one_line_summary": "string",
  "estimated_total_time": "string",
  "difficulty": "string",

  "prerequisites": {{
    "knowledge": ["Domain specific concept 1", "Domain specific concept 2"],
    "tools": ["Lab equipment, software, or machinery needed"],
    "materials": ["Chemicals, datasets, or physical materials needed"]
  }},

  "project_structure": {{
    "description": "How to organise the project workspace, lab notebooks, or directories",
    "directories": [
      {{"path": "data/", "purpose": "Raw and processed datasets/experimental logs"}},
      {{"path": "protocols/", "purpose": "Standard operating procedures"}},
      {{"path": "analysis/", "purpose": "Data analysis scripts or notebooks"}}
    ],
    "key_files": [
      {{"file": "README.md", "purpose": "Project overview"}},
      {{"file": "protocol_v1.pdf", "purpose": "Detailed methodology"}}
    ]
  }},

  "environment_setup": {{
    "description": "How to set up the lab, software environment, or workspace",
    "steps": [
      {{"step": 1, "title": "Setup workspace", "command": "Action or command", "note": ""}}
    ],
    "requirements": ["List of critical requirements"]
  }},

  "phases": [
    {{
      "phase": 1,
      "title": "Data Collection & Preparation",
      "duration": "X days/weeks",
      "goal": "What you will have at the end of this phase",
      "steps": [
        {{
          "step": 1,
          "title": "Step title",
          "description": "Detailed description of what to do and why",
          "command_or_code": "# code snippet or terminal command here",
          "expected_output": "What you should see when this works",
          "common_issues": ["Issue 1: how to fix", "Issue 2: how to fix"]
        }}
      ],
      "phase_deliverable": "What you produce at the end of this phase"
    }}
  ],

  "architecture_guide": {{
    "overview": "High-level description of the system architecture or experimental design",
    "components": [
      {{
        "name": "Component/Apparatus name",
        "purpose": "What this does",
        "implementation_hint": "Key detail, material, or library",
        "code_sketch": "Pseudocode, formula, or protocol snippet"
      }}
    ],
    "data_flow": ["Input → Process → Output"],
    "design_decisions": [
      {{"decision": "Why use X over Y", "reasoning": "Because..."}}
    ]
  }},

  "key_implementation_details": [
    {{
      "topic": "Critical execution step",
      "explanation": "What the challenge is and how to handle it",
      "code_snippet": "Relevant code, formula, or protocol"
    }}
  ],

  "training_guide": {{
    "overview": "How to execute the core experiment or training",
    "hyperparameters": [
      {{"name": "variable_name", "recommended": "value", "range": "min-max", "note": "Why this value"}}
    ],
    "training_command": "Command or physical action to start",
    "monitoring": "How to track progress safely",
    "checkpointing": "How to save intermediate results",
    "expected_training_time": "Time estimate"
  }},

  "evaluation_guide": {{
    "metrics": [
      {{"metric": "Name", "why": "Why use this", "how_to_compute": "Formula or script"}}
    ],
    "baseline_comparison": "What to compare against",
    "evaluation_command": "Action to evaluate",
    "how_to_interpret": "What good results look like"
  }},

  "experiment_tracking": {{
    "tool": "Lab notebook, Weights & Biases, or Excel",
    "setup_steps": ["How to set it up"],
    "what_to_log": ["Variables to track over time"]
  }},

  "debugging_guide": [
    {{
      "problem": "Common problem description",
      "symptoms": "What you observe",
      "solution": "How to fix it",
      "prevention": "How to avoid it"
    }}
  ],

  "next_steps": {{
    "improvements": ["Improvement 1 to try after baseline works", "Improvement 2"],
    "ablation_studies": ["Ablation 1: remove X to see its contribution", "Ablation 2"],
    "paper_checklist": ["Reproduce baseline results", "Run ablations", "Statistical significance tests", "Write related work"]
  }},

  "resources": [
    {{"title": "Resource name", "url": "https://...", "why": "Why this is useful"}}
  ]
}}"""


async def run_code_generation(
    idea: Dict,
    plan: Dict,
    llm: LLMClient,
    file_hints: Optional[List[str]] = None,
) -> Dict:
    """Generate a comprehensive build guide instead of code files."""
    domain = ", ".join([] if not plan else plan.get("tech_stack", {}).get("languages", ["Python"]))
    constraints = _fmt_constraints(idea)
    
    prompt = GUIDE_PROMPT.format(
        title=idea.get("title", "Research Project"),
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        domain=", ".join([]),
        constraints=constraints,
        methods=", ".join(idea.get("suggested_methods", [])[:5]) or "deep learning, transformers",
        datasets=", ".join(idea.get("suggested_datasets", [])[:3]) or "standard benchmarks",
        metrics=", ".join(plan.get("evaluation_metrics", [])[:4]) if plan else "accuracy, F1",
        time_estimate=idea.get("time_estimate", "2-3 months"),
        difficulty=idea.get("difficulty", "intermediate"),
    )

    try:
        raw = await llm.complete(prompt, system=GUIDE_SYSTEM, json_mode=True)
        result = safe_parse_llm_json(raw, default=None)
        if isinstance(result, dict) and result.get("phases"):
            return result
    except Exception as e:
        print(f"[BuildGuide LLM failed: {e}]")

    return _fallback_guide(idea, plan)


def _fmt_constraints(idea: Dict) -> str:
    parts = []
    if idea.get("difficulty"): parts.append(f"difficulty: {idea['difficulty']}")
    if idea.get("time_estimate"): parts.append(f"timeline: {idea['time_estimate']}")
    if idea.get("feasibility"): parts.append(f"feasibility: {idea['feasibility']}")
    return ", ".join(parts) or "standard research constraints"


def _fallback_guide(idea: Dict, plan: Dict) -> Dict:
    """Structured fallback guide when LLM fails."""
    title = idea.get("title", "Research Project")
    approach = idea.get("approach", "deep learning approach")
    methods = idea.get("suggested_methods", ["PyTorch", "HuggingFace Transformers"])
    datasets = idea.get("suggested_datasets", ["standard benchmark dataset"])
    metrics = plan.get("evaluation_metrics", ["accuracy", "F1"]) if plan else ["accuracy", "F1"]

    return {
        "project_name": title,
        "one_line_summary": idea.get("description", "")[:120],
        "estimated_total_time": idea.get("time_estimate", "2-3 months"),
        "difficulty": idea.get("difficulty", "intermediate"),

        "prerequisites": {
            "knowledge": ["Python 3.9+", "PyTorch basics", "Machine learning fundamentals", "Git"],
            "tools": ["Python 3.9+", "pip or conda", "Git", "Text editor or IDE (VSCode recommended)"],
            "accounts": ["HuggingFace account (free) for datasets/models", "Weights & Biases account (free tier) for experiment tracking"],
        },

        "project_structure": {
            "description": "Recommended directory layout for this project",
            "directories": [
                {"path": "data/raw/", "purpose": "Original downloaded datasets"},
                {"path": "data/processed/", "purpose": "Cleaned and preprocessed data ready for training"},
                {"path": "src/", "purpose": "All Python source code"},
                {"path": "configs/", "purpose": "YAML configuration files for experiments"},
                {"path": "outputs/checkpoints/", "purpose": "Saved model weights"},
                {"path": "outputs/results/", "purpose": "Evaluation results, metrics, plots"},
                {"path": "notebooks/", "purpose": "Jupyter notebooks for exploration and visualization"},
                {"path": "tests/", "purpose": "Unit tests for your code"},
            ],
            "key_files": [
                {"file": "src/model.py", "purpose": "Model architecture"},
                {"file": "src/dataset.py", "purpose": "Dataset loading and preprocessing"},
                {"file": "src/train.py", "purpose": "Training loop with logging"},
                {"file": "src/evaluate.py", "purpose": "Evaluation and metric computation"},
                {"file": "src/utils.py", "purpose": "Shared utilities (seed, device, checkpointing)"},
                {"file": "configs/base.yaml", "purpose": "Base hyperparameters"},
                {"file": "requirements.txt", "purpose": "Python dependencies"},
                {"file": "README.md", "purpose": "Project documentation"},
            ],
        },

        "environment_setup": {
            "description": "Set up your Python environment before writing any code",
            "steps": [
                {"step": 1, "title": "Create virtual environment", "command": "python -m venv venv\nsource venv/bin/activate  # Linux/Mac\n# Windows: venv\\Scripts\\activate", "note": "Always use a virtual environment to avoid dependency conflicts"},
                {"step": 2, "title": "Install PyTorch", "command": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118", "note": "Visit pytorch.org to get the right command for your CUDA version. Use 'cpu' version if no GPU."},
                {"step": 3, "title": "Install ML libraries", "command": f"pip install transformers datasets wandb scikit-learn numpy pandas pyyaml tqdm matplotlib", "note": "These cover the core ML workflow"},
                {"step": 4, "title": "Verify installation", "command": "python -c \"import torch; print(torch.__version__, torch.cuda.is_available())\"", "note": "Should print version number and True/False for CUDA"},
                {"step": 5, "title": "Initialize git", "command": "git init\necho 'venv/\ndata/\noutputs/\n*.pyc\n__pycache__/' > .gitignore", "note": "Never commit data or model weights to git"},
            ],
            "requirements": ["torch>=2.1.0", "transformers>=4.40.0", "datasets>=2.18.0", "wandb", "scikit-learn>=1.3.0", "numpy>=1.24.0", "pandas>=2.0.0", "pyyaml>=6.0", "tqdm", "matplotlib"],
        },

        "phases": [
            {
                "phase": 1,
                "title": "Literature Review & Problem Scoping",
                "duration": "3-5 days",
                "goal": "Deep understanding of the problem and existing approaches before writing any code",
                "steps": [
                    {
                        "step": 1,
                        "title": "Read the top 10 papers from your retrieved list",
                        "description": "Focus on their methodology, datasets used, and reported results. Take notes on what each paper does and where it falls short. These gaps are your opportunity.",
                        "command_or_code": "# Create a literature notes file\ntouch notes/literature_review.md\n\n# For each paper, note:\n# - What problem they solve\n# - Their methodology\n# - Dataset + evaluation setup\n# - Key results\n# - Limitations / future work",
                        "expected_output": "A clear understanding of the landscape. You should be able to explain why your approach is different.",
                        "common_issues": ["Reading too broadly — focus on your specific subfield", "Skipping related work — it reveals baselines you must compare against"],
                    },
                    {
                        "step": 2,
                        "title": "Define your baseline",
                        "description": "Choose the strongest existing method as your baseline. You must beat it or show a meaningful trade-off. Find its official code on GitHub.",
                        "command_or_code": "# Search PapersWithCode for your task\n# https://paperswithcode.com\n# Find: task → datasets → SOTA methods → code links",
                        "expected_output": "A clear baseline method + its GitHub repo + its reported numbers on your target dataset.",
                        "common_issues": ["Choosing a weak baseline makes results look better but reviewers will reject"],
                    },
                    {
                        "step": 3,
                        "title": "Formalize your hypothesis",
                        "description": f"Write down in 2-3 sentences: what you claim, why you believe it will work, and how you will verify it. Example: '{approach}. We hypothesize this will improve X because Y. We will verify by measuring Z on dataset W.'",
                        "command_or_code": "# Add to README.md:\n## Hypothesis\n[Your 2-3 sentence hypothesis here]",
                        "expected_output": "A written hypothesis that guides all your decisions",
                        "common_issues": ["Vague hypothesis leads to unfocused experiments"],
                    },
                ],
                "phase_deliverable": "Literature review notes + defined baseline + written hypothesis",
            },
            {
                "phase": 2,
                "title": "Data Pipeline",
                "duration": "3-7 days",
                "goal": "Reliable, reproducible data loading and preprocessing",
                "steps": [
                    {
                        "step": 1,
                        "title": "Download and explore your dataset",
                        "description": f"Start with {', '.join(datasets[:2])}. Load it, check for class imbalance, missing values, text length distributions. Understanding your data prevents most bugs later.",
                        "command_or_code": f"from datasets import load_dataset\nimport pandas as pd\n\n# Load dataset\ndataset = load_dataset('{datasets[0] if datasets else 'your_dataset'}')\nprint(dataset)\n\n# Explore\ndf = dataset['train'].to_pandas()\nprint(df.describe())\nprint(df['label'].value_counts())  # Check class balance",
                        "expected_output": "Console output showing dataset shape, label distribution, and sample text lengths",
                        "common_issues": ["Class imbalance — use weighted sampling or loss weighting", "Very long texts — truncate or use sliding window"],
                    },
                    {
                        "step": 2,
                        "title": "Write the Dataset class",
                        "description": "Create src/dataset.py with a PyTorch Dataset class that handles tokenization, padding, and batching. Make it configurable via config YAML.",
                        "command_or_code": "# src/dataset.py skeleton\nimport torch\nfrom torch.utils.data import Dataset\nfrom transformers import AutoTokenizer\n\nclass ResearchDataset(Dataset):\n    def __init__(self, data, tokenizer, max_length=512):\n        self.data = data\n        self.tokenizer = tokenizer\n        self.max_length = max_length\n\n    def __len__(self):\n        return len(self.data)\n\n    def __getitem__(self, idx):\n        item = self.data[idx]\n        encoding = self.tokenizer(\n            item['text'],\n            max_length=self.max_length,\n            padding='max_length',\n            truncation=True,\n            return_tensors='pt'\n        )\n        return {\n            'input_ids': encoding['input_ids'].squeeze(),\n            'attention_mask': encoding['attention_mask'].squeeze(),\n            'labels': torch.tensor(item['label'])\n        }",
                        "expected_output": "Dataset that returns correct tensor shapes when indexed",
                        "common_issues": ["Forgetting to squeeze tensors from tokenizer", "Not handling missing labels"],
                    },
                    {
                        "step": 3,
                        "title": "Write a data validation script",
                        "description": "Before training, always validate: shapes, dtypes, label distribution in each split, no NaN values. 30 minutes here saves hours of debugging later.",
                        "command_or_code": "# Add to a notebook or scripts/validate_data.py\nfrom torch.utils.data import DataLoader\n\nloader = DataLoader(dataset, batch_size=4)\nbatch = next(iter(loader))\nprint('input_ids shape:', batch['input_ids'].shape)\nprint('labels shape:', batch['labels'].shape)\nprint('label distribution:', batch['labels'].bincount())\nassert batch['input_ids'].dtype == torch.long",
                        "expected_output": "All assertions pass, shapes look correct",
                        "common_issues": ["Wrong dtype causes silent errors in loss computation"],
                    },
                ],
                "phase_deliverable": "src/dataset.py + validation script that confirms data pipeline works end-to-end",
            },
            {
                "phase": 3,
                "title": "Model Implementation",
                "duration": "5-10 days",
                "goal": f"Implement {approach} and verify it runs correctly",
                "steps": [
                    {
                        "step": 1,
                        "title": "Start with a pretrained baseline",
                        "description": f"Before implementing your novel method, first get a standard pretrained model working end-to-end. This is your reference point. Use one of: {', '.join(methods[:3]) if methods else 'BERT, RoBERTa, or DistilBERT'}.",
                        "command_or_code": "# src/model.py — start simple\nfrom transformers import AutoModelForSequenceClassification\n\nmodel = AutoModelForSequenceClassification.from_pretrained(\n    'bert-base-uncased',\n    num_labels=num_classes\n)\n\n# Test forward pass with dummy data\nimport torch\ndummy_ids = torch.randint(0, 1000, (2, 128))\ndummy_mask = torch.ones(2, 128, dtype=torch.long)\noutputs = model(input_ids=dummy_ids, attention_mask=dummy_mask)\nprint('Output logits shape:', outputs.logits.shape)  # Should be (2, num_classes)",
                        "expected_output": "Forward pass runs without errors, output shape is correct",
                        "common_issues": ["num_labels mismatch with dataset — double check", "OOM error — reduce batch size or max_length"],
                    },
                    {
                        "step": 2,
                        "title": "Implement your novel contribution",
                        "description": f"Now add your specific innovation: {approach}. Keep the change modular — it should be easy to ablate (turn on/off) for your experiments.",
                        "command_or_code": f"# Add your method as a module\n# Good pattern: inherit from nn.Module\nimport torch.nn as nn\n\nclass YourContribution(nn.Module):\n    def __init__(self, config):\n        super().__init__()\n        # Initialize your components here\n        pass\n\n    def forward(self, x):\n        # Your method logic here\n        return x",
                        "expected_output": "Modified model passes forward pass with same input/output interface",
                        "common_issues": ["Breaking the interface — keep input/output shapes consistent", "Not making it ablatable — add a config flag to disable it"],
                    },
                    {
                        "step": 3,
                        "title": "Write unit tests for your model",
                        "description": "Test: (1) forward pass with known shapes, (2) gradient flow works, (3) output dtype correct. Catch bugs before 8-hour training runs.",
                        "command_or_code": "# tests/test_model.py\nimport torch\nfrom src.model import YourModel\n\ndef test_forward_pass():\n    model = YourModel(num_labels=2)\n    x = torch.randint(0, 1000, (4, 128))\n    mask = torch.ones(4, 128, dtype=torch.long)\n    out = model(x, mask)\n    assert out.logits.shape == (4, 2)\n\ndef test_gradients():\n    model = YourModel(num_labels=2)\n    x = torch.randint(0, 1000, (2, 128))\n    out = model(x, torch.ones_like(x))\n    loss = out.logits.sum()\n    loss.backward()\n    for p in model.parameters():\n        if p.requires_grad:\n            assert p.grad is not None\n\n# Run: pytest tests/test_model.py -v",
                        "expected_output": "All tests pass in < 10 seconds",
                        "common_issues": ["Detached tensors have no grad — check your forward pass for .detach() calls"],
                    },
                ],
                "phase_deliverable": "src/model.py with your contribution + passing unit tests",
            },
            {
                "phase": 4,
                "title": "Training & Experimentation",
                "duration": "7-14 days",
                "goal": "Train baseline, then your method, compare results systematically",
                "steps": [
                    {
                        "step": 1,
                        "title": "Write the training loop",
                        "description": "Implement src/train.py with: optimizer, scheduler, gradient clipping, checkpointing, and wandb logging. Use AdamW + linear warmup as default — it works for most transformer fine-tuning.",
                        "command_or_code": "# Key components of train.py\nfrom transformers import get_linear_schedule_with_warmup\nimport wandb\n\n# Optimizer\noptimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=0.01)\n\n# Scheduler\nnum_steps = len(train_loader) * cfg.epochs\nscheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=num_steps//10, num_training_steps=num_steps)\n\n# Training step\nfor batch in train_loader:\n    optimizer.zero_grad()\n    outputs = model(**batch)\n    loss = outputs.loss\n    loss.backward()\n    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # Prevent exploding gradients\n    optimizer.step()\n    scheduler.step()\n    wandb.log({'train_loss': loss.item()})",
                        "expected_output": "Training loss decreasing over first few steps (sanity check on 1 epoch)",
                        "common_issues": ["Loss is NaN — learning rate too high or bad data batch", "Loss not decreasing — check label mapping, loss function"],
                    },
                    {
                        "step": 2,
                        "title": "Overfit on a tiny batch first",
                        "description": "BEFORE full training, overfit your model on 10-20 examples. If your model can't memorize 10 examples, something is wrong with your model or data pipeline. This is the most important debugging step.",
                        "command_or_code": "# Sanity check: should reach ~0 loss in < 50 steps\ntiny_dataset = train_dataset[:20]\nfor step in range(100):\n    batch = collate(tiny_dataset)\n    loss = train_step(model, batch, optimizer)\n    if step % 10 == 0:\n        print(f'Step {step}: loss={loss:.4f}')\n# Expected: loss should drop to near 0",
                        "expected_output": "Training loss drops to < 0.01 on tiny batch within 50-100 steps",
                        "common_issues": ["Loss stays high — wrong loss function or label encoding", "Loss oscillates — learning rate too high"],
                    },
                    {
                        "step": 3,
                        "title": "Run full experiments with configs",
                        "description": "Create a YAML config for each experiment. Train baseline first, then your method. Log everything to wandb. Run at least 3 seeds for each condition to get variance estimates.",
                        "command_or_code": "# configs/baseline.yaml\nmodel_name: bert-base-uncased\nlr: 2e-5\nbatch_size: 32\nepochs: 5\nmax_length: 256\nseed: 42\n\n# configs/our_method.yaml  \nmodel_name: bert-base-uncased\nuse_our_method: true  # your ablation flag\nlr: 2e-5\nbatch_size: 32\nepochs: 5\n\n# Run:\npython src/train.py --config configs/baseline.yaml\npython src/train.py --config configs/our_method.yaml",
                        "expected_output": "Two sets of results in wandb, clearly labeled. Your method should show improvement.",
                        "common_issues": ["Forgetting to set random seed — results not reproducible", "Only running 1 seed — variance too high to draw conclusions"],
                    },
                ],
                "phase_deliverable": "Trained models + wandb experiment logs + comparison table showing baseline vs your method",
            },
            {
                "phase": 5,
                "title": "Evaluation & Analysis",
                "duration": "3-5 days",
                "goal": f"Rigorous evaluation on {', '.join(metrics)} + error analysis",
                "steps": [
                    {
                        "step": 1,
                        "title": "Evaluate on test set",
                        "description": "ONLY evaluate on the test set once — after all hyperparameter tuning is done on the validation set. This is standard research ethics. Report mean ± std across 3+ seeds.",
                        "command_or_code": f"# src/evaluate.py\nfrom sklearn.metrics import f1_score, classification_report\nimport json\n\ndef evaluate(model, test_loader, device):\n    model.eval()\n    all_preds, all_labels = [], []\n    with torch.no_grad():\n        for batch in test_loader:\n            logits = model(**batch).logits\n            preds = logits.argmax(-1).cpu()\n            all_preds.extend(preds.tolist())\n            all_labels.extend(batch['labels'].cpu().tolist())\n\n    results = {{'f1': f1_score(all_labels, all_preds, average='weighted'),\n                'report': classification_report(all_labels, all_preds)}}\n    print(results)\n    json.dump(results, open('outputs/results.json','w'))\n    return results",
                        "expected_output": f"JSON file with {', '.join(metrics)} numbers + classification report",
                        "common_issues": ["Testing multiple times — inflates results. Test ONCE on final model", "Forgetting weighted vs macro F1 — specify which you report"],
                    },
                    {
                        "step": 2,
                        "title": "Error analysis",
                        "description": "Look at your model's mistakes. What types of examples does it get wrong? This gives you ablation ideas and shows reviewers you understand your model's limitations.",
                        "command_or_code": "# Find misclassified examples\nerrors = [(text, pred, true) for text, pred, true in zip(texts, preds, labels) if pred != true]\n\n# Group by error type\nfor error_text, pred_label, true_label in errors[:20]:\n    print(f'True: {true_label} | Predicted: {pred_label}')\n    print(f'Text: {error_text[:100]}')\n    print('---')",
                        "expected_output": "A list of failure patterns (e.g. 'model fails on sarcasm', 'struggles with domain-specific terms')",
                        "common_issues": ["Only reporting aggregate numbers — reviewers want to understand failure modes"],
                    },
                    {
                        "step": 3,
                        "title": "Ablation studies",
                        "description": "Remove each component of your method one at a time and measure the performance drop. This proves each part of your contribution is necessary.",
                        "command_or_code": "# Create ablation configs:\n# configs/ablation_no_component_A.yaml\n# configs/ablation_no_component_B.yaml\n\n# Build a results table:\n# Method              | F1    | Accuracy\n# Full model          | 0.87  | 0.88\n# Without component A | 0.83  | 0.84  (-4.6%)\n# Without component B | 0.85  | 0.86  (-2.3%)\n# Baseline            | 0.79  | 0.81",
                        "expected_output": "Ablation table showing contribution of each component",
                        "common_issues": ["Not running ablations — weakens the paper significantly", "Running only 1 seed per ablation — results noisy"],
                    },
                ],
                "phase_deliverable": "Results JSON + error analysis report + ablation table",
            },
            {
                "phase": 6,
                "title": "Documentation & Paper Writing",
                "duration": "5-10 days",
                "goal": "Reproducible code + written paper draft",
                "steps": [
                    {
                        "step": 1,
                        "title": "Write README.md",
                        "description": "A good README lets anyone reproduce your results in < 30 minutes. Include: project description, requirements, installation, training command, evaluation command, and results table.",
                        "command_or_code": "# README template:\n# # Project Title\n# ## Quick Start\n# git clone ...\n# pip install -r requirements.txt\n# python src/train.py --config configs/our_method.yaml\n# ## Results\n# | Method | F1 | Acc |\n# |--------|----|----|",
                        "expected_output": "Someone else can reproduce your results following the README",
                        "common_issues": ["Missing environment details — specify exact Python/CUDA versions"],
                    },
                    {
                        "step": 2,
                        "title": "Write the paper using your generated draft",
                        "description": "Your ResearchIDE has already generated an IEEE-format paper draft in the Paper tab. Use it as your starting point. Fill in the actual results numbers, expand the methodology, and add your ablation table.",
                        "command_or_code": "# Paper structure:\n# 1. Introduction: problem, why it matters, your contribution (3 claims)\n# 2. Related Work: what others did, how you differ\n# 3. Methodology: your approach with equations/diagrams\n# 4. Experiments: dataset, metrics, baselines, results table\n# 5. Analysis: ablations, error analysis, case studies\n# 6. Conclusion: summary, limitations, future work",
                        "expected_output": "Complete paper draft with all sections filled in",
                        "common_issues": ["Writing intro last — actually write it last (it's easier)", "Weak related work — reviewers check this carefully"],
                    },
                ],
                "phase_deliverable": "Clean reproducible codebase + paper draft",
            },
        ],

        "architecture_guide": {
            "overview": f"The system follows a standard ML pipeline adapted for: {approach}",
            "components": [
                {"name": "Data Pipeline", "purpose": "Load, preprocess, and batch training data", "implementation_hint": "Use HuggingFace datasets + DataLoader with num_workers=4", "code_sketch": "from datasets import load_dataset\ndataset = load_dataset('your_dataset')"},
                {"name": "Model", "purpose": f"Implements {approach}", "implementation_hint": f"Start from pretrained: {methods[0] if methods else 'bert-base-uncased'}", "code_sketch": "from transformers import AutoModel\nencoder = AutoModel.from_pretrained('bert-base-uncased')"},
                {"name": "Training Loop", "purpose": "Optimize model parameters with gradient descent", "implementation_hint": "AdamW + linear warmup scheduler + gradient clipping at 1.0", "code_sketch": "loss.backward(); clip_grad_norm_(model.parameters(), 1.0); optimizer.step()"},
                {"name": "Evaluator", "purpose": "Measure model performance on held-out data", "implementation_hint": f"Compute {', '.join(metrics[:2])} on validation and test sets", "code_sketch": "from sklearn.metrics import f1_score"},
            ],
            "data_flow": [
                "Raw text → Tokenizer → input_ids, attention_mask",
                "Tokens → Encoder → Hidden states",
                "Hidden states → Your method → Enhanced representations",
                "Enhanced repr → Classifier head → Logits",
                "Logits vs ground truth → Loss → Backprop → Updated weights",
            ],
            "design_decisions": [
                {"decision": "Why start with a pretrained model", "reasoning": "Transfer learning from large pretrained models almost always outperforms training from scratch on limited data"},
                {"decision": "Why AdamW over SGD", "reasoning": "AdamW handles sparse gradients better and decouples weight decay from learning rate — standard for transformer fine-tuning"},
                {"decision": f"Why use {datasets[0] if datasets else 'this dataset'}", "reasoning": "Standard benchmark allows fair comparison with published baselines"},
            ],
        },

        "training_guide": {
            "overview": "Use AdamW optimizer with linear warmup — standard for transformer fine-tuning",
            "hyperparameters": [
                {"name": "learning_rate", "recommended": "2e-5", "range": "1e-5 to 5e-5", "note": "Lower for larger models (3B+)"},
                {"name": "batch_size", "recommended": "32", "range": "8 to 64", "note": "Larger = more stable gradients but more GPU RAM"},
                {"name": "epochs", "recommended": "5", "range": "3 to 10", "note": "Use early stopping based on validation F1"},
                {"name": "max_length", "recommended": "256", "range": "128 to 512", "note": "Longer = more context but more memory"},
                {"name": "warmup_ratio", "recommended": "0.1", "range": "0.05 to 0.15", "note": "10% of total steps for warmup"},
                {"name": "weight_decay", "recommended": "0.01", "range": "0 to 0.1", "note": "Regularisation — prevents overfitting"},
            ],
            "training_command": "python src/train.py --config configs/base.yaml",
            "monitoring": "Open wandb dashboard at wandb.ai — watch train_loss, val_loss, val_f1. Stop early if val_f1 stops improving for 3 epochs.",
            "checkpointing": "Save model when val_f1 improves: torch.save(model.state_dict(), 'outputs/best_model.pt')",
            "expected_training_time": "20-60 min per epoch on a single A100/V100 GPU. ~2-5 hours total for 5 epochs.",
        },

        "evaluation_guide": {
            "metrics": [
                {"metric": m, "why": "Standard metric for this task type", "how_to_compute": f"from sklearn.metrics import {m.lower().replace(' ','_')}_score"}
                for m in metrics[:4]
            ],
            "baseline_comparison": f"Compare against the strongest published baseline on {datasets[0] if datasets else 'your dataset'}. Find their reported numbers in their paper and verify by running their code.",
            "evaluation_command": "python src/evaluate.py --checkpoint outputs/best_model.pt --split test",
            "how_to_interpret": f"Your method should improve {metrics[0] if metrics else 'F1'} by at least 1-2 points absolute over the baseline to be worth publishing. Statistical significance testing (p < 0.05) is required.",
        },

        "experiment_tracking": {
            "tool": "Weights & Biases (wandb)",
            "setup_steps": ["pip install wandb", "wandb login  # paste your API key from wandb.ai", "Add wandb.init(project='your-project', config=cfg) to start of train.py", "Add wandb.log({...}) inside the training loop"],
            "what_to_log": ["train_loss (every step)", "val_loss (every epoch)", f"val_{metrics[0].lower().replace(' ','_') if metrics else 'f1'} (every epoch)", "learning_rate", "epoch", "best_val_metric"],
        },

        "debugging_guide": [
            {"problem": "Loss is NaN from the first step", "symptoms": "loss=nan in logs", "solution": "Check for zeros in denominators, extreme values in data, or learning rate too high (try 1e-6 first)", "prevention": "Always validate data before training"},
            {"problem": "Training loss decreases but validation loss increases", "symptoms": "Overfitting curve in wandb", "solution": "Add dropout, reduce model size, increase weight_decay, use early stopping, or get more data", "prevention": "Monitor val_loss from the start"},
            {"problem": "CUDA out of memory", "symptoms": "RuntimeError: CUDA out of memory", "solution": "Reduce batch_size by half, reduce max_length, use gradient accumulation, or use fp16 training", "prevention": "Start with small batch size and scale up"},
            {"problem": "Reproducibility issues — different results each run", "symptoms": "Results vary significantly between runs", "solution": "Set all seeds: torch.manual_seed(42), random.seed(42), np.random.seed(42), torch.backends.cudnn.deterministic=True", "prevention": "Always set seeds at the top of train.py"},
            {"problem": "Model doesn't converge", "symptoms": "Loss stays flat or oscillates", "solution": "Check data pipeline is returning correct labels, check loss function is correct for your task, try lower learning rate", "prevention": "Always do the tiny-batch overfit test first"},
        ],

        "next_steps": {
            "improvements": [
                "Try larger pretrained models (e.g. RoBERTa-large instead of base)",
                "Experiment with different pooling strategies",
                "Add data augmentation for minority classes",
                f"Cross-dataset evaluation — test on a related {datasets[1] if len(datasets) > 1 else 'second'} dataset",
                "Distillation — compress your model for deployment",
            ],
            "ablation_studies": [
                "Remove your main contribution — how much does F1 drop?",
                "Replace pretrained model with smaller/larger variant",
                "Vary training data size — does your method benefit from more data?",
                "Effect of max_length — shorter vs longer context",
            ],
            "paper_checklist": [
                "Run experiments with 3+ random seeds and report mean ± std",
                "Statistical significance test (paired t-test or bootstrap)",
                "Reproduce baseline results yourself (don't just copy their numbers)",
                "Error analysis section with qualitative examples",
                "Ablation table in main paper or appendix",
                "Compute efficiency comparison (params, FLOPs, inference time)",
                "Release code on GitHub for reproducibility",
            ],
        },

        "resources": [
            {"title": "HuggingFace Course", "url": "https://huggingface.co/learn/nlp-course", "why": "Best free resource for transformer fine-tuning"},
            {"title": "Papers With Code", "url": "https://paperswithcode.com", "why": "Find SOTA baselines and their code for your task"},
            {"title": "Weights & Biases Quickstart", "url": "https://docs.wandb.ai/quickstart", "why": "Experiment tracking setup in 5 minutes"},
            {"title": "PyTorch Documentation", "url": "https://pytorch.org/docs/stable/", "why": "Reference for all PyTorch operations"},
            {"title": "The Illustrated Transformer", "url": "http://jalammar.github.io/illustrated-transformer/", "why": "Visual explanation of transformer architecture"},
            {"title": "Andrej Karpathy's makemore", "url": "https://github.com/karpathy/makemore", "why": "Learn to build language models from scratch"},
        ],
    }

# Backward compatibility aliases (used by tests)
_fallback_code = _fallback_guide
EXPECTED_FILES = [
    "phases", "prerequisites", "environment_setup",
    "training_guide", "evaluation_guide", "debugging_guide",
    "next_steps", "resources",
]
