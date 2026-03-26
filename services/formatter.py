# from datetime import datetime, timezone

# SUN_DEVELOPERS = {"mdv-sunasterisk", "jeraldechavia", "jstephend-sun", "jescabillas", "rdelrosariojr", "NiloJr-sun", "reno-angelo", "Francis-Tulang", "hieutm-3360" } 


# def parse_time(t):
#     return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")


# def time_ago(iso_time):
#     now = datetime.now(timezone.utc)
#     past = parse_time(iso_time).replace(tzinfo=timezone.utc)
#     diff = now - past

#     days = diff.days
#     hours = diff.total_seconds() // 3600

#     if days > 0:
#         return f"{int(days)} day(s) ago"
#     elif hours > 0:
#         return f"{int(hours)} hr(s) ago"
#     return "just now"


# def build_timeline(pr):
#     timeline = []

#     timeline.append({
#         "type": "opened",
#         "author": pr["author"],
#         "time": pr["created_at"]
#     })

#     for c in pr["comments"]:
#         timeline.append({
#             "type": "comment",
#             "author": c["author"],
#             "body": c["body"],
#             "time": c["created_at"]
#         })

#     for cm in pr["commits"]:
#         timeline.append({
#             "type": "commit",
#             "author": cm["author"],
#             "time": cm["date"]
#         })

#     for r in pr["reviews"]:
#         timeline.append({
#             "type": "review",
#             "author": r["author"],
#             "state": r["state"],
#             "time": r["submitted_at"]
#         })

#     timeline.sort(key=lambda x: parse_time(x["time"]), reverse=True)
#     return timeline


# def format_pr(pr):
#     timeline = build_timeline(pr)

#     lines = []
#     lines.append(f"• *<{pr['url']}|{pr['title']}>*")
#     lines.append(f"  Author: {pr['author']}")

#     for item in timeline[:4]:
#         t = time_ago(item["time"])

#         if item["type"] == "opened":
#             lines.append(f"  - PR was opened {t}")

#         elif item["type"] == "comment":
#             lines.append(f"  - {item['author']} commented {t}")

#         elif item["type"] == "commit":
#             lines.append(f"  - {item['author']} added a commit {t}")

#         elif item["type"] == "review":
#             if item["state"] == "APPROVED":
#                 lines.append(f"  - {item['author']} approved {t}")
#             elif item["state"] == "CHANGES_REQUESTED":
#                 lines.append(f"  - {item['author']} requested changes {t}")
#             else:
#                 lines.append(f"  - {item['author']} reviewed {t}")

#     # Smart warnings
#     if not pr["requested_reviewers"]:
#         lines.append("  - ⚠️ No assigned reviewer")

#     return "\n".join(lines)


# def format_all(prs):
#     return "\n\n".join([format_pr(pr) for pr in prs])

from datetime import datetime, timezone

SUN_DEVELOPERS = {
    "mdv-sunasterisk",
    "jeraldechavia",
    "jstephend-sun",
    "jescabillas",
    "rdelrosariojr",
    "NiloJr-sun",
    "reno-angelo",
    "Francis-Tulang",
    "hieutm-3360",
}


# =========================
# TIME HELPERS
# =========================
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


# =========================
# HELPERS
# =========================
def get_latest_reviews(reviews):
    latest = {}
    for r in reviews:
        author = r["author"]
        if author not in latest or parse_time(r["submitted_at"]) > parse_time(latest[author]["submitted_at"]):
            latest[author] = r
    return list(latest.values())


def all_in_sun(users):
    return all(u in SUN_DEVELOPERS for u in users)


# =========================
# MAIN FORMATTER
# =========================
def format_pr(pr):
    message = ""

    requested_reviewers = pr.get("requested_reviewers", [])
    reviews = pr.get("reviews", [])
    comments = pr.get("comments", [])
    commits = pr.get("commits", [])
    labels = pr.get("labels", [])
    author = pr["author"]

    # latest commit
    latest_commit = max(commits, key=lambda x: parse_time(x["date"])) if commits else None

    # =========================
    # NO REVIEWS
    # =========================
    if not reviews:
        if not requested_reviewers:
            message = "If the PR isn’t ready for review, please add an “in-progress” or “pending” label. Otherwise, kindly request a review."
        else:
            reviewer_logins = [r["login"] for r in requested_reviewers]

            if all_in_sun(reviewer_logins):
                reviewers = ", ".join(reviewer_logins)
                message = f"{reviewers} Please review this PR."
            else:
                message = "Please follow up on the client review request."

        # comments override
        if comments and all(c["author"] != author for c in comments):
            latest_comment = max(comments, key=lambda x: parse_time(x["created_at"]))
            message = f"New comment/s ({time_ago(latest_comment['created_at'])}), please check."

    # =========================
    # WITH REVIEWS
    # =========================
    else:
        latest_reviews = get_latest_reviews(reviews)

        review_authors = [r["author"] for r in latest_reviews]
        states = [r["state"] for r in latest_reviews]

        all_approved = all(s == "APPROVED" for s in states)
        all_sun = all_in_sun(review_authors)

        # -------------------------
        # ALL APPROVED
        # -------------------------
        if all_approved:
            latest_approval = max(latest_reviews, key=lambda x: parse_time(x["submitted_at"]))
            t = time_ago(latest_approval["submitted_at"])

            if not all_sun:
                message = f"All reviewers approved ({t}). Please merge this PR."
            else:
                reviewer_logins = [r["login"] for r in requested_reviewers]

                if "server" in labels:
                    if not requested_reviewers or all_in_sun(reviewer_logins):
                        message = "Please endorse this for client review."
                else:
                    if not requested_reviewers or all_in_sun(reviewer_logins):
                        message = "If requires client review, please request. Otherwise, please merge this PR."

        # -------------------------
        # COMMENTED / CHANGES REQUESTED
        # -------------------------
        else:
            flagged_reviews = [
                r for r in latest_reviews
                if r["state"] in ["COMMENTED", "CHANGES_REQUESTED"]
            ]

            if flagged_reviews and latest_commit:
                latest_flag = max(flagged_reviews, key=lambda x: parse_time(x["submitted_at"]))
                review_time = parse_time(latest_flag["submitted_at"])
                commit_time = parse_time(latest_commit["date"])

                t_review = time_ago(latest_flag["submitted_at"])
                t_commit = time_ago(latest_commit["date"])

                if review_time > commit_time:
                    message = f"New comments/change requests from {latest_flag['author']} ({t_review}), please check."
                else:
                    message = f"If the new commit, ({t_commit}), was to address comments/change requests, please notify the author."

    # =========================
    # FORMAT OUTPUT
    # =========================
    opened_time = time_ago(pr["created_at"])

    lines = []
    lines.append(f"• <{pr['url']}|{pr['title']}>")
    lines.append(f"  Author: {author}, opened {opened_time}")
    lines.append(f"  - {message}")

    return "\n".join(lines)


# =========================
# FORMAT ALL
# =========================
def format_all(prs):
    if not prs:
        return "No open PRs."

    return "\n\n".join([format_pr(pr) for pr in prs])