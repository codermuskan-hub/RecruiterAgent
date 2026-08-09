import re
from typing import Dict, List, Tuple

# Comprehensive Indian Institution Lists
TIER_1_PATTERNS = [
    # IITs
    r"\biit\b", r"\bindian institute of technology\b", r"\biit\s+(bombay|delhi|madras|kanpur|kharagpur|roorkee|guwahati|hyderabad|bhu|indore|varanasi|ism|dhanbad|gandhinagar|ropar|patna|mandi|jodhpur)\b",
    # BITS
    r"\bbits\b", r"\bbirla institute of technology and science\b", r"\bbits\s+(pilani|goa|hyderabad)\b",
    # Top IIITs
    r"\biiit\s+(hyderabad|bangalore|delhi|allahabad)\b", r"\bindraprastha institute of information technology\b",
    # Top NITs
    r"\bnit\s+(trichy|tiruchirappalli|surathkal|warangal|rourkela|calicut|nagpur|jaipur|allahabad|surat|bhopal|kurukshetra)\b",
    r"\bnational institute of technology\s+(trichy|surathkal|warangal|rourkela|calicut)\b",
    # Top Delhi / State Premier Tech
    r"\bdtu\b", r"\bdelhi technological university\b", r"\bdce\b",
    r"\bnsut\b", r"\bnetaji subhas university of technology\b", r"\bnsit\b",
    r"\bjadavpur university\b", r"\banna university\b", r"\bcollege of engineering guindy\b"
]

TIER_2_PATTERNS = [
    # Top Premier Private Universities
    r"\bvit\b", r"\bvellore institute of technology\b",
    r"\bmanipal\b", r"\bmanipal institute of technology\b", r"\bmit\s+manipal\b",
    r"\bthapar\b", r"\bthapar institute of engineering\b",
    r"\brvce\b", r"\br\.?v\.?\s+college of engineering\b",
    r"\bbmsce\b", r"\bbms college of engineering\b",
    r"\bpes university\b", r"\bpesit\b",
    r"\bms ramaiah\b", r"\bmsrit\b",
    r"\bpsg tech\b", r"\bpsg college of technology\b",
    r"\bssn college of engineering\b",
    r"\bcoep\b", r"\bcollege of engineering pune\b",
    r"\bvjti\b", r"\bveermata jijabai\b",
    r"\bda-iict\b", r"\bdhirubhai ambani institute\b",
    r"\bsrm university\b", r"\bsrmist\b",
    r"\bkiit\b", r"\bkalinga institute\b",
    r"\bamity university\b",
    # Other NITs and IIITs
    r"\bnit\b", r"\bnational institute of technology\b",
    r"\biiit\b", r"\bindian institute of information technology\b"
]

INDIAN_TECH_HUBS = {
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "blr": "Bengaluru",
    "whitefield": "Bengaluru",
    "electronic city": "Bengaluru",
    "gurugram": "Delhi-NCR",
    "gurgaon": "Delhi-NCR",
    "noida": "Delhi-NCR",
    "greater noida": "Delhi-NCR",
    "delhi": "Delhi-NCR",
    "new delhi": "Delhi-NCR",
    "faridabad": "Delhi-NCR",
    "ghaziabad": "Delhi-NCR",
    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",
    "cyberabad": "Hyderabad",
    "hitec city": "Hyderabad",
    "pune": "Pune",
    "hinjewadi": "Pune",
    "mumbai": "Mumbai",
    "navi mumbai": "Mumbai",
    "thane": "Mumbai",
    "chennai": "Chennai",
    "madras": "Chennai",
    "kolkata": "Kolkata",
    "ahmedabad": "Ahmedabad"
}


def classify_indian_college_tier(institution_name: str) -> Tuple[str, str]:
    """
    Identifies if an educational institution is Tier-1, Tier-2, or Tier-3 in the Indian tech ecosystem.
    Returns:
        (tier_label: str, normalized_name: str)
    """
    if not institution_name:
        return "Tier-3", "Regional / Affiliated Institution"

    name_lower = institution_name.lower().strip()

    # Check Tier-1
    for pattern in TIER_1_PATTERNS:
        if re.search(pattern, name_lower):
            return "Tier-1", institution_name

    # Check Tier-2
    for pattern in TIER_2_PATTERNS:
        if re.search(pattern, name_lower):
            return "Tier-2", institution_name

    return "Tier-3", institution_name


def normalize_indian_degree(degree_str: str) -> str:
    """Normalizes Indian technical degrees (B.Tech, B.E., M.Tech, MCA, etc.)."""
    if not degree_str:
        return "B.Tech"

    d_lower = degree_str.lower()
    if "b.tech" in d_lower or "bachelor of technology" in d_lower or "btech" in d_lower:
        return "B.Tech"
    elif "b.e" in d_lower or "bachelor of engineering" in d_lower:
        return "B.E."
    elif "m.tech" in d_lower or "master of technology" in d_lower or "mtech" in d_lower:
        return "M.Tech"
    elif "mca" in d_lower or "master of computer applications" in d_lower:
        return "MCA"
    elif "bca" in d_lower or "bachelor of computer applications" in d_lower:
        return "BCA"
    elif "m.s" in d_lower or "master of science" in d_lower:
        return "M.S. / M.Sc."
    elif "b.sc" in d_lower or "bachelor of science" in d_lower:
        return "B.Sc (CS/IT)"

    return degree_str.strip()


def parse_notice_period(text: str) -> int:
    """
    Extracts notice period in days from candidate profile or text.
    Standard Indian IT notice periods: 0 (Immediate), 15, 30, 60, 90 days.
    """
    if not text:
        return 30

    t_lower = text.lower()

    if any(k in t_lower for k in ["immediate", "immediately", "serving notice", "0 days", "buyout possible"]):
        return 0
    elif any(k in t_lower for k in ["15 days", "2 weeks"]):
        return 15
    elif any(k in t_lower for k in ["30 days", "1 month", "one month"]):
        return 30
    elif any(k in t_lower for k in ["45 days"]):
        return 45
    elif any(k in t_lower for k in ["60 days", "2 months", "two months"]):
        return 60
    elif any(k in t_lower for k in ["90 days", "3 months", "three months"]):
        return 90

    # Regex search for digits followed by days/months
    match_days = re.search(r"(\d+)\s*(?:days?|day)\s*notice", t_lower)
    if match_days:
        return int(match_days.group(1))

    match_months = re.search(r"(\d+)\s*(?:months?|month)\s*notice", t_lower)
    if match_months:
        return int(match_months.group(1)) * 30

    return 30  # Default Indian standard


def parse_ctc_lpa(text: str) -> Tuple[float, float]:
    """
    Parses Current and Expected CTC in LPA (Lakhs Per Annum).
    Returns (current_lpa, expected_lpa).
    """
    if not text:
        return (0.0, 0.0)

    t_lower = text.lower()
    curr_lpa = 0.0
    exp_lpa = 0.0

    # Pattern like: Current CTC: 12 LPA, Expected: 18 LPA
    curr_match = re.search(r"(?:current|cctc|current ctc)[\s:\-₹rs\.]*([\d\.]+)\s*(?:lpa|lakhs?|lac|l)?", t_lower)
    if curr_match:
        try:
            curr_lpa = float(curr_match.group(1))
        except ValueError:
            pass

    exp_match = re.search(r"(?:expected|ectc|expected ctc)[\s:\-₹rs\.]*([\d\.]+)\s*(?:lpa|lakhs?|lac|l)?", t_lower)
    if exp_match:
        try:
            exp_lpa = float(exp_match.group(1))
        except ValueError:
            pass

    # Generic search for numbers followed by LPA if not labeled
    if curr_lpa == 0.0 and exp_lpa == 0.0:
        lpa_matches = re.findall(r"([\d\.]+)\s*(?:lpa|lakhs?|lac)", t_lower)
        if len(lpa_matches) >= 2:
            try:
                curr_lpa = float(lpa_matches[0])
                exp_lpa = float(lpa_matches[1])
            except ValueError:
                pass
        elif len(lpa_matches) == 1:
            try:
                curr_lpa = float(lpa_matches[0])
                exp_lpa = round(curr_lpa * 1.3, 1)  # Est. 30% hike standard in Indian tech
            except ValueError:
                pass

    return (curr_lpa, exp_lpa)


def normalize_indian_location(loc_str: str) -> str:
    """Normalizes location into primary Indian Tech Hub regions."""
    if not loc_str:
        return "Delhi-NCR / Remote"

    l_lower = loc_str.lower().strip()

    for token, hub in INDIAN_TECH_HUBS.items():
        if token in l_lower:
            return hub

    return loc_str.strip().title()
