import sqlite3

import pytest

import stravad


def ride(identifier, name="Ride"):
    return {
        "id": identifier,
        "name": name,
        "start_date": "2026-05-01T10:00:00Z",
        "distance": 1000.0,
        "moving_time": 300,
        "elapsed_time": 360,
    }


def test_init_db_allows_same_activity_id_for_different_users(tmp_path):
    db_path = tmp_path / "rides.sqlite"
    stravad.init_db(db_path)
    conn = sqlite3.connect(db_path)

    stravad.save_rides(conn, [ride(1, "Alice Ride")], "alice")
    stravad.save_rides(conn, [ride(1, "Bob Ride")], "bob")

    rows = conn.execute("SELECT user, id FROM rides ORDER BY user").fetchall()
    assert rows == [("alice", 1), ("bob", 1)]


def test_save_rides_ignores_duplicate_for_same_user(tmp_path):
    db_path = tmp_path / "rides.sqlite"
    stravad.init_db(db_path)
    conn = sqlite3.connect(db_path)

    stravad.save_rides(conn, [ride(1), ride(1)], "alice")

    rows = conn.execute("SELECT user, id FROM rides").fetchall()
    assert rows == [("alice", 1)]


def test_load_config_supplies_defaults(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"users": [{"name": "alice", "access_token": "token"}]}',
        encoding="utf-8",
    )

    config = stravad.load_config(config_path)

    assert config["rate_limit_per_hour"] == 1000
    assert config["per_page"] == stravad.DEFAULT_PER_PAGE
    assert config["request_timeout"] == stravad.DEFAULT_REQUEST_TIMEOUT


def test_load_config_rejects_bad_per_page(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"per_page": 500, "users": [{"name": "alice", "access_token": "token"}]}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="per_page"):
        stravad.load_config(config_path)


def test_fetch_rides_paginates_until_empty(monkeypatch):
    calls = []

    def fake_fetch_page(token, *, page, per_page, after, before, timeout):
        calls.append((token, page, per_page, after, before, timeout))
        if page == 1:
            return [ride(1)]
        if page == 2:
            return [ride(2)]
        return []

    monkeypatch.setattr(stravad, "fetch_rides_page", fake_fetch_page)

    rides, requests_made = stravad.fetch_rides(
        "token",
        per_page=100,
        timeout=5,
    )

    assert [item["id"] for item in rides] == [1, 2]
    assert requests_made == 3
    assert calls == [
        ("token", 1, 100, None, None, 5),
        ("token", 2, 100, None, None, 5),
        ("token", 3, 100, None, None, 5),
    ]


def test_fetch_rides_honors_max_requests(monkeypatch):
    def fake_fetch_page(token, *, page, per_page, after, before, timeout):
        return [ride(page)]

    monkeypatch.setattr(stravad, "fetch_rides_page", fake_fetch_page)

    rides, requests_made = stravad.fetch_rides("token", max_requests=2)

    assert [item["id"] for item in rides] == [1, 2]
    assert requests_made == 2


def test_parse_args_allows_init_without_config(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["stravad.py", "--db", "rides.sqlite", "--init"],
    )

    args = stravad.parse_args()

    assert args.init
    assert args.config is None
