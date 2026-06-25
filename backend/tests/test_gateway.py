from unittest.mock import patch

import pytest


def _setup_prompt(client, name="gw-prompt", content="Answer the question: {{input}}"):
    pid = client.post("/api/prompts", json={"name": name}).json()["id"]
    vid = client.post(
        f"/api/prompts/{pid}/versions", json={"content": content}
    ).json()["id"]
    return pid, vid


MOCK_QUALITY = {
    "relevance": 0.9,
    "completeness": 0.8,
    "coherence": 0.85,
    "reasoning": "Good quality response",
}

MOCK_HALLUCINATION = {
    "score": 0.1,
    "reasoning": "No hallucinated content detected",
}

MOCK_MODERATION = {
    "passed": True,
    "reasoning": "Content is appropriate",
}

LOW_QUALITY = {
    "relevance": 0.3,
    "completeness": 0.2,
    "coherence": 0.4,
    "reasoning": "Poor quality response",
}

HIGH_HALLUCINATION = {
    "score": 0.8,
    "reasoning": "Multiple fabricated claims",
}

MOCK_MODERATION_FAIL = {
    "passed": False,
    "reasoning": "Content contains harmful material",
}


def _mock_generate(prompt_template, input_text, locale):
    return f"Mock response for '{input_text}' in {locale}"


def _mock_judge_quality(*args, **kwargs):
    return MOCK_QUALITY


def _mock_judge_hallucination(*args, **kwargs):
    return MOCK_HALLUCINATION


def _mock_moderate(*args, **kwargs):
    return MOCK_MODERATION


class TestGatewayRun:
    @patch("app.routers.gateway.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.routers.gateway.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "No hallucination"},
    )
    @patch(
        "app.routers.gateway.judge.score_quality",
        return_value={"score": 0.85, "reasoning": "Good quality"},
    )
    @patch("app.routers.gateway.generate", side_effect=_mock_generate)
    def test_successful_run(self, mock_gen, mock_qual, mock_hall, mock_mod, client):
        _setup_prompt(client)
        r = client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "What is AI?", "locale": "en-US"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["overall_passed"] is True
        assert data["quality_score"] == 0.85
        assert data["hallucination_score"] == 0.1
        assert data["moderation_passed"] is True
        assert "Mock response" in data["llm_output"]
        assert "eval_run_id" in data

    @patch("app.routers.gateway.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.routers.gateway.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.routers.gateway.judge.score_quality",
        return_value={"score": 0.5, "reasoning": "Below threshold"},
    )
    @patch("app.routers.gateway.generate", side_effect=_mock_generate)
    def test_fails_quality_threshold(self, mock_gen, mock_qual, mock_hall, mock_mod, client):
        _setup_prompt(client)
        r = client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "test", "locale": "en-US"},
        )
        assert r.status_code == 200
        assert r.json()["overall_passed"] is False
        assert r.json()["quality_score"] == 0.5

    @patch("app.routers.gateway.moderator.check_moderation", return_value=MOCK_MODERATION)
    @patch(
        "app.routers.gateway.judge.score_hallucination",
        return_value={"score": 0.8, "reasoning": "Fabricated"},
    )
    @patch(
        "app.routers.gateway.judge.score_quality",
        return_value={"score": 0.9, "reasoning": "Good"},
    )
    @patch("app.routers.gateway.generate", side_effect=_mock_generate)
    def test_fails_hallucination_threshold(
        self, mock_gen, mock_qual, mock_hall, mock_mod, client
    ):
        _setup_prompt(client)
        r = client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "test", "locale": "es-MX"},
        )
        assert r.status_code == 200
        assert r.json()["overall_passed"] is False
        assert r.json()["hallucination_score"] == 0.8

    @patch(
        "app.routers.gateway.moderator.check_moderation",
        return_value=MOCK_MODERATION_FAIL,
    )
    @patch(
        "app.routers.gateway.judge.score_hallucination",
        return_value={"score": 0.1, "reasoning": "OK"},
    )
    @patch(
        "app.routers.gateway.judge.score_quality",
        return_value={"score": 0.9, "reasoning": "Good"},
    )
    @patch("app.routers.gateway.generate", side_effect=_mock_generate)
    def test_fails_moderation(self, mock_gen, mock_qual, mock_hall, mock_mod, client):
        _setup_prompt(client)
        r = client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "test", "locale": "en-US"},
        )
        assert r.status_code == 200
        assert r.json()["overall_passed"] is False
        assert r.json()["moderation_passed"] is False

    def test_prompt_not_found(self, client):
        r = client.post(
            "/api/gateway/run",
            json={"prompt_name": "nonexistent", "input": "test", "locale": "en-US"},
        )
        assert r.status_code == 404

    def test_no_active_version(self, client):
        client.post("/api/prompts", json={"name": "empty-prompt"})
        r = client.post(
            "/api/gateway/run",
            json={"prompt_name": "empty-prompt", "input": "test", "locale": "en-US"},
        )
        assert r.status_code == 404

    def test_invalid_locale(self, client):
        r = client.post(
            "/api/gateway/run",
            json={"prompt_name": "test", "input": "test", "locale": "xx-YY"},
        )
        assert r.status_code == 422

    @patch(
        "app.routers.gateway.world_readiness.validate",
        return_value={"passed": True, "checks": []},
    )
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
    def test_with_specific_version_id(
        self, mock_gen, mock_qual, mock_hall, mock_mod, mock_wr, client
    ):
        pid, vid = _setup_prompt(client)
        v2_id = client.post(
            f"/api/prompts/{pid}/versions", json={"content": "V2 prompt"}
        ).json()["id"]

        r = client.post(
            "/api/gateway/run",
            json={
                "prompt_name": "gw-prompt",
                "input": "test",
                "locale": "ja-JP",
                "version_id": v2_id,
            },
        )
        assert r.status_code == 200
        assert r.json()["overall_passed"] is True


class TestModerationFailClosed:
    @patch(
        "app.services.moderator.moderate_call",
        side_effect=Exception("Connection error"),
    )
    def test_moderation_exception_returns_fail(self, mock_call):
        from app.services.moderator import check_moderation

        result = check_moderation("test text", "en-US")
        assert result["passed"] is False
        assert "fail-closed" in result["reasoning"]


class TestEvalRunsEndpoints:
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
    def test_list_eval_runs(self, mock_gen, mock_qual, mock_hall, mock_mod, client):
        _setup_prompt(client)
        client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "q1", "locale": "en-US"},
        )
        client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "q2", "locale": "es-MX"},
        )

        r = client.get("/api/eval-runs")
        assert r.status_code == 200
        assert len(r.json()) == 2

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
    def test_filter_by_locale(self, mock_gen, mock_qual, mock_hall, mock_mod, client):
        _setup_prompt(client)
        client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "q1", "locale": "en-US"},
        )
        client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "q2", "locale": "ar-SA"},
        )

        r = client.get("/api/eval-runs?locale=ar-SA")
        assert len(r.json()) == 1
        assert r.json()[0]["locale"] == "ar-SA"

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
    def test_get_eval_run_detail(self, mock_gen, mock_qual, mock_hall, mock_mod, client):
        _setup_prompt(client)
        run_resp = client.post(
            "/api/gateway/run",
            json={"prompt_name": "gw-prompt", "input": "q1", "locale": "en-US"},
        )
        eval_id = run_resp.json()["eval_run_id"]

        r = client.get(f"/api/eval-runs/{eval_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == eval_id
        assert data["quality_score"] == 0.9
        assert data["locale"] == "en-US"

    def test_get_eval_run_not_found(self, client):
        r = client.get("/api/eval-runs/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404
