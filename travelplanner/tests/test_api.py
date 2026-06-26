from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_session_create():
    response = client.post("/session/create")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0


def test_chat_flow():
    # create session
    r = client.post("/session/create")
    sid = r.json()["session_id"]

    # send message
    r = client.post(f"/chat/{sid}", json={"message": "Quiero viajar a Paris por 3 dias"})
    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    assert len(data["response"]) > 0

    # check history
    r = client.get(f"/session/{sid}/history")
    assert r.status_code == 200
    history = r.json()["history"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "bot"


def test_session_reset():
    r = client.post("/session/create")
    sid = r.json()["session_id"]

    client.post(f"/chat/{sid}", json={"message": "Hola"})
    r = client.get(f"/session/{sid}/history")
    assert len(r.json()["history"]) > 0

    client.post(f"/session/{sid}/reset")
    r = client.get(f"/session/{sid}/history")
    assert r.json()["history"] == []
