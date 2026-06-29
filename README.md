# AI Candidate Ranking System

Ranks candidates the way a great recruiter would, not by keyword matching.

## Approach
Hybrid retrieve-then-rerank:
1. Semantic retrieval (embeddings) to beat the keyword trap
2. Interpretable structured scores: career velocity, impact density
3. LLM re-rank with evidence-cited scorecards

## Structure
- `notebooks/` research (EDA, embeddings, scoring experiments)
- `src/` clean pipeline modules
- `output/ranked_candidates.csv` the deliverable
- `deck/` approach PDF

## Run
pip install -r requirements.txt
