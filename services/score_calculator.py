def calculate_score(skill_score, experience_score=0, education_score=0):
    """
    Input: individual scores
    Output: final combined score (simple average for now)
    """
    final_score = (skill_score + experience_score + education_score) / 3
    return final_score