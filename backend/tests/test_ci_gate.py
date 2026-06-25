from unittest.mock import patch

import pytest


MOCK_MODERATION = {"passed": True, "reasoning": "OK"}


def _mock_generate(prompt_template, input_text, locale):
    return f"Mock response for '{input_text}' in {locale}"


def _mock_wr_pass(text, locale):
    return {"passed": True, "checks": []}


def _setup_prompt_with_golden(client, name="ci-prompt"):
    pid = client.post("/api/prompts", json={"name": name}).json()["id"]
    v1_id = client.post(
        f"/api/prompts/{pid}/versions", json={"content": "V1: Answer {{input}}"}
    ).json()["id"]

    client.patch(
        f"/api/prompts/{pid}/versions/{v1_id}/labels",
        json={"labels": ["production"]},
    )

    client.post(
        "/api/golden-sets",
        json={"prompt_id": pid, "locale": "en-US", "input_text": "What is AI?"},
    )
    client.post(
        "/api/golden-sets",
        json={"prompt_id": pid, "locale": "es-MX", "input_text": "¿Qué es la IA?"},
    )
    return pid, v1_id


class TestCIGate:
    @patch("app.services.ci_gate.world_readiness.validate", side_effect=_mock_wr_pass)
    @patch("app.services.ci_gate.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.services.ci_gate.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.services.ci_gate.judge.score_quality",
        return_value={"score": 0.9, "reasoning": "Good"},
    )
    @patch("app.services.ci_gate.generate", side_effect=_mock_generate)
    def test_ci_passes_no_baseline(
        self, mock_gen, mock_qual, mock_hall, mock_mod, mock_wr, client
    ):
        pid = client.post("/api/prompts", json={"name": "new-prompt"}).json()["id"]
        client.post(
            f"/api/prompts/{pid}/versions", json={"content": "First version"}
        )
        client.post(
            "/api/golden-sets",
            json={"prompt_id": pid, "locale": "en-US", "input_text": "test"},
        )

        r = client.post(
            "/api/ci/check",
            json={"prompt_name": "new-prompt", "locales": ["en-US"]},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["passed"] is True
        assert data["status"] == "passed"
        assert len(data["regressions"]) == 0

    @patch("app.services.ci_gate.world_readiness.validate", side_effect=_mock_wr_pass)
    @patch("app.services.ci_gate.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.services.ci_gate.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.services.ci_gate.judge.score_quality",
        return_value={"score": 0.9, "reasoning": "Good"},
    )
    @patch("app.services.ci_gate.generate", side_effect=_mock_generate)
    def test_ci_passes_no_regression(
        self, mock_gen, mock_qual, mock_hall, mock_mod, mock_wr, client
    ):
        pid, v1_id = _setup_prompt_with_golden(client)

        # Run baseline eval first
        client.post(
            "/api/ci/check",
            json={"prompt_name": "ci-prompt", "locales": ["en-US"]},
        )

        # Create v2 and run CI check
        v2_id = client.post(
            f"/api/prompts/{pid}/versions", json={"content": "V2: Better answer {{input}}"}
        ).json()["id"]

        r = client.post(
            "/api/ci/check",
            json={"prompt_name": "ci-prompt", "locales": ["en-US"], "version_id": v2_id},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["passed"] is True
        assert len(data["regressions"]) == 0

    @patch("app.services.ci_gate.world_readiness.validate", side_effect=_mock_wr_pass)
    @patch("app.services.ci_gate.moderator.check_moderation", return_value=MOCK_MODERATION)
    def test_ci_detects_quality_regression(self, mock_mod, mock_wr, client):
        pid, v1_id = _setup_prompt_with_golden(client)

        # Run baseline with high quality
        with patch("app.services.ci_gate.judge.score_quality", return_value={"score": 0.9, "reasoning": "Good"}), \
             patch("app.services.ci_gate.judge.score_hallucination", return_value={"score": 0.1, "reasoning": "OK"}), \
             patch("app.services.ci_gate.generate", side_effect=_mock_generate):
            client.post(
                "/api/ci/check",
                json={"prompt_name": "ci-prompt", "locales": ["en-US"]},
            )

        # Create v2 and run with low quality
        v2_id = client.post(
            f"/api/prompts/{pid}/versions", json={"content": "V2: Worse prompt"}
        ).json()["id"]

        with patch("app.services.ci_gate.judge.score_quality", return_value={"score": 0.5, "reasoning": "Bad"}), \
             patch("app.services.ci_gate.judge.score_hallucination", return_value={"score": 0.1, "reasoning": "OK"}), \
             patch("app.services.ci_gate.generate", side_effect=_mock_generate):
            r = client.post(
                "/api/ci/check",
                json={"prompt_name": "ci-prompt", "locales": ["en-US"], "version_id": v2_id},
            )

        assert r.status_code == 200
        data = r.json()
        assert data["passed"] is False
        assert data["status"] == "failed"
        assert len(data["regressions"]) >= 1
        assert data["regressions"][0]["metric"] == "quality"

    @patch("app.services.ci_gate.world_readiness.validate", side_effect=_mock_wr_pass)
    @patch("app.services.ci_gate.moderator.check_moderation", return_value=MOCK_MODERATION)
    def test_ci_detects_hallucination_regression(self, mock_mod, mock_wr, client):
        pid, v1_id = _setup_prompt_with_golden(client)

        # Run baseline with low hallucination
        with patch("app.services.ci_gate.judge.score_quality", return_value={"score": 0.9, "reasoning": "Good"}), \
             patch("app.services.ci_gate.judge.score_hallucination", return_value={"score": 0.1, "reasoning": "OK"}), \
             patch("app.services.ci_gate.generate", side_effect=_mock_generate):
            client.post(
                "/api/ci/check",
                json={"prompt_name": "ci-prompt", "locales": ["en-US"]},
            )

        # Create v2 and run with high hallucination
        v2_id = client.post(
            f"/api/prompts/{pid}/versions", json={"content": "V2: Hallucinates"}
        ).json()["id"]

        with patch("app.services.ci_gate.judge.score_quality", return_value={"score": 0.9, "reasoning": "Good"}), \
             patch("app.services.ci_gate.judge.score_hallucination", return_value={"score": 0.6, "reasoning": "Fabricated"}), \
             patch("app.services.ci_gate.generate", side_effect=_mock_generate):
            r = client.post(
                "/api/ci/check",
                json={"prompt_name": "ci-prompt", "locales": ["en-US"], "version_id": v2_id},
            )

        assert r.status_code == 200
        data = r.json()
        assert data["passed"] is False
        assert any(reg["metric"] == "hallucination" for reg in data["regressions"])

    @patch("app.services.ci_gate.world_readiness.validate", side_effect=_mock_wr_pass)
    @patch("app.services.ci_gate.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.services.ci_gate.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.services.ci_gate.judge.score_quality",
        return_value={"score": 0.9, "reasoning": "Good"},
    )
    @patch("app.services.ci_gate.generate", side_effect=_mock_generate)
    def test_ci_skips_locale_without_goldens(
        self, mock_gen, mock_qual, mock_hall, mock_mod, mock_wr, client
    ):
        pid = client.post("/api/prompts", json={"name": "skip-test"}).json()["id"]
        client.post(f"/api/prompts/{pid}/versions", json={"content": "prompt"})
        client.post(
            "/api/golden-sets",
            json={"prompt_id": pid, "locale": "en-US", "input_text": "test"},
        )

        r = client.post(
            "/api/ci/check",
            json={"prompt_name": "skip-test", "locales": ["en-US", "ja-JP"]},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["details"]["ja-JP"]["status"] == "skipped"

    def test_ci_prompt_not_found(self, client):
        r = client.post(
            "/api/ci/check",
            json={"prompt_name": "nonexistent"},
        )
        assert r.status_code == 404


class TestDashboard:
    @patch("app.routers.gateway.world_readiness.validate", return_value={"passed": True, "checks": []})
    @patch("app.routers.gateway.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.routers.gateway.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.routers.gateway.judge.score_quality",
        return_value={"score": 0.9, "reasoning": "Good"},
    )
    @patch("app.routers.gateway.generate", side_effect=_mock_generate)
    def test_overview_with_data(
        self, mock_gen, mock_qual, mock_hall, mock_mod, mock_wr, client
    ):
        pid = client.post("/api/prompts", json={"name": "dash-prompt"}).json()["id"]
        client.post(f"/api/prompts/{pid}/versions", json={"content": "prompt"})
        client.post(
            "/api/gateway/run",
            json={"prompt_name": "dash-prompt", "input": "test", "locale": "en-US"},
        )

        r = client.get("/api/dashboard/overview")
        assert r.status_code == 200
        data = r.json()
        assert data["total_runs"] == 1
        assert data["total_prompts"] == 1
        assert data["locale_stats"]["en-US"]["total_runs"] == 1
        assert len(data["recent_runs"]) == 1

    def test_overview_empty(self, client):
        r = client.get("/api/dashboard/overview")
        assert r.status_code == 200
        data = r.json()
        assert data["total_runs"] == 0
        assert data["locale_stats"]["en-US"]["total_runs"] == 0

    @patch("app.routers.gateway.world_readiness.validate", return_value={"passed": True, "checks": []})
    @patch("app.routers.gateway.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.routers.gateway.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.routers.gateway.judge.score_quality",
        return_value={"score": 0.85, "reasoning": "Good"},
    )
    @patch("app.routers.gateway.generate", side_effect=_mock_generate)
    def test_prompt_history(
        self, mock_gen, mock_qual, mock_hall, mock_mod, mock_wr, client
    ):
        pid = client.post("/api/prompts", json={"name": "hist-prompt"}).json()["id"]
        client.post(f"/api/prompts/{pid}/versions", json={"content": "v1 prompt"})
        client.post(
            "/api/gateway/run",
            json={"prompt_name": "hist-prompt", "input": "test", "locale": "en-US"},
        )

        r = client.get(f"/api/dashboard/prompts/{pid}/history")
        assert r.status_code == 200
        data = r.json()
        assert data["prompt_id"] == pid
        assert len(data["history"]) == 1
        assert data["history"][0]["version"] == 1
        assert "en-US" in data["history"][0]["locale_scores"]

    def test_ci_history_empty(self, client):
        r = client.get("/api/dashboard/ci-history")
        assert r.status_code == 200
        assert r.json() == []

    @patch("app.services.ci_gate.world_readiness.validate", side_effect=_mock_wr_pass)
    @patch("app.services.ci_gate.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.services.ci_gate.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.services.ci_gate.judge.score_quality",
        return_value={"score": 0.9, "reasoning": "Good"},
    )
    @patch("app.services.ci_gate.generate", side_effect=_mock_generate)
    def test_ci_history_with_data(
        self, mock_gen, mock_qual, mock_hall, mock_mod, mock_wr, client
    ):
        pid = client.post("/api/prompts", json={"name": "ci-hist"}).json()["id"]
        client.post(f"/api/prompts/{pid}/versions", json={"content": "prompt"})
        client.post(
            "/api/golden-sets",
            json={"prompt_id": pid, "locale": "en-US", "input_text": "test"},
        )
        client.post("/api/ci/check", json={"prompt_name": "ci-hist", "locales": ["en-US"]})

        r = client.get("/api/dashboard/ci-history")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["status"] == "passed"
