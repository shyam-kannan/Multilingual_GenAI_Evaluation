import pytest


def _create_prompt(client, name="gs-prompt"):
    return client.post("/api/prompts", json={"name": name}).json()


def _create_golden(client, prompt_id, locale="en-US", input_text="Hello"):
    return client.post(
        "/api/golden-sets",
        json={
            "prompt_id": prompt_id,
            "locale": locale,
            "input_text": input_text,
            "expected_output": "Expected response",
        },
    )


class TestGoldenSetCRUD:
    def test_create_golden_example(self, client):
        pid = _create_prompt(client)["id"]
        r = _create_golden(client, pid)
        assert r.status_code == 201
        data = r.json()
        assert data["locale"] == "en-US"
        assert data["input_text"] == "Hello"
        assert data["expected_output"] == "Expected response"

    def test_create_with_invalid_locale(self, client):
        pid = _create_prompt(client)["id"]
        r = client.post(
            "/api/golden-sets",
            json={"prompt_id": pid, "locale": "xx-YY", "input_text": "test"},
        )
        assert r.status_code == 422

    def test_create_with_nonexistent_prompt(self, client):
        r = client.post(
            "/api/golden-sets",
            json={
                "prompt_id": "00000000-0000-0000-0000-000000000000",
                "locale": "en-US",
                "input_text": "test",
            },
        )
        assert r.status_code == 404

    def test_list_golden_examples(self, client):
        pid = _create_prompt(client)["id"]
        _create_golden(client, pid, "en-US", "one")
        _create_golden(client, pid, "es-MX", "two")
        _create_golden(client, pid, "ja-JP", "three")

        r = client.get("/api/golden-sets")
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_filter_by_prompt_id(self, client):
        p1 = _create_prompt(client, "p1")["id"]
        p2 = _create_prompt(client, "p2")["id"]
        _create_golden(client, p1, "en-US", "one")
        _create_golden(client, p2, "en-US", "two")

        r = client.get(f"/api/golden-sets?prompt_id={p1}")
        assert len(r.json()) == 1
        assert r.json()[0]["prompt_id"] == p1

    def test_filter_by_locale(self, client):
        pid = _create_prompt(client)["id"]
        _create_golden(client, pid, "en-US", "one")
        _create_golden(client, pid, "ar-SA", "two")

        r = client.get("/api/golden-sets?locale=ar-SA")
        assert len(r.json()) == 1
        assert r.json()[0]["locale"] == "ar-SA"

    def test_update_golden_example(self, client):
        pid = _create_prompt(client)["id"]
        gid = _create_golden(client, pid).json()["id"]

        r = client.put(
            f"/api/golden-sets/{gid}",
            json={"input_text": "Updated input", "expected_output": "Updated output"},
        )
        assert r.status_code == 200
        assert r.json()["input_text"] == "Updated input"
        assert r.json()["expected_output"] == "Updated output"

    def test_update_not_found(self, client):
        r = client.put(
            "/api/golden-sets/00000000-0000-0000-0000-000000000000",
            json={"input_text": "nope"},
        )
        assert r.status_code == 404

    def test_delete_golden_example(self, client):
        pid = _create_prompt(client)["id"]
        gid = _create_golden(client, pid).json()["id"]

        r = client.delete(f"/api/golden-sets/{gid}")
        assert r.status_code == 204

        r = client.get("/api/golden-sets")
        assert len(r.json()) == 0

    def test_delete_not_found(self, client):
        r = client.delete("/api/golden-sets/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404
