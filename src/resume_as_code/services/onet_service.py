"""O*NET Web Services API v2.0 client.

Provides skill and occupation lookup with caching and error handling.
Gracefully degrades when API key unavailable or API errors occur.

API v2.0 uses X-API-Key header authentication (not HTTP Basic Auth).
Reference: https://services.onetcenter.org/reference/
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import httpx

if TYPE_CHECKING:
    from resume_as_code.models.config import ONetConfig

logger = logging.getLogger(__name__)

# O*NET API v2.0 base URL (November 2025)
BASE_URL = "https://api-v2.onetcenter.org"


@dataclass
class ONetSkill:
    """Skill data from O*NET API v2.0.

    Attributes:
        id: Element ID (e.g., "2.A.2.b").
        name: Skill name (e.g., "Programming").
        description: Skill description.
        importance: Importance rating (direct value in v2.0).
        level: Level rating (direct value in v2.0).
    """

    id: str
    name: str
    description: str | None = None
    importance: float | None = None
    level: float | None = None


@dataclass
class ONetOccupation:
    """Occupation data from O*NET search.

    Attributes:
        code: SOC code (e.g., "15-1252.00").
        title: Occupation title.
        score: Relevance score (renamed from relevance_score in v2.0).
    """

    code: str
    title: str
    score: float | None = None


class ONetService:
    """O*NET Web Services API v2.0 client.

    Provides skill and occupation lookup with caching and error handling.
    Gracefully degrades when API key unavailable or API errors occur.

    API v2.0 uses X-API-Key header authentication (not HTTP Basic Auth).

    Can be used as a context manager for automatic resource cleanup:

        with ONetService(config) as service:
            results = service.search_occupations("python")

    """

    def __init__(self, config: ONetConfig) -> None:
        """Initialize O*NET service.

        Args:
            config: O*NET configuration with API key.
        """
        self.config = config
        self._client: httpx.Client | None = None
        self._cache_dir = Path.home() / ".cache" / "resume-as-code" / "onet"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def __enter__(self) -> ONetService:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager and close HTTP client."""
        self.close()

    def close(self) -> None:
        """Close HTTP client and release resources.

        Safe to call multiple times.
        """
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize HTTP client with X-API-Key auth."""
        if self._client is None:
            if not self.config.is_configured:
                raise RuntimeError("O*NET API key not configured")

            # api_key is guaranteed to be str when is_configured is True
            api_key = cast(str, self.config.api_key)
            self._client = httpx.Client(
                base_url=BASE_URL,
                headers={"X-API-Key": api_key},  # v2.0 auth
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    def search_occupations(self, keyword: str) -> list[ONetOccupation]:
        """Search O*NET for occupations matching keyword.

        Args:
            keyword: Search term (skill name, job title, etc.)

        Returns:
            List of matching occupations, empty on error.
        """
        if not self.config.is_configured:
            logger.debug("O*NET not configured, skipping search")
            return []

        cache_key = self._cache_key(f"search:{keyword}")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return [
                ONetOccupation(
                    code=str(occ["code"]),
                    title=str(occ["title"]),
                    score=float(occ["score"]) if occ.get("score") is not None else None,
                )
                for occ in cached
            ]

        try:
            response = self._request_with_backoff(
                "/online/search",
                params={"keyword": keyword, "start": 1, "end": 10},
            )
            if response is None:
                return []

            data = response.json()
            occupations = [
                ONetOccupation(
                    code=occ["code"],
                    title=occ["title"],
                    score=occ.get("score"),  # v2.0: renamed from relevance_score
                )
                for occ in data.get("occupation", [])
            ]

            self._set_cached(cache_key, [vars(o) for o in occupations])
            return occupations

        except Exception as e:
            logger.warning(f"O*NET search failed for '{keyword}': {e}")
            return []

    def get_occupation_skills(self, soc_code: str) -> list[ONetSkill]:
        """Get skills for a specific occupation.

        Args:
            soc_code: O*NET-SOC code (e.g., "15-1252.00")

        Returns:
            List of skills for the occupation, empty on error.
        """
        if not self.config.is_configured:
            return []

        cache_key = self._cache_key(f"skills:{soc_code}")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return [
                ONetSkill(
                    id=str(skill["id"]),
                    name=str(skill["name"]),
                    description=str(skill["description"])
                    if skill.get("description") is not None
                    else None,
                    importance=float(skill["importance"])
                    if skill.get("importance") is not None
                    else None,
                    level=float(skill["level"]) if skill.get("level") is not None else None,
                )
                for skill in cached
            ]

        try:
            # v2.0 endpoint with skills=true query param
            response = self._request_with_backoff(
                f"/online/occupations/{soc_code}",
                params={"skills": "true"},
            )
            if response is None:
                return []

            data = response.json()
            # v2.0: skills in "element" array with flattened importance/level
            skills = [
                ONetSkill(
                    id=skill["id"],
                    name=skill["name"],
                    description=skill.get("description"),
                    importance=skill.get("importance"),  # v2.0: direct value
                    level=skill.get("level"),  # v2.0: direct value
                )
                for skill in data.get("element", [])
            ]

            self._set_cached(cache_key, [vars(s) for s in skills])
            return skills

        except Exception as e:
            logger.warning(f"O*NET skills lookup failed for '{soc_code}': {e}")
            return []

    def _request_with_backoff(
        self,
        path: str,
        params: dict[str, str | int] | None = None,
        max_retries: int = 3,
    ) -> httpx.Response | None:
        """Make request with exponential backoff for rate limits.

        O*NET docs: "delay at least 200 milliseconds before retrying" on 429.

        Args:
            path: API endpoint path.
            params: Query parameters.
            max_retries: Maximum retry attempts.

        Returns:
            Response object or None on failure.
        """
        base_delay = self.config.retry_delay_ms / 1000.0  # Convert to seconds

        for attempt in range(max_retries):
            try:
                response = self.client.get(path, params=params)

                if response.status_code == 200:
                    return response

                if response.status_code == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        # O*NET minimum 200ms, then exponential: 0.2s, 0.4s, 0.8s
                        wait = base_delay * (2**attempt)
                        logger.warning(f"O*NET rate limited, waiting {wait:.1f}s")
                        time.sleep(wait)
                    continue

                if response.status_code >= 500:  # Server error
                    if attempt < max_retries - 1:
                        wait = base_delay * (2**attempt)
                        logger.warning(
                            f"O*NET server error {response.status_code}, waiting {wait:.1f}s"
                        )
                        time.sleep(wait)
                    continue

                # Client error (4xx except 429) - don't retry
                logger.warning(f"O*NET request failed: {response.status_code}")
                return None

            except httpx.TimeoutException:
                logger.warning(f"O*NET request timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2**attempt))

        return None

    def _cache_key(self, query: str) -> str:
        """Generate cache key from query.

        Uses first 32 chars of SHA256 (128 bits) for collision resistance.
        """
        return hashlib.sha256(query.encode()).hexdigest()[:32]

    def _get_cached(self, key: str) -> list[dict[str, Any]] | None:
        """Get cached response if valid."""
        cache_file = self._cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            data: dict[str, Any] = json.loads(cache_file.read_text())
            if time.time() - data["timestamp"] < self.config.cache_ttl:
                logger.debug(f"O*NET cache hit: {key}")
                return cast(list[dict[str, Any]], data["response"])
            # Cache expired
            cache_file.unlink()
        except Exception:
            pass
        return None

    def _set_cached(self, key: str, response: list[dict[str, Any]]) -> None:
        """Cache response."""
        cache_file = self._cache_dir / f"{key}.json"
        try:
            cache_file.write_text(json.dumps({"timestamp": time.time(), "response": response}))
            logger.debug(f"O*NET cache set: {key}")
        except Exception as e:
            logger.warning(f"Failed to cache O*NET response: {e}")

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        cache_files = list(self._cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        return {
            "entries": len(cache_files),
            "size_bytes": total_size,
        }
