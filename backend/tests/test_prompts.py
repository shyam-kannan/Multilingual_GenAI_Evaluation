import pytest


def _create_prompt(client, name="test-prompt"):
    return client.post("/api/prompts", json={"name": name})


def _create_version(client, prompt_id, content="Hello {{input}}"):
    return client.post(f"/api/prompts/{prompt_id}/versions", json={"content": content})


class TestPromptCRUD:
    def test_create_prompt(self, client):
        r = _create_prompt(client)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "test-prompt"
        assert "id" in data

    def test_create_prompt_duplicate_name(self, client):
        _create_prompt(client, "dup")
        r = _create_prompt(client, "dup")
        assert r.status_code == 409

    def test_list_prompts(self, client):
        _create_prompt(client, "a")
        _create_prompt(client, "b")
        r = client.get("/api/prompts")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_prompt(self, client):
        pid = _create_prompt(client).json()["id"]
        r = client.get(f"/api/prompts/{pid}")
        assert r.status_code == 200
        assert r.json()["name"] == "test-prompt"
        assert r.json()["versions"] == []

    def test_get_prompt_not_found(self, client):
        r = client.get("/api/prompts/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404


class TestVersioning:
    def test_create_version(self, client):
        pid = _create_prompt(client).json()["id"]
        r = _create_version(client, pid, "v1 content")
        assert r.status_code == 201
        data = r.json()
        assert data["version"] == 1
        assert data["is_active"] is True

    def test_first_version_auto_active(self, client):
        pid = _create_prompt(client).json()["id"]
        r = _create_version(client, pid, "first")
        assert r.json()["is_active"] is True

    def test_second_version_not_auto_active(self, client):
        pid = _create_prompt(client).json()["id"]
        _create_version(client, pid, "first")
        r = _create_version(client, pid, "second")
        assert r.json()["version"] == 2
        assert r.json()["is_active"] is False

    def test_version_increments(self, client):
        pid = _create_prompt(client).json()["id"]
        _create_version(client, pid, "v1")
        _create_version(client, pid, "v2")
        r = _create_version(client, pid, "v3")
        assert r.json()["version"] == 3

    def test_duplicate_content_rejected(self, client):
        pid = _create_prompt(client).json()["id"]
        _create_version(client, pid, "same content")
        r = _create_version(client, pid, "same content")
        assert r.status_code == 409

    def test_versions_in_prompt_detail(self, client):
        pid = _create_prompt(client).json()["id"]
        _create_version(client, pid, "v1")
        _create_version(client, pid, "v2")
        r = client.get(f"/api/prompts/{pid}")
        assert len(r.json()["versions"]) == 2


class TestActivateAndRollback:
    def test_activate_version(self, client):
        pid = _create_prompt(client).json()["id"]
        v1 = _create_version(client, pid, "v1").json()
        v2 = _create_version(client, pid, "v2").json()

        r = client.patch(f"/api/prompts/{pid}/versions/{v2['id']}/activate")
        assert r.status_code == 200
        assert r.json()["is_active"] is True

        detail = client.get(f"/api/prompts/{pid}").json()
        active_versions = [v for v in detail["versions"] if v["is_active"]]
        assert len(active_versions) == 1
        assert active_versions[0]["id"] == v2["id"]

    def test_rollback(self, client):
        pid = _create_prompt(client).json()["id"]
        v1 = _create_version(client, pid, "v1").json()
        v2 = _create_version(client, pid, "v2").json()
        client.patch(f"/api/prompts/{pid}/versions/{v2['id']}/activate")

        r = client.post(f"/api/prompts/{pid}/rollback/{v1['id']}")
        assert r.status_code == 200
        assert r.json()["is_active"] is True
        assert r.json()["id"] == v1["id"]

    def test_activate_not_found(self, client):
        pid = _create_prompt(client).json()["id"]
        r = client.patch(
            f"/api/prompts/{pid}/versions/00000000-0000-0000-0000-000000000000/activate"
        )
        assert r.status_code == 404


class TestLabels:
    def test_update_labels(self, client):
        pid = _create_prompt(client).json()["id"]
        vid = _create_version(client, pid, "v1").json()["id"]

        r = client.patch(
            f"/api/prompts/{pid}/versions/{vid}/labels",
            json={"labels": ["production", "reviewed"]},
        )
        assert r.status_code == 200
        assert r.json()["labels"] == ["production", "reviewed"]

    def test_update_labels_replaces(self, client):
        pid = _create_prompt(client).json()["id"]
        vid = _create_version(client, pid, "v1").json()["id"]
        client.patch(
            f"/api/prompts/{pid}/versions/{vid}/labels",
            json={"labels": ["old"]},
        )
        r = client.patch(
            f"/api/prompts/{pid}/versions/{vid}/labels",
            json={"labels": ["new"]},
        )
        assert r.json()["labels"] == ["new"]


class TestDiff:
    def test_diff_versions(self, client):
        pid = _create_prompt(client).json()["id"]
        v1 = _create_version(client, pid, "line one\nline two").json()
        v2 = _create_version(client, pid, "line one\nline three").json()

        r = client.get(f"/api/prompts/{pid}/diff/{v1['id']}/{v2['id']}")
        assert r.status_code == 200
        data = r.json()
        assert "line two" in data["diff"]
        assert "line three" in data["diff"]
        assert data["v1_version"] == 1
        assert data["v2_version"] == 2

    def test_diff_not_found(self, client):
        pid = _create_prompt(client).json()["id"]
        v1 = _create_version(client, pid, "v1").json()
        r = client.get(
            f"/api/prompts/{pid}/diff/{v1['id']}/00000000-0000-0000-0000-000000000000"
        )
        assert r.status_code == 404
