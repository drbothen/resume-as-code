"""Tests for SavedPlan model."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from resume_as_code.models.plan import SavedPlan, SelectedWorkUnit


class TestSelectedWorkUnit:
    """Tests for SelectedWorkUnit model."""

    def test_create_selected_work_unit(self) -> None:
        """Test creating a SelectedWorkUnit with all fields."""
        wu = SelectedWorkUnit(
            id="wu-2026-01-05-python-api",
            title="Built Python REST API",
            score=0.87,
            match_reasons=["Skills: python, aws", "Keywords: microservices"],
        )

        assert wu.id == "wu-2026-01-05-python-api"
        assert wu.title == "Built Python REST API"
        assert wu.score == 0.87
        assert wu.match_reasons == ["Skills: python, aws", "Keywords: microservices"]

    def test_default_match_reasons(self) -> None:
        """Test that match_reasons defaults to empty list."""
        wu = SelectedWorkUnit(
            id="wu-test",
            title="Test Work Unit",
            score=0.5,
        )

        assert wu.match_reasons == []


class TestSavedPlan:
    """Tests for SavedPlan model."""

    def test_create_saved_plan(self) -> None:
        """Test creating a SavedPlan with required fields."""
        plan = SavedPlan(
            jd_hash="a1b2c3d4e5f67890",
            selected_work_units=[
                SelectedWorkUnit(id="wu-1", title="Test", score=0.8),
            ],
            selection_count=1,
        )

        assert plan.jd_hash == "a1b2c3d4e5f67890"
        assert plan.version == "1.0.0"
        assert len(plan.selected_work_units) == 1
        assert plan.selection_count == 1

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        plan = SavedPlan(
            jd_hash="test",
            selected_work_units=[],
            selection_count=0,
        )

        assert plan.version == "1.0.0"
        assert plan.top_k == 8
        assert plan.ranker_version == "hybrid-rrf-v1"
        assert plan.jd_title is None
        assert plan.jd_path is None
        assert isinstance(plan.created_at, datetime)

    def test_hash_jd_produces_consistent_hash(self) -> None:
        """Test that _hash_jd produces consistent hashes."""
        content = "Senior Software Engineer at Acme Corp"
        hash1 = SavedPlan._hash_jd(content)
        hash2 = SavedPlan._hash_jd(content)

        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated SHA256

    def test_hash_jd_different_content_different_hash(self) -> None:
        """Test that different content produces different hashes."""
        hash1 = SavedPlan._hash_jd("Content A")
        hash2 = SavedPlan._hash_jd("Content B")

        assert hash1 != hash2

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Test that save/load produces identical plan."""
        original = SavedPlan(
            jd_hash="abc123def456",
            jd_title="Senior Engineer",
            jd_path="/path/to/jd.txt",
            selected_work_units=[
                SelectedWorkUnit(
                    id="wu-2026-01-05-api",
                    title="Built API",
                    score=0.85,
                    match_reasons=["Skills: python"],
                ),
                SelectedWorkUnit(
                    id="wu-2026-01-10-k8s",
                    title="K8s Migration",
                    score=0.72,
                    match_reasons=["Skills: kubernetes"],
                ),
            ],
            selection_count=2,
            top_k=8,
        )

        plan_file = tmp_path / "plan.yaml"
        original.save(plan_file)
        loaded = SavedPlan.load(plan_file)

        assert loaded.jd_hash == original.jd_hash
        assert loaded.jd_title == original.jd_title
        assert loaded.jd_path == original.jd_path
        assert loaded.selection_count == original.selection_count
        assert loaded.top_k == original.top_k
        assert loaded.version == original.version
        assert len(loaded.selected_work_units) == len(original.selected_work_units)

        # Check Work Units
        for loaded_wu, orig_wu in zip(
            loaded.selected_work_units, original.selected_work_units, strict=True
        ):
            assert loaded_wu.id == orig_wu.id
            assert loaded_wu.title == orig_wu.title
            assert loaded_wu.score == orig_wu.score
            assert loaded_wu.match_reasons == orig_wu.match_reasons

    def test_saved_file_has_human_readable_header(self, tmp_path: Path) -> None:
        """Test that saved plan has human-readable header comments."""
        plan = SavedPlan(
            jd_hash="test",
            selected_work_units=[],
            selection_count=0,
        )

        plan_file = tmp_path / "plan.yaml"
        plan.save(plan_file)

        content = plan_file.read_text()
        assert "# Resume Plan" in content
        assert "resume build --plan" in content

    def test_from_ranking_creates_plan(self) -> None:
        """Test creating SavedPlan from ranking output."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import RankingOutput, RankingResult

        # Create mock ranking output
        results = [
            RankingResult(
                work_unit_id="wu-1",
                work_unit={"id": "wu-1", "title": "Work Unit 1"},
                score=0.9,
                bm25_rank=1,
                semantic_rank=2,
                match_reasons=["Skills: python"],
            ),
            RankingResult(
                work_unit_id="wu-2",
                work_unit={"id": "wu-2", "title": "Work Unit 2"},
                score=0.7,
                bm25_rank=2,
                semantic_rank=1,
                match_reasons=["Keywords: api"],
            ),
        ]
        ranking = RankingOutput(results=results, jd_keywords=["python", "api"])

        # Create mock JD
        jd = JobDescription(
            raw_text="Looking for Python developer",
            title="Python Developer",
        )

        # Create plan from ranking
        plan = SavedPlan.from_ranking(
            ranking_output=ranking,
            jd=jd,
            jd_path=Path("/jobs/python.txt"),
            top_k=8,
        )

        assert plan.jd_title == "Python Developer"
        assert plan.jd_path == "/jobs/python.txt"
        assert len(plan.selected_work_units) == 2
        assert plan.selection_count == 2
        assert plan.selected_work_units[0].id == "wu-1"
        assert plan.selected_work_units[0].score == 0.9

    def test_from_ranking_respects_top_k(self) -> None:
        """Test that from_ranking only includes top_k items."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import RankingOutput, RankingResult

        # Create 5 results but only take top 2
        results = [
            RankingResult(
                work_unit_id=f"wu-{i}",
                work_unit={"id": f"wu-{i}", "title": f"WU {i}"},
                score=0.9 - (i * 0.1),
                bm25_rank=i,
                semantic_rank=i,
                match_reasons=[],
            )
            for i in range(5)
        ]
        ranking = RankingOutput(results=results, jd_keywords=[])
        jd = JobDescription(raw_text="test")

        plan = SavedPlan.from_ranking(ranking, jd, top_k=2)

        assert len(plan.selected_work_units) == 2
        assert plan.selection_count == 2
        assert plan.top_k == 2
