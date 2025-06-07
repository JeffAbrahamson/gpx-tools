#!/usr/bin/env python
# coding=utf8

"""Check PR message sanity."""

import json
import os

# import re

commit_regex = r"^[A-Z].{0,50}[^.]$"


def check_pr_message():
    """Do basic checks on commit message sanity."""
    with open(
        os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8"
    ) as fp_git_event:
        event = fp_git_event.read()
    event_json = json.loads(event)
    head_commit_sha = event_json["pull_request"]["base"]["sha"]
    print("head_commit_sha: ", head_commit_sha)
    # For another day, actually check the commit message from HEAD
    # back to base branch.


if __name__ == "__main__":
    check_pr_message()
