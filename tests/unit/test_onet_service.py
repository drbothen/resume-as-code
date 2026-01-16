"""Tests for O*NET API v2.0 service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from resume_as_code.models.config import ONetConfig
from resume_as_code.services.onet_service import (
    BASE_URL,
    ONetOccupation,
    ONetService,
    ONetSkill,
)


@pytest.fixture
def mock_config() -> ONetConfig:
    """Create mock O*NET config with API key."""
    return ONetConfig(
        enabled=True,
        api_key="test-api-key",
    )


@pytest.fixture
def mock_config_no_key() -> ONetConfig:
    """Create mock O*NET config without API key."""
    return ONetConfig(enabled=True, api_key=None)


@pytest.fixture
def mock_config_disabled() -> ONetConfig:
    """Create disabled O*NET config."""
    return ONetConfig(enabled=False, api_key="test-key")


@pytest.fixture
def service(mock_config: ONetConfig, tmp_path: Path) -> ONetService:
    """Create service with mocked config and temp cache dir."""
    svc = ONetService(mock_config)
    svc._cache_dir = tmp_path / "onet_cache"
    svc._cache_dir.mkdir(parents=True, exist_ok=True)
    return svc


class TestONetServiceInit:
    """Test ONetService initialization."""

    def test_base_url_is_v2(self) -> None:
        """BASE_URL should be the v2.0 API endpoint."""
        assert BASE_URL == "https://api-v2.onetcenter.org"

    def test_cache_dir_created(self, mock_config: ONetConfig, tmp_path: Path) -> None:
        """ONetService should create cache directory on init."""
        with patch.object(Path, "home", return_value=tmp_path):
            service = ONetService(mock_config)
            assert service._cache_dir.exists()


class TestONetOccupationDataclass:
    """Test ONetOccupation dataclass."""

    def test_occupation_fields(self) -> None:
        """ONetOccupation should have code, title, and optional score."""
        occ = ONetOccupation(code="15-1252.00", title="Software Developers", score=97.5)
        assert occ.code == "15-1252.00"
        assert occ.title == "Software Developers"
        assert occ.score == 97.5

    def test_occupation_score_optional(self) -> None:
        """ONetOccupation score should be optional."""
        occ = ONetOccupation(code="15-1252.00", title="Software Developers")
        assert occ.score is None


class TestONetSkillDataclass:
    """Test ONetSkill dataclass."""

    def test_skill_fields(self) -> None:
        """ONetSkill should have id, name, and optional description/importance/level."""
        skill = ONetSkill(
            id="2.A.2.b",
            name="Programming",
            description="Writing computer programs",
            importance=4.75,
            level=5.13,
        )
        assert skill.id == "2.A.2.b"
        assert skill.name == "Programming"
        assert skill.description == "Writing computer programs"
        assert skill.importance == 4.75
        assert skill.level == 5.13

    def test_skill_optional_fields(self) -> None:
        """ONetSkill optional fields should default to None."""
        skill = ONetSkill(id="2.A.2.b", name="Programming")
        assert skill.description is None
        assert skill.importance is None
        assert skill.level is None


class TestSearchOccupations:
    """Test search_occupations method."""

    @respx.mock
    def test_search_returns_results(self, service: ONetService) -> None:
        """Search returns list of occupations with v2.0 response format."""
        respx.get(f"{BASE_URL}/online/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "occupation": [
                        {"code": "15-1252.00", "title": "Software Developers", "score": 97}
                    ]
                },
            )
        )

        results = service.search_occupations("python")

        assert len(results) == 1
        assert results[0].code == "15-1252.00"
        assert results[0].title == "Software Developers"
        assert results[0].score == 97

    @respx.mock
    def test_search_sends_api_key_header(self, service: ONetService) -> None:
        """Search should send X-API-Key header (v2.0 auth)."""
        route = respx.get(f"{BASE_URL}/online/search").mock(
            return_value=httpx.Response(200, json={"occupation": []})
        )

        service.search_occupations("python")

        assert route.called
        request = route.calls[0].request
        assert request.headers.get("X-API-Key") == "test-api-key"

    def test_search_graceful_on_no_api_key(
        self, mock_config_no_key: ONetConfig, tmp_path: Path
    ) -> None:
        """Search returns empty list when API key missing."""
        service = ONetService(mock_config_no_key)
        service._cache_dir = tmp_path / "cache"
        service._cache_dir.mkdir(parents=True, exist_ok=True)

        results = service.search_occupations("python")

        assert results == []

    def test_search_graceful_on_disabled(
        self, mock_config_disabled: ONetConfig, tmp_path: Path
    ) -> None:
        """Search returns empty list when disabled."""
        service = ONetService(mock_config_disabled)
        service._cache_dir = tmp_path / "cache"
        service._cache_dir.mkdir(parents=True, exist_ok=True)

        results = service.search_occupations("python")

        assert results == []

    @respx.mock
    def test_search_handles_empty_results(self, service: ONetService) -> None:
        """Search handles empty occupation list."""
        respx.get(f"{BASE_URL}/online/search").mock(
            return_value=httpx.Response(200, json={"occupation": []})
        )

        results = service.search_occupations("nonexistent-skill-xyz")

        assert results == []

    @respx.mock
    def test_search_handles_api_error(self, service: ONetService) -> None:
        """Search returns empty list on API error."""
        respx.get(f"{BASE_URL}/online/search").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        results = service.search_occupations("python")

        assert results == []


class TestGetOccupationSkills:
    """Test get_occupation_skills method."""

    @respx.mock
    def test_get_skills_returns_results(self, service: ONetService) -> None:
        """Get skills for occupation with v2.0 flattened response."""
        respx.get(f"{BASE_URL}/online/occupations/15-1252.00").mock(
            return_value=httpx.Response(
                200,
                json={
                    "element": [
                        {
                            "id": "2.A.2.b",
                            "name": "Programming",
                            "description": "Writing computer programs",
                            "importance": 4.75,
                            "level": 5.13,
                        }
                    ]
                },
            )
        )

        skills = service.get_occupation_skills("15-1252.00")

        assert len(skills) == 1
        assert skills[0].id == "2.A.2.b"
        assert skills[0].name == "Programming"
        assert skills[0].importance == 4.75
        assert skills[0].level == 5.13

    @respx.mock
    def test_get_skills_sends_skills_param(self, service: ONetService) -> None:
        """Get skills should send skills=true query param."""
        route = respx.get(f"{BASE_URL}/online/occupations/15-1252.00").mock(
            return_value=httpx.Response(200, json={"element": []})
        )

        service.get_occupation_skills("15-1252.00")

        assert route.called
        request = route.calls[0].request
        assert "skills=true" in str(request.url)

    def test_get_skills_graceful_on_no_api_key(
        self, mock_config_no_key: ONetConfig, tmp_path: Path
    ) -> None:
        """Get skills returns empty list when API key missing."""
        service = ONetService(mock_config_no_key)
        service._cache_dir = tmp_path / "cache"
        service._cache_dir.mkdir(parents=True, exist_ok=True)

        skills = service.get_occupation_skills("15-1252.00")

        assert skills == []


class TestCaching:
    """Test caching functionality."""

    @respx.mock
    def test_cache_hit_skips_api_call(self, service: ONetService) -> None:
        """Cached response doesn't make API call."""
        # Pre-populate cache
        service._set_cached(
            service._cache_key("search:python"),
            [{"code": "15-1252.00", "title": "Cached Result", "score": None}],
        )

        # Mock should NOT be called
        route = respx.get(f"{BASE_URL}/online/search").mock(
            return_value=httpx.Response(200, json={"occupation": []})
        )

        results = service.search_occupations("python")

        assert not route.called
        assert results[0].title == "Cached Result"

    def test_cache_expires_after_ttl(self, mock_config: ONetConfig, tmp_path: Path) -> None:
        """Cached entries expire after cache_ttl seconds."""
        # Create config with very short TTL
        short_ttl_config = ONetConfig(
            enabled=True,
            api_key="test-key",
            cache_ttl=3600,  # 1 hour
        )
        service = ONetService(short_ttl_config)
        service._cache_dir = tmp_path / "cache"
        service._cache_dir.mkdir(parents=True, exist_ok=True)

        # Set cache entry with old timestamp
        import json
        import time

        cache_key = service._cache_key("search:expired")
        cache_file = service._cache_dir / f"{cache_key}.json"

        # Write cache entry that expired 2 hours ago
        old_timestamp = time.time() - 7200  # 2 hours ago
        cache_file.write_text(
            json.dumps(
                {
                    "timestamp": old_timestamp,
                    "response": [{"code": "15-1252.00", "title": "Expired", "score": None}],
                }
            )
        )

        # Cache should be considered expired
        result = service._get_cached(cache_key)
        assert result is None

        # File should be deleted
        assert not cache_file.exists()

    @respx.mock
    def test_cache_miss_makes_api_call(self, service: ONetService) -> None:
        """Cache miss triggers API call."""
        route = respx.get(f"{BASE_URL}/online/search").mock(
            return_value=httpx.Response(
                200,
                json={"occupation": [{"code": "15-1252.00", "title": "API Result", "score": 90}]},
            )
        )

        results = service.search_occupations("uncached-query")

        assert route.called
        assert results[0].title == "API Result"

    @respx.mock
    def test_successful_response_is_cached(self, service: ONetService) -> None:
        """Successful API response is cached."""
        respx.get(f"{BASE_URL}/online/search").mock(
            return_value=httpx.Response(
                200,
                json={"occupation": [{"code": "15-1252.00", "title": "New Result", "score": 95}]},
            )
        )

        service.search_occupations("new-query")

        # Verify cache was set
        cache_key = service._cache_key("search:new-query")
        cached = service._get_cached(cache_key)
        assert cached is not None
        assert cached[0]["title"] == "New Result"

    def test_get_cache_stats(self, service: ONetService) -> None:
        """get_cache_stats returns entry count and size."""
        # Add some cache entries
        service._set_cached("key1", [{"test": "data1"}])
        service._set_cached("key2", [{"test": "data2"}])

        stats = service.get_cache_stats()

        assert stats["entries"] == 2
        assert stats["size_bytes"] > 0


class TestErrorHandling:
    """Test error handling and backoff."""

    @respx.mock
    def test_backoff_on_rate_limit(self, service: ONetService) -> None:
        """Rate limit (429) triggers exponential backoff."""
        respx.get(f"{BASE_URL}/test").mock(return_value=httpx.Response(429))

        with patch("time.sleep") as mock_sleep:
            result = service._request_with_backoff("/test", max_retries=3)

            assert result is None
            # Should sleep with exponential backoff: 0.2s, 0.4s (2 sleeps for 3 attempts)
            assert mock_sleep.call_count == 2
            # First sleep: 0.2s (200ms base)
            mock_sleep.assert_any_call(pytest.approx(0.2, rel=0.01))

    @respx.mock
    def test_backoff_on_server_error(self, service: ONetService) -> None:
        """Server error (5xx) triggers exponential backoff."""
        respx.get(f"{BASE_URL}/test").mock(return_value=httpx.Response(503))

        with patch("time.sleep") as mock_sleep:
            result = service._request_with_backoff("/test", max_retries=2)

            assert result is None
            assert mock_sleep.call_count == 1

    @respx.mock
    def test_no_retry_on_client_error(self, service: ONetService) -> None:
        """Client error (4xx except 429) does not retry."""
        respx.get(f"{BASE_URL}/test").mock(return_value=httpx.Response(404))

        with patch("time.sleep") as mock_sleep:
            result = service._request_with_backoff("/test", max_retries=3)

            assert result is None
            assert mock_sleep.call_count == 0

    @respx.mock
    def test_timeout_handling(self, service: ONetService) -> None:
        """Timeout triggers retry with backoff."""
        respx.get(f"{BASE_URL}/test").mock(side_effect=httpx.TimeoutException("timeout"))

        with patch("time.sleep") as mock_sleep:
            result = service._request_with_backoff("/test", max_retries=2)

            assert result is None
            # Should sleep once between 2 attempts
            assert mock_sleep.call_count == 1

    @respx.mock
    def test_success_after_retry(self, service: ONetService) -> None:
        """Successful response after retry."""
        route = respx.get(f"{BASE_URL}/test")
        # First call returns 429, second succeeds
        route.side_effect = [
            httpx.Response(429),
            httpx.Response(200, json={"data": "success"}),
        ]

        with patch("time.sleep"):
            result = service._request_with_backoff("/test", max_retries=3)

            assert result is not None
            assert result.json() == {"data": "success"}


class TestClientInitialization:
    """Test HTTP client initialization."""

    def test_client_raises_without_api_key(
        self, mock_config_no_key: ONetConfig, tmp_path: Path
    ) -> None:
        """Accessing client without API key raises RuntimeError."""
        service = ONetService(mock_config_no_key)
        service._cache_dir = tmp_path / "cache"
        service._cache_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(RuntimeError, match="API key not configured"):
            _ = service.client

    def test_client_lazy_initialization(self, service: ONetService) -> None:
        """HTTP client is lazily initialized."""
        assert service._client is None
        _ = service.client
        assert service._client is not None

    def test_client_reuses_instance(self, service: ONetService) -> None:
        """HTTP client is reused across calls."""
        client1 = service.client
        client2 = service.client
        assert client1 is client2


class TestClientCleanup:
    """Test HTTP client cleanup and resource management."""

    def test_close_releases_client(self, service: ONetService) -> None:
        """close() releases the HTTP client."""
        _ = service.client  # Initialize client
        assert service._client is not None

        service.close()
        assert service._client is None

    def test_close_safe_to_call_multiple_times(self, service: ONetService) -> None:
        """close() can be called multiple times safely."""
        _ = service.client
        service.close()
        service.close()  # Should not raise
        assert service._client is None

    def test_close_safe_before_client_init(self, mock_config: ONetConfig, tmp_path: Path) -> None:
        """close() safe to call before client is initialized."""
        svc = ONetService(mock_config)
        svc._cache_dir = tmp_path / "cache"
        svc._cache_dir.mkdir(parents=True, exist_ok=True)

        svc.close()  # Should not raise
        assert svc._client is None

    def test_context_manager_closes_client(self, mock_config: ONetConfig, tmp_path: Path) -> None:
        """Context manager closes client on exit."""
        with ONetService(mock_config) as svc:
            svc._cache_dir = tmp_path / "cache"
            svc._cache_dir.mkdir(parents=True, exist_ok=True)
            _ = svc.client
            assert svc._client is not None

        assert svc._client is None

    def test_context_manager_closes_on_exception(
        self, mock_config: ONetConfig, tmp_path: Path
    ) -> None:
        """Context manager closes client even on exception."""
        svc: ONetService | None = None
        try:
            with ONetService(mock_config) as svc:
                svc._cache_dir = tmp_path / "cache"
                svc._cache_dir.mkdir(parents=True, exist_ok=True)
                _ = svc.client
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert svc is not None
        assert svc._client is None
