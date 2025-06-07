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
import time
from datetime import datetime

import requests

STRAVA_API_BASE = "https://www.strava.com/api/v3"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Strava ride data sync daemon."
    )
    parser.add_argument(
        "--db", type=str, help="SQLite3 database file", required=True
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize new database (requires --db)",
    )
    parser.add_argument(
        "--config", type=str, help="Path to config JSON file", required=True
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
            id INTEGER PRIMARY KEY,
            user TEXT,
            name TEXT,
            start_date TEXT,
            distance REAL,
            moving_time INTEGER,
            elapsed_time INTEGER,
            UNIQUE(id, user)
        )
    """
    )
    conn.commit()
    conn.close()
    print("Database initialized.")


def load_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    # Basic validation
    if "users" not in config or "rate_limit_per_hour" not in config:
        raise ValueError("Invalid config format.")
    return config


def get_existing_ride_ids(conn, user):
    c = conn.cursor()
    c.execute("SELECT id FROM rides WHERE user = ?", (user,))
    return set(row[0] for row in c.fetchall())


def fetch_rides(user_token, after=None):
    headers = {"Authorization": f"Bearer {user_token}"}
    params = {"per_page": 50}
    if after:
        params["after"] = int(after.timestamp())
    response = requests.get(
        f"{STRAVA_API_BASE}/athlete/activities", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


def save_rides(conn, rides, user):
    c = conn.cursor()
    for ride in rides:
        try:
            c.execute(
                """
                INSERT OR IGNORE INTO rides (id, user, name, start_date, distance, moving_time, elapsed_time)
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
        except sqlite3.IntegrityError:
            continue
    conn.commit()


def main():
    args = parse_args()

    if args.init:
        if not args.db:
            print("Error: --init requires --db.")
            sys.exit(1)
        init_db(args.db)
        return

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
            new_rides = fetch_rides(token)
            requests_made += 1

            filtered_rides = [
                ride for ride in new_rides if ride["id"] not in existing_ids
            ]
            print(f"{user}: {len(filtered_rides)} new rides found.")
            save_rides(conn, filtered_rides, user)
        except Exception as e:
            print(f"Error processing user {user}: {e}")

    conn.close()


if __name__ == "__main__":
    main()
