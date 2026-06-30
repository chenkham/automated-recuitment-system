import re
from datetime import datetime
import numpy as np

# Key keywords to search for technical experience
CORE_AI_KEYWORDS = [
    "ai", "ml", "machine learning", "nlp", "natural language processing",
    "retrieval", "search", "recommendation", "ranking", "vector search",
    "embeddings", "deep learning", "llm", "large language model", "transformers",
    "learning to rank", "information retrieval", "rag", "fine-tuning"
]

# Boost for product companies and common product startups
PRODUCT_BUZZWORDS = ["product", "saas", "platform", "startup", "scale-up", "real-time", "microservices"]
TOP_PRODUCT_COMPANIES = ["swiggy", "zomato", "zoho", "paytm", "flipkart", "ola", "uber", "netflix", "adobe", "apple", "google", "meta", "microsoft", "amazon", "razorpay"]

# Key locations for hybrid/relocation fit
PUNE_NOIDA = ["pune", "noida"]
INDIAN_CITIES = ["hyderabad", "mumbai", "bangalore", "bengaluru", "chennai", "delhi", "ncr", "kolkata", "jaipur"]

class CandidateScorer:
    def __init__(self):
        self.has_semantic_model = False
        try:
            from sentence_transformers import SentenceTransformer
            # Try to load a tiny local model. If offline and not cached, this will raise an exception.
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.has_semantic_model = True
            print("Loaded semantic embedding model (all-MiniLM-L6-v2) successfully.")
        except Exception as e:
            print(f"Semantic model could not be loaded ({e}). Falling back to advanced keyword-concept matching.")

    def get_semantic_similarity(self, text1: str, text2: str) -> float:
        """Computes cosine similarity between two texts using sentence-transformers."""
        if not self.has_semantic_model:
            return 0.0
        try:
            emb1 = self.model.encode(text1, convert_to_numpy=True)
            emb2 = self.model.encode(text2, convert_to_numpy=True)
            dot = np.dot(emb1, emb2)
            norm = np.linalg.norm(emb1) * np.linalg.norm(emb2)
            return float(dot / norm) if norm > 0 else 0.0
        except Exception:
            return 0.0

    def compute_role_fit(self, candidate, jd_text: str) -> float:
        """
        Calculates how well the candidate's career history and titles match the Senior AI role.
        Weights current title higher than historical descriptions.
        """
        p = candidate.get("profile", {})
        history = candidate.get("career_history", [])
        
        current_title = p.get("current_title", "").lower()
        headline = p.get("headline", "").lower()
        summary = p.get("summary", "").lower()
        
        # 1. Semantic Match (if available)
        semantic_score = 0.0
        if self.has_semantic_model:
            combined_text = f"{current_title} {headline} {summary}"
            semantic_score = self.get_semantic_similarity(combined_text, jd_text)
            
        # 2. Keyword-Concept Match
        # Check current title
        current_title_match = sum(kw in current_title for kw in CORE_AI_KEYWORDS)
        
        # Check career history descriptions and past titles
        past_title_match = 0
        desc_match_count = 0
        
        for job in history:
            title = job.get("title", "").lower()
            desc = job.get("description", "").lower()
            
            past_title_match += sum(kw in title for kw in CORE_AI_KEYWORDS)
            desc_match_count += sum(kw in desc for kw in CORE_AI_KEYWORDS)
            
        # Normalize and combine scores
        keyword_score = (current_title_match * 0.5) + (past_title_match * 0.2) + min(desc_match_count * 0.05, 0.3)
        keyword_score = min(keyword_score, 1.0)
        
        if self.has_semantic_model:
            return 0.4 * semantic_score + 0.6 * keyword_score
        else:
            return keyword_score

    def compute_experience_fit(self, candidate) -> float:
        """
        JD prefers 5-9 years of experience, sweet spot is 6-8 years.
        Generates a score between 0.0 and 1.0 based on years of experience.
        """
        yoe = candidate.get("profile", {}).get("years_of_experience", 0)
        
        if 6.0 <= yoe <= 8.0:
            return 1.0
        elif 5.0 <= yoe < 6.0 or 8.0 < yoe <= 9.0:
            return 0.8
        elif 4.0 <= yoe < 5.0 or 9.0 < yoe <= 11.0:
            return 0.5
        elif 3.0 <= yoe < 4.0 or 11.0 < yoe <= 13.0:
            return 0.2
        else:
            return 0.0

    def compute_company_fit(self, candidate) -> float:
        """
        Rewards candidates who worked at product companies and startups.
        """
        history = candidate.get("career_history", [])
        score = 0.5 # Default middle score
        
        product_hits = 0
        for job in history:
            company = job.get("company", "").lower()
            desc = job.get("description", "").lower()
            
            # Check if worked at a top product firm
            if any(p_comp in company for p_comp in TOP_PRODUCT_COMPANIES):
                product_hits += 2
                
            # Check if description mentions startup/saas/product keywords
            if any(word in desc for word in PRODUCT_BUZZWORDS):
                product_hits += 1
                
        # Normalize to [0.0, 1.0]
        score += min(product_hits * 0.1, 0.5)
        return min(score, 1.0)

    def compute_location_fit(self, candidate) -> float:
        """
        Noida/Pune get max score (1.0).
        Other major Indian cities get a secondary boost (0.8).
        Other locations get 0.3.
        """
        p = candidate.get("profile", {})
        loc = p.get("location", "").lower()
        country = p.get("country", "").lower()
        
        if any(city in loc for city in PUNE_NOIDA):
            return 1.0
        elif any(city in loc for city in INDIAN_CITIES) or country == "india":
            return 0.8
        else:
            return 0.3

    def score_candidate(self, candidate, jd_text: str) -> float:
        """
        Combines role fit, experience fit, company fit, and location fit
        with platform availability/engagement multipliers.
        """
        role_fit = self.compute_role_fit(candidate, jd_text)
        exp_fit = self.compute_experience_fit(candidate)
        comp_fit = self.compute_company_fit(candidate)
        loc_fit = self.compute_location_fit(candidate)
        
        # Base Fit Score (weighted average)
        fit_score = (0.50 * role_fit) + (0.25 * exp_fit) + (0.15 * comp_fit) + (0.10 * loc_fit)
        
        # Availability / Engagement Multiplier
        signals = candidate.get("redrob_signals", {})
        open_to_work = signals.get("open_to_work_flag", False)
        resp_rate = signals.get("recruiter_response_rate", 0.0)
        github_score = signals.get("github_activity_score", -1)
        notice_period = signals.get("notice_period_days", 90)
        
        # Base multiplier is 0.7
        multiplier = 0.7
        
        # Boost if open to work
        if open_to_work:
            multiplier += 0.15
            
        # Add response rate contribution
        multiplier += resp_rate * 0.15
        
        # Boost for active GitHub (github_score > 30)
        if github_score > 30:
            multiplier += 0.05
            
        # Boost for short notice period (< 45 days)
        if notice_period <= 45:
            multiplier += 0.05
        # Penalty for extremely long notice period (> 90 days)
        elif notice_period >= 90:
            multiplier -= 0.10
            
        # Return final score (bound between 0.0 and 1.0)
        final_score = fit_score * multiplier
        return min(max(final_score, 0.0), 1.0)
