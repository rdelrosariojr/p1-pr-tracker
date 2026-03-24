from datetime import datetime, timezone


def parse_time(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")


def time_ago(iso_time):
    now = datetime.now(timezone.utc)
    past = parse_time(iso_time).replace(tzinfo=timezone.utc)
    diff = now - past

    days = diff.days
    hours = diff.total_seconds() // 3600

    if days > 0:
        return f"{int(days)} day(s) ago"
    elif hours > 0:
        return f"{int(hours)} hr(s) ago"
    return "just now"


def build_timeline(pr):
    timeline = []

    timeline.append({
        "type": "opened",
        "author": pr["author"],
        "time": pr["created_at"]
    })

    for c in pr["comments"]:
        timeline.append({
            "type": "comment",
            "author": c["author"],
            "body": c["body"],
            "time": c["created_at"]
        })

    for cm in pr["commits"]:
        timeline.append({
            "type": "commit",
            "author": cm["author"],
            "time": cm["date"]
        })

    for r in pr["reviews"]:
        timeline.append({
            "type": "review",
            "author": r["author"],
            "state": r["state"],
            "time": r["submitted_at"]
        })

    timeline.sort(key=lambda x: parse_time(x["time"]), reverse=True)
    return timeline


def format_pr(pr):
    timeline = build_timeline(pr)

    lines = []
    lines.append(f"• *<{pr['url']}|{pr['title']}>*")
    lines.append(f"  Author: {pr['author']}")

    for item in timeline[:4]:
        t = time_ago(item["time"])

        if item["type"] == "opened":
            lines.append(f"  - PR was opened {t}")

        elif item["type"] == "comment":
            lines.append(f"  - {item['author']} commented {t}")

        elif item["type"] == "commit":
            lines.append(f"  - {item['author']} added a commit {t}")

        elif item["type"] == "review":
            if item["state"] == "APPROVED":
                lines.append(f"  - {item['author']} approved {t}")
            elif item["state"] == "CHANGES_REQUESTED":
                lines.append(f"  - {item['author']} requested changes {t}")
            else:
                lines.append(f"  - {item['author']} reviewed {t}")

    # Smart warnings
    if not pr["requested_reviewers"]:
        lines.append("  - ⚠️ No assigned reviewer")

    return "\n".join(lines)


def format_all(prs):
    return "\n\n".join([format_pr(pr) for pr in prs])