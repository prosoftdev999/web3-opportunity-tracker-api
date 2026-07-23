from datetime import datetime, timezone


def calculate_opportunity_score(
    *,
    reward_amount: float | None,
    required_skills: list[str],
    difficulty: str,
    deadline: datetime | None,
    is_active: bool,
) -> int:
    """
    Calculate an opportunity quality score between 0 and 100.
    """

    if not is_active:
        return 0

    score = 20

    if reward_amount is not None:
        if reward_amount >= 10_000:
            score += 35
        elif reward_amount >= 5_000:
            score += 30
        elif reward_amount >= 1_000:
            score += 25
        elif reward_amount >= 500:
            score += 20
        elif reward_amount > 0:
            score += 10

    skill_count = len(required_skills)

    if 1 <= skill_count <= 5:
        score += 15
    elif skill_count > 5:
        score += 10

    difficulty_scores = {
        "beginner": 15,
        "intermediate": 10,
        "advanced": 5,
    }

    score += difficulty_scores.get(difficulty, 5)

    if deadline is None:
        score += 5
    else:
        now = datetime.now(timezone.utc)

        normalized_deadline = deadline
        if deadline.tzinfo is None:
            normalized_deadline = deadline.replace(tzinfo=timezone.utc)

        days_remaining = (normalized_deadline - now).days

        if days_remaining < 0:
            return 0

        if days_remaining >= 30:
            score += 15
        elif days_remaining >= 14:
            score += 12
        elif days_remaining >= 7:
            score += 8
        else:
            score += 3

    return min(score, 100)