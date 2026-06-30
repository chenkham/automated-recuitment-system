import argparse
import sys
import os
import pandas as pd
from tqdm import tqdm

# Import our custom modular pipeline functions
from src.data_loader import stream_candidates
from src.filters import should_filter_out
from src.scorer import CandidateScorer
from src.reasoner import generate_reasoning

# Hardcoded Job Description description to serve as the embedding comparison text
# and keyword search query. This guarantees the script is self-contained.
JOB_DESCRIPTION_TEXT = (
    "Senior AI Engineer - Founding Team. 5 to 9 years of experience. "
    "Production experience with embeddings-based retrieval systems (sentence-transformers, BGE, E5, OpenAI) "
    "and vector databases or hybrid search (Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, FAISS). "
    "Strong Python, designing evaluation frameworks for ranking systems (NDCG, MRR, MAP). "
    "Experience shipping recommendation systems at product startups."
)

def main():
    parser = argparse.ArgumentParser(description="Redrob AI Candidate Ranking Pipeline")
    parser.add_argument("--candidates", required=True, help="Path to candidates JSONL file")
    parser.add_argument("--out", required=True, help="Path to output submission CSV file")
    args = parser.parse_args()
    
    if not os.path.exists(args.candidates):
        print(f"Error: Candidate file '{args.candidates}' not found.")
        sys.exit(1)
        
    print("Initializing Scorer...")
    scorer = CandidateScorer()
    
    scored_candidates = []
    print("Processing and filtering candidates...")
    
    # We load and filter candidates on the fly to save memory
    for c in tqdm(stream_candidates(args.candidates), desc="Streaming Candidates"):
        cid = c.get("candidate_id")
        
        # 1. Apply hard rules and honeypot filters
        if should_filter_out(c):
            continue
            
        # 2. Score candidate against the JD
        score = scorer.score_candidate(c, JOB_DESCRIPTION_TEXT)
        
        scored_candidates.append({
            "candidate_id": cid,
            "score": score,
            "raw_candidate": c
        })
        
    print(f"Total candidates passed filters: {len(scored_candidates):,}")
    
    # 3. Sort candidates.
    # Rules: Score descending.
    # Tie-break: candidate_id ascending (e.g. CAND_0000001 before CAND_0000002).
    print("Sorting and ranking candidates...")
    scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Keep only the top 100
    top_100 = scored_candidates[:100]
    
    # 4. Generate reasonings for the top 100
    results = []
    for i, item in enumerate(top_100):
        rank = i + 1
        score = item["score"]
        c = item["raw_candidate"]
        
        reasoning = generate_reasoning(c, rank, score)
        
        results.append({
            "candidate_id": item["candidate_id"],
            "rank": rank,
            "score": round(score, 4),
            "reasoning": reasoning
        })
        
    # Write output to CSV
    print(f"Writing ranked candidates to '{args.out}'...")
    df_out = pd.DataFrame(results)
    
    # Ensure correct columns and order
    df_out = df_out[["candidate_id", "rank", "score", "reasoning"]]
    df_out.to_csv(args.out, index=False, encoding="utf-8")
    
    print("Ranking complete. Submission file generated successfully.")

if __name__ == "__main__":
    main()
