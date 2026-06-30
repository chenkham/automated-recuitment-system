from datetime import datetime

# Lists of service/consulting companies to identify candidates with ONLY service background
SERVICES_COMPANIES = ["tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"]

# Non-technical current titles to filter out keyword-stuffed profiles
NON_TECH_TITLES = ["operations manager", "marketing manager", "graphic designer", "accountant", "hr manager", "customer support"]

def is_honeypot(candidate) -> bool:
    """
    Checks if a candidate is a honeypot (an impossible profile designed to trap naive systems).
    Returns True if an anomaly is detected, False otherwise.
    """
    skills = candidate.get("skills", [])
    history = candidate.get("career_history", [])
    education = candidate.get("education", [])
    
    # Check 1: Expert or Advanced skills with 0 months of experience
    expert_zero_months = 0
    for s in skills:
        if s.get("proficiency") in ["expert", "advanced"] and s.get("duration_months", 0) == 0:
            expert_zero_months += 1
    # If 3 or more skills show this anomaly, classify as honeypot
    if expert_zero_months >= 3:
        return True

    # Check 2: Duration of a job exceeds the elapsed time since its start date
    # Reference date is mid-2026 (local time is June 2026, active dates in dataset end in May 2026)
    ref_date = datetime(2026, 6, 30)
    for job in history:
        start_str = job.get("start_date")
        duration = job.get("duration_months", 0)
        if start_str:
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                # Calculate maximum possible months between start date and reference date
                max_months = (ref_date.year - start_dt.year) * 12 + (ref_date.month - start_dt.month) + 2
                if duration > max_months:
                    return True
            except ValueError:
                pass

    # Check 3: Education start year is after they started working in their career history
    if education and history:
        earliest_job_year = 9999
        for job in history:
            start_str = job.get("start_date")
            if start_str:
                try:
                    job_year = int(start_str.split("-")[0])
                    if job_year < earliest_job_year:
                        earliest_job_year = job_year
                except (ValueError, IndexError):
                    pass
        
        for edu in education:
            start_year = edu.get("start_year")
            # If they started a senior job way before starting college
            if start_year and earliest_job_year < start_year - 5:
                return True

    return False


def is_excluded_by_role(candidate) -> bool:
    """
    Applies strict exclusions based on job description constraints:
    1. Excludes candidates with non-technical current titles.
    2. Excludes candidates who have worked ONLY at consulting/services firms in their career.
    """
    p = candidate.get("profile", {})
    history = candidate.get("career_history", [])
    
    # 1. Check current title
    current_title = p.get("current_title", "").lower()
    if any(title in current_title for title in NON_TECH_TITLES):
        return True
        
    # 2. Check consulting/services company history
    if not history:
        return True
        
    worked_companies = [job.get("company", "").lower() for job in history]
    
    # Check if they have only worked at services companies
    worked_only_services = True
    for company in worked_companies:
        is_service = any(service in company for service in SERVICES_COMPANIES)
        if not is_service:
            worked_only_services = False
            break
            
    if worked_only_services:
        return True
        
    return False


def should_filter_out(candidate) -> bool:
    """
    Combines all exclusion checks to decide if a candidate should be dropped immediately.
    """
    return is_honeypot(candidate) or is_excluded_by_role(candidate)
