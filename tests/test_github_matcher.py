from app.services.github_matcher import (
    calculate_skill_match,
    normalize_skill,
)


def test_normalize_skill_aliases() -> None:
    assert normalize_skill("Dockerfile") == "docker"
    assert normalize_skill("Shell") == "bash"
    assert normalize_skill("Python") == "python"


def test_calculate_skill_match() -> None:
    score, matched, missing, recommendation = calculate_skill_match(
        required_skills=["python", "fastapi", "react", "web3"],
        profile_languages=["python", "typescript"],
        profile_topics=["fastapi", "web3"],
    )

    assert score == 75
    assert matched == ["fastapi", "python", "web3"]
    assert missing == ["react"]
    assert recommendation == "Moderate match"


def test_empty_required_skills_is_full_match() -> None:
    score, matched, missing, recommendation = calculate_skill_match(
        required_skills=[],
        profile_languages=["python"],
        profile_topics=["fastapi"],
    )

    assert score == 100
    assert matched == []
    assert missing == []
    assert recommendation == "Strong match"
