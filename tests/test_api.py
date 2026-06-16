def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["index_ready"] is True
    assert payload["document_count"] > 0


def test_ask_endpoint_returns_grounded_answer(client):
    response = client.post("/ask", json={"question": "How do I read a CSV file in pandas?"})
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert payload["question"].startswith("How do I read a CSV")
    assert len(payload["sources"]) > 0
    assert payload["mode"] in {"generation", "retrieval_only"}


def test_ask_rejects_short_question(client):
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 422


def test_ask_handles_unknown_topic(client):
    response = client.post("/ask", json={"question": "How do I configure Kubernetes ingress controllers?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert isinstance(payload["sources"], list)
