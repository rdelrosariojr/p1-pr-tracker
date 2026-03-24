import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

FILTER_LABELS = {"Opened by sun-asterisk", "Created by sun-asterisk"}
EXCLUDE_LABELS = {"pending", "in-progress"} 


def fetch_prs():
    result = []
    page = 1
    per_page = 30

    while True:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls?state=open&page={page}&per_page={per_page}"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        prs = resp.json()
        if not prs:
            break

        for pr in prs:
            pr_labels = {label["name"] for label in pr.get("labels", [])}
            if not FILTER_LABELS.intersection(pr_labels):
                continue
            if EXCLUDE_LABELS.intersection(pr_labels):
                continue

            comments = fetch_comments(pr["comments_url"])
            commits = fetch_commits(pr["commits_url"])
            reviews = fetch_reviews(pr["url"])

            result.append({
                "number": pr["number"],
                "title": pr["title"],
                "author": pr["user"]["login"],
                "url": pr["html_url"],
                "created_at": pr["created_at"],
                "requested_reviewers": pr.get("requested_reviewers", []),
                "comments": comments,
                "commits": commits,
                "reviews": reviews,
                "labels": [l["name"] for l in pr.get("labels", [])]
            })

        page += 1

    return result


def fetch_comments(url):
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []

    return [
        {
            "author": c["user"]["login"],
            "body": c["body"],
            "created_at": c["created_at"]
        }
        for c in resp.json()
        if "[bot]" not in c["user"]["login"].lower()
    ]


def fetch_commits(url):
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []

    return [
        {
            "author": cm["commit"]["author"]["name"],
            "message": cm["commit"]["message"],
            "date": cm["commit"]["author"]["date"]
        }
        for cm in resp.json()
        if "[bot]" not in cm["commit"]["author"]["name"].lower()
    ]


def fetch_reviews(pr_url):
    resp = requests.get(f"{pr_url}/reviews", headers=headers, timeout=15)
    if resp.status_code != 200:
        return []

    return [
        {
            "author": r["user"]["login"],
            "state": r["state"],
            "submitted_at": r["submitted_at"]
        }
        for r in resp.json()
        if r.get("submitted_at") and "[bot]" not in r["user"]["login"].lower()
    ]