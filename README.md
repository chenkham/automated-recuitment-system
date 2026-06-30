# AI Candidate Ranking System

Ranks candidates for the founding Senior AI Engineer role at Redrob AI, utilizing a hybrid retrieve-then-rerank architecture designed to beat keyword stuffing and filter out impossible profiles (honeypots).

## Pipeline Approach
1. **Rule-Based Filters (`src/filters.py`)**: Eliminates non-technical current titles, candidates who have only worked at services companies (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini), and ~80 honeypots with impossible date timelines or skills.
2. **Lightweight Embedding / Concept Scoring (`src/scorer.py`)**: Scores candidates against job description requirements using a lightweight local embedding model (`all-MiniLM-L6-v2`) with automatic fallback to an advanced keyword-concept scorer for offline/restricted environments.
3. **Structured Attribute & Signals Fit (`src/scorer.py`)**: Evaluates years of experience fit (targeting 5-9 years, peak 6-8), company product-focus background, location (Noida/Pune preferred), and notice period.
4. **Behavioral Platform Multiplier (`src/scorer.py`)**: Boosts candidates based on response rate, open-to-work status, and GitHub contribution activity.
5. **Hallucination-Free Reasoner (`src/reasoner.py`)**: Dynamically generates unique 1-2 sentence evidence-based reasonings based on candidate-specific profile facts.

## Directory Structure
* `src/data_loader.py` — Streams JSONL data with low memory overhead.
* `src/filters.py` — Rule exclusions for honeypots, services conglomerates, and non-tech titles.
* `src/scorer.py` — Hybrid scoring models and platform multipliers.
* `src/reasoner.py` — Factual reasoning generator.
* `rank.py` — Orchestrates data load, filtering, scoring, ranking, and output generation.
* `notebooks/` — Interactive research and dry runs (`01_eda.ipynb`, `02_features.ipynb`, `03_ranker.ipynb`).
* `submission_metadata.yaml` — Challenge metadata template.

## Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run ranking pipeline (produces `submission.csv` or similar):
   ```bash
   python rank.py --candidates ./data/raw/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl --out ./output/ranked_candidates.csv
   ```

