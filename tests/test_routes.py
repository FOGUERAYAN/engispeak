def test_home_shows_login_when_anonymous(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Commencer la roadmap" in response.text


def test_login_rejects_invalid_id(client):
    response = client.post("/login", data={"student_id": "!"})
    assert response.status_code == 400


def test_login_sets_cookie_and_shows_dashboard(logged_client):
    response = logged_client.get("/")
    assert response.status_code == 200
    assert "0 étape sur 16" in response.text


def test_week_page_requires_login(client):
    response = client.get("/weeks/1", follow_redirects=False)
    assert response.status_code == 303


def test_week_page_lists_sessions(logged_client):
    response = logged_client.get("/weeks/2")
    assert response.status_code == 200
    assert "Carol Dweck" in response.text
    assert "Sunday Showcase" in response.text


def test_unknown_week_is_404(logged_client):
    assert logged_client.get("/weeks/9").status_code == 404


def test_toggle_step_from_ui(logged_client):
    response = logged_client.post("/steps/w1-s1/toggle", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/weeks/1#w1-s1"
    assert "1 étape sur 16" in logged_client.get("/").text
    logged_client.post("/steps/w1-s1/toggle")
    assert "0 étape sur 16" in logged_client.get("/").text


def test_toggle_unknown_step_is_404(logged_client):
    assert logged_client.post("/steps/w9-s99/toggle").status_code == 404


def test_resources_list_and_download(client):
    page = client.get("/resources")
    assert page.status_code == 200
    assert "fiche-test.md" in page.text
    file = client.get("/resources/fiche-test.md")
    assert file.status_code == 200
    assert file.text == "# Fiche test"


def test_resource_path_traversal_is_rejected(client):
    assert client.get("/resources/..%2F..%2Fetc%2Fpasswd").status_code == 404
    assert client.get("/resources/missing.pdf").status_code == 404


def test_api_roadmap_has_four_weeks(client):
    data = client.get("/api/roadmap").json()
    assert [w["week"] for w in data] == [1, 2, 3, 4]
    assert sum(len(w["steps"]) for w in data) == 16


def test_api_progress_roundtrip(client):
    r = client.put("/api/students/alice/steps/w1-s2", json={"completed": True})
    assert r.status_code == 200
    progress = client.get("/api/students/alice/progress").json()
    assert progress["completed_steps"] == ["w1-s2"]
    assert progress["next_step"] == "w1-s1"


def test_api_rejects_unknown_step(client):
    r = client.put("/api/students/alice/steps/nope", json={"completed": True})
    assert r.status_code == 404
