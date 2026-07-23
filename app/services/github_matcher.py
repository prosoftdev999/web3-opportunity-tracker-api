from __future__ import annotations

from collections import Counter
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


GITHUB_API_URL = "https://api.github.com"


def normalize_skill(value: str) -> str:
    aliases = {
        "javascript": "javascript",
        "typescript": "typescript",
        "python": "python",
        "dockerfile": "docker",
        "shell": "bash",
        "solidity": "solidity",
        "rust": "rust",
        "go": "go",
        "html": "html",
        "css": "css",
    }

    normalized = value.strip().lower()
    return aliases.get(normalized, normalized)


class GitHubService:
    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "web3-opportunity-tracker-api",
        }

        if settings.github_token:
            headers["Authorization"] = (
                f"Bearer {settings.github_token}"
            )

        return headers

    async def analyze_user(self, username: str) -> dict[str, Any]:
        timeout = httpx.Timeout(30.0, connect=10.0)

        async with httpx.AsyncClient(
            base_url=GITHUB_API_URL,
            headers=self._headers(),
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            user_response = await client.get(f"/users/{username}")

            if user_response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="GitHub user not found.",
                )

            if user_response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "GitHub API rate limit exceeded or the "
                        "configured token is not permitted."
                    ),
                )

            user_response.raise_for_status()
            user = user_response.json()

            repos_response = await client.get(
                f"/users/{username}/repos",
                params={
                    "per_page": 100,
                    "sort": "updated",
                    "direction": "desc",
                    "type": "owner",
                },
            )
            repos_response.raise_for_status()
            repos = repos_response.json()

        language_counter: Counter[str] = Counter()
        topic_counter: Counter[str] = Counter()
        repository_items: list[dict[str, Any]] = []

        total_stars = 0
        total_forks = 0

        for repo in repos:
            if repo.get("fork"):
                continue

            language = repo.get("language")
            topics = repo.get("topics") or []
            stars = int(repo.get("stargazers_count") or 0)
            forks = int(repo.get("forks_count") or 0)

            total_stars += stars
            total_forks += forks

            if language:
                language_counter[normalize_skill(language)] += 1

            for topic in topics:
                topic_counter[normalize_skill(topic)] += 1

            repository_items.append(
                {
                    "name": repo["name"],
                    "url": repo["html_url"],
                    "description": repo.get("description"),
                    "primary_language": language,
                    "topics": topics,
                    "stars": stars,
                    "forks": forks,
                }
            )

        languages = [
            item
            for item, _ in language_counter.most_common()
        ]
        topics = [
            item
            for item, _ in topic_counter.most_common(30)
        ]

        experience_score = min(
            100,
            len(repository_items) * 3
            + len(languages) * 5
            + min(total_stars, 25)
            + min(total_forks, 15),
        )

        return {
            "username": user["login"],
            "profile_url": user["html_url"],
            "public_repositories": len(repository_items),
            "followers": int(user.get("followers") or 0),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "languages": languages,
            "topics": topics,
            "repositories": repository_items,
            "experience_score": experience_score,
        }


def calculate_skill_match(
    required_skills: list[str],
    profile_languages: list[str],
    profile_topics: list[str],
) -> tuple[int, list[str], list[str], str]:
    required = {
        normalize_skill(skill)
        for skill in required_skills
        if skill.strip()
    }

    available = {
        normalize_skill(skill)
        for skill in profile_languages + profile_topics
        if skill.strip()
    }

    matched = sorted(required & available)
    missing = sorted(required - available)

    if not required:
        score = 100
    else:
        score = round(len(matched) / len(required) * 100)

    if score >= 80:
        recommendation = "Strong match"
    elif score >= 50:
        recommendation = "Moderate match"
    else:
        recommendation = "Low match"

    return score, matched, missing, recommendation


github_service = GitHubService()