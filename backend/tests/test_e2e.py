"""
End-to-End (E2E) Tests for SchemaDoc AI API.

Framework: pytest + httpx.AsyncClient (in-process, no running server needed).

JUSTIFICATION:
- httpx.AsyncClient lets us test the real FastAPI `app` object without spinning
  up a separate uvicorn process, making tests fast and CI-friendly.
- pytest-asyncio provides native async test support.
- We test real HTTP semantics (status codes, headers, JSON bodies) — not unit mocks.

Run with:
    pytest backend/tests/test_e2e.py -v
"""
import sys
import pytest
import pytest_asyncio
from pathlib import Path
from httpx import AsyncClient, ASGITransport

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.main import app


# ─────────────────────────────── Fixtures ───────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI app (no network)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def reset_state():
    """Reset server state between tests to avoid cross-contamination."""
    from backend.services.pipeline_service import clear_all_runs
    from backend.api.routes.export import _report_cache
    clear_all_runs()
    _report_cache.clear()
    yield
    clear_all_runs()
    _report_cache.clear()


# ══════════════════════════════════════════════════════════════════════════
#  HAPPY-PATH TESTS
# ══════════════════════════════════════════════════════════════════════════

class TestHappyPath:
    """Tests that verify normal, expected behavior end-to-end."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, client: AsyncClient):
        """GET /api/health should return 200 with service info."""
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "SchemaDoc AI API"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_root_returns_api_info(self, client: AsyncClient):
        """GET / should return API metadata links."""
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "docs" in data
        assert "health" in data

    @pytest.mark.asyncio
    async def test_list_databases_returns_array(self, client: AsyncClient):
        """GET /api/pipeline/databases should return a list (possibly empty)."""
        resp = await client.get("/api/pipeline/databases")
        assert resp.status_code == 200
        data = resp.json()
        assert "databases" in data
        assert isinstance(data["databases"], list)

    @pytest.mark.asyncio
    async def test_list_runs_initially_empty(self, client: AsyncClient):
        """GET /api/pipeline/runs should return an empty list on fresh start."""
        resp = await client.get("/api/pipeline/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_reset_session_clears_state(self, client: AsyncClient):
        """POST /api/reset should return success confirmation."""
        resp = await client.post("/api/reset")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_openapi_docs_accessible(self, client: AsyncClient):
        """GET /api/docs should return the Swagger UI page."""
        resp = await client.get("/api/docs")
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
#  FAILURE / EDGE-CASE TESTS
# ══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests that verify error handling, validation, and abuse prevention."""

    @pytest.mark.asyncio
    async def test_pipeline_run_invalid_connection_string(self, client: AsyncClient):
        """POST /api/pipeline/run with a bogus connection string should fail gracefully."""
        resp = await client.post(
            "/api/pipeline/run",
            json={"connection_string": "sqlite:///nonexistent_path/fake_db.db"},
        )
        # Should return 500 (pipeline execution error) — NOT an unhandled traceback
        assert resp.status_code == 500
        data = resp.json()
        # Verify structured error response (from our centralized handler)
        assert "error" in data
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_pipeline_run_missing_body(self, client: AsyncClient):
        """POST /api/pipeline/run with no body should return 422 validation error."""
        resp = await client.post("/api/pipeline/run")
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_run(self, client: AsyncClient):
        """GET /api/pipeline/run/<bad_id> should return 404."""
        resp = await client.get("/api/pipeline/run/nonexistent-id")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_schema_nonexistent_run(self, client: AsyncClient):
        """GET /api/schema/<bad_id> should return 404."""
        resp = await client.get("/api/schema/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_missing_run(self, client: AsyncClient):
        """POST /api/chat with an invalid run_id should return 404."""
        resp = await client.post(
            "/api/chat",
            json={"message": "Show all tables", "run_id": "does-not-exist", "history": []},
        )
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_chat_empty_message_rejected(self, client: AsyncClient):
        """POST /api/chat with empty message should return 422 (Pydantic min_length=1)."""
        resp = await client.post(
            "/api/chat",
            json={"message": "", "run_id": "any-id", "history": []},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_export_json_nonexistent_run(self, client: AsyncClient):
        """GET /api/export/<bad_id>/json should return 404."""
        resp = await client.get("/api/export/nonexistent-id/json")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_markdown_nonexistent_run(self, client: AsyncClient):
        """GET /api/export/<bad_id>/markdown should return 404."""
        resp = await client.get("/api/export/nonexistent-id/markdown")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_report_nonexistent_run(self, client: AsyncClient):
        """GET /api/export/<bad_id>/report should return 404."""
        resp = await client.get("/api/export/nonexistent-id/report")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_schema_overview_nonexistent_run(self, client: AsyncClient):
        """GET /api/schema/<bad_id>/overview should return 404."""
        resp = await client.get("/api/schema/nonexistent-id/overview")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_schema_table_nonexistent_run(self, client: AsyncClient):
        """GET /api/schema/<bad_id>/table/foo should return 404."""
        resp = await client.get("/api/schema/nonexistent-id/table/foo")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════
#  RATE LIMITING TESTS
# ══════════════════════════════════════════════════════════════════════════

class TestRateLimiting:
    """Verify that rate limiting returns 429 when thresholds are exceeded."""

    @pytest.mark.asyncio
    async def test_rate_limit_on_pipeline_run(self, client: AsyncClient):
        """
        POST /api/pipeline/run is limited to 5/minute.
        Sending 7 rapid requests should trigger at least one 429 response.

        Note: The first few might fail with 500 (invalid DB), but the rate
        limiter should kick in regardless of downstream errors.
        """
        statuses = []
        for _ in range(7):
            resp = await client.post(
                "/api/pipeline/run",
                json={"connection_string": "sqlite:///nonexistent.db"},
            )
            statuses.append(resp.status_code)

        # At least one should be rate-limited (429)
        assert 429 in statuses, (
            f"Expected at least one 429 response, got: {statuses}"
        )

    @pytest.mark.asyncio
    async def test_rate_limit_response_structure(self, client: AsyncClient):
        """429 responses should have structured JSON error body."""
        # Exhaust the rate limit
        for _ in range(7):
            resp = await client.post(
                "/api/pipeline/run",
                json={"connection_string": "sqlite:///nonexistent.db"},
            )
            if resp.status_code == 429:
                data = resp.json()
                assert data["error"] == "RateLimitExceeded"
                assert "detail" in data
                assert data["status_code"] == 429
                return  # test passed

        pytest.skip("Rate limit was not triggered within 7 requests")


# ══════════════════════════════════════════════════════════════════════════
#  ERROR RESPONSE STRUCTURE TESTS
# ══════════════════════════════════════════════════════════════════════════

class TestErrorResponseStructure:
    """Verify that all error responses follow our centralized format."""

    @pytest.mark.asyncio
    async def test_404_has_structured_body(self, client: AsyncClient):
        """Any 404 should have 'error', 'detail', and 'status_code' fields."""
        resp = await client.get("/api/pipeline/run/does-not-exist")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert "detail" in data
        assert "status_code" in data
        assert data["status_code"] == 404

    @pytest.mark.asyncio
    async def test_422_has_field_errors(self, client: AsyncClient):
        """Validation errors should include field-level details."""
        resp = await client.post("/api/pipeline/run", json={})
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data
        assert data["error"] == "ValidationError"
        assert "field_errors" in data
