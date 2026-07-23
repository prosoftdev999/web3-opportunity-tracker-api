from datetime import datetime, timedelta, timezone

from app.services.scoring import calculate_opportunity_score


def test_inactive_opportunity_score_is_zero() -> None:
    score = calculate_opportunity_score(
        reward_amount=1000,
        required_skills=["python"],
        difficulty="beginner",
        deadline=None,
        is_active=False,
    )

    assert score == 0


def test_high_value_opportunity_gets_strong_score() -> None:
    # Use 31 days instead of 30 to avoid timing differences during execution.
    score = calculate_opportunity_score(
        reward_amount=10_000,
        required_skills=["python", "fastapi", "docker"],
        difficulty="beginner",
        deadline=datetime.now(timezone.utc) + timedelta(days=31),
        is_active=True,
    )

    assert score == 100


def test_expired_opportunity_score_is_zero() -> None:
    score = calculate_opportunity_score(
        reward_amount=500,
        required_skills=["python"],
        difficulty="intermediate",
        deadline=datetime.now(timezone.utc) - timedelta(days=1),
        is_active=True,
    )

    assert score == 0