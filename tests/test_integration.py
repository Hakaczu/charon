from datetime import datetime

from charon import cache as cache_utils
from charon.decision import DecisionResult


FAKE_HISTORY = [
    ["2024-01-01", 4.0],
    ["2024-01-02", 4.1],
]


def test_health(api_client):
    client, _, _ = api_client
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_snapshot_and_history(api_client):
    client, fake_redis, api = api_client
    decisions = [
        DecisionResult(
            name="US Dollar",
            code="USD",
            latest_rate=4.1,
            change_pct=1.0,
            decision="sell",
            basis="1% above",
            icon_class="fa-dollar",
        )
    ]
    fetched_at = datetime(2024, 1, 2)
    history_map = {"USD": FAKE_HISTORY}
    payload = cache_utils.serialize_snapshot(decisions, fetched_at, history_map)
    fake_redis.setex(api.REDIS_CACHE_KEY, 3600, payload)

    snap = client.get("/api/v1/snapshot")
    assert snap.status_code == 200
    data = snap.json()
    assert data["items"][0]["code"] == "USD"
    assert data["history_map"]["USD"] == FAKE_HISTORY

    history = client.get("/api/v1/history", params={"code": "USD"})
    assert history.status_code == 200
    assert history.json()["points"] == FAKE_HISTORY

    missing = client.get("/api/v1/history", params={"code": "EUR"})
    assert missing.status_code == 404
