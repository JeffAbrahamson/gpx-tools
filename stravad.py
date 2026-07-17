#!/usr/bin/env python3
"""Check strava for my rides and my friends' rides.

TODO:

  * Manage API key.

  * This script does not refresh tokens; you may want to enhance it
    with OAuth refresh token logic.

  * Add paging to fetch_rides.

"""

import argparse
import json
import os
import sqlite3
import sys

import requests

STRAVA_API_BASE = "https://www.strava.com/api/v3"
DEFAULT_PER_PAGE = 200
DEFAULT_REQUEST_TIMEOUT = 30


def parse_args():
    parser = argparse.ArgumentParser(description="Strava ride data sync daemon.")
    parser.add_argument("--db", type=str, help="SQLite3 database file", required=True)
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize new database (requires --db)",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config JSON file",
    )
    return parser.parse_args()


def init_db(db_path):
    if os.path.exists(db_path):
        print("Error: database already exists.")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE rides (
            id INTEGER NOT NULL,
            user TEXT NOT NULL,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            distance REAL NOT NULL,
            moving_time INTEGER NOT NULL,
            elapsed_time INTEGER NOT NULL,
            PRIMARY KEY (user, id)
        )
    """
    )
    conn.commit()
    conn.close()
    print("Database initialized.")


def load_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)

    if not isinstance(config.get("users"), list):
        raise ValueError("Invalid config: users must be a list.")
    for index, user in enumerate(config["users"], start=1):
        if not user.get("name") or not user.get("access_token"):
            raise ValueError(
                f"Invalid config: user {index} needs name and access_token."
            )

    if "rate_limit_per_hour" in config and config["rate_limit_per_hour"] <= 0:
        raise ValueError("Invalid config: rate_limit_per_hour must be positive.")
    if "per_page" in config and not 1 <= config["per_page"] <= DEFAULT_PER_PAGE:
        raise ValueError(f"Invalid config: per_page must be 1-{DEFAULT_PER_PAGE}.")

    if "rate_limit_per_hour" not in config:
        config["rate_limit_per_hour"] = 1000
    if "per_page" not in config:
        config["per_page"] = DEFAULT_PER_PAGE
    if "request_timeout" not in config:
        config["request_timeout"] = DEFAULT_REQUEST_TIMEOUT
    if config["request_timeout"] <= 0:
        raise ValueError("Invalid config format.")

    return config


def get_existing_ride_ids(conn, user):
    c = conn.cursor()
    c.execute("SELECT id FROM rides WHERE user = ?", (user,))
    return set(row[0] for row in c.fetchall())


def fetch_rides_page(
    user_token,
    *,
    page,
    per_page=DEFAULT_PER_PAGE,
    after=None,
    before=None,
    timeout=DEFAULT_REQUEST_TIMEOUT,
):
    headers = {"Authorization": f"Bearer {user_token}"}
    params = {"page": page, "per_page": per_page}
    if after:
        params["after"] = int(after.timestamp())
    if before:
        params["before"] = int(before.timestamp())
    response = requests.get(
        f"{STRAVA_API_BASE}/athlete/activities",
        headers=headers,
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def fetch_rides(
    user_token,
    *,
    after=None,
    before=None,
    per_page=DEFAULT_PER_PAGE,
    max_requests=None,
    timeout=DEFAULT_REQUEST_TIMEOUT,
):
    rides = []
    requests_made = 0
    page = 1

    while max_requests is None or requests_made < max_requests:
        page_rides = fetch_rides_page(
            user_token,
            page=page,
            per_page=per_page,
            after=after,
            before=before,
            timeout=timeout,
        )
        requests_made += 1
        if not page_rides:
            break
        rides.extend(page_rides)
        page += 1

    return rides, requests_made


def save_rides(conn, rides, user):
    c = conn.cursor()
    for ride in rides:
        c.execute(
            """
            INSERT OR IGNORE INTO rides (
                id, user, name, start_date, distance, moving_time, elapsed_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ride["id"],
                user,
                ride["name"],
                ride["start_date"],
                ride["distance"],
                ride["moving_time"],
                ride["elapsed_time"],
            ),
        )
    conn.commit()


def main():
    args = parse_args()

    if args.init:
        if not args.db:
            print("Error: --init requires --db.")
            sys.exit(1)
        init_db(args.db)
        return

    if not args.config:
        print("Error: --config is required unless --init is used.")
        sys.exit(1)

    if not os.path.exists(args.db):
        print("Error: database not found.")
        sys.exit(1)

    config = load_config(args.config)

    conn = sqlite3.connect(args.db)
    requests_made = 0
    max_requests = config.get("rate_limit_per_hour", 1000)

    for user_entry in config["users"]:
        if requests_made >= max_requests:
            print("Reached API rate limit for this run.")
            break

        user = user_entry["name"]
        token = user_entry["access_token"]

        try:
            existing_ids = get_existing_ride_ids(conn, user)
            remaining_requests = max_requests - requests_made
            fetched_rides, user_requests = fetch_rides(
                token,
                per_page=config["per_page"],
                max_requests=remaining_requests,
                timeout=config["request_timeout"],
            )
            requests_made += user_requests

            filtered_rides = [
                ride for ride in fetched_rides if ride["id"] not in existing_ids
            ]
            print(f"{user}: {len(filtered_rides)} new rides found.")
            save_rides(conn, filtered_rides, user)
        except Exception as e:
            print(f"Error processing user {user}: {e}")

    conn.close()


if __name__ == "__main__":
    main()
