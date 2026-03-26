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


def any_not_in_sun(users):
    return any(u not in SUN_DEVELOPERS for u in users)


def tag_users(usernames):
    """Return Slack-style mentions for SUN_DEVELOPERS"""
    return " ".join([f"@{u}" for u in usernames if u in SUN_DEVELOPERS])


# =========================
# FORMAT SINGLE PR
# =========================
def format_pr(pr):
    message = ""
    extra_message = ""
    status = "🟡 Waiting Review"

    requested_reviewers = pr.get("requested_reviewers", [])
    reviews = pr.get("reviews", [])
    comments = pr.get("comments", [])
    commits = pr.get("commits", [])
    labels = pr.get("labels", [])
    author = pr["author"]

    latest_commit = max(commits, key=lambda x: parse_time(x["date"])) if commits else None

    # -------------------------
    # NO REVIEWS
    # -------------------------
    if not reviews:
        if not requested_reviewers:
            message = "If the PR isn’t ready for review, please add an “in-progress” or “pending” label. Otherwise, kindly request a review."
            status = "🔴 Needs Action"
        else:
            reviewer_logins = [r["login"] for r in requested_reviewers]
            if all_in_sun(reviewer_logins):
                reviewers_tag = tag_users(reviewer_logins)
                message = f"{reviewers_tag} Please review this PR."
            else:
                message = "Please follow up on the client review request."
                status = "🔴 Needs Action"

        # comments override
        if comments and all(c["author"] != author for c in comments):
            latest_comment = max(comments, key=lambda x: parse_time(x["created_at"]))
            message = f"New comment/s ({time_ago(latest_comment['created_at'])}), please check."
            status = "🔴 Needs Action"

    # -------------------------
    # WITH REVIEWS
    # -------------------------
    else:
        latest_reviews = get_latest_reviews(reviews)
        review_authors = [r["author"] for r in latest_reviews]
        states = [r["state"] for r in latest_reviews]

        all_approved = all(s == "APPROVED" for s in states)
        all_sun = all_in_sun(review_authors)

        # ===== ALL APPROVED =====
        if all_approved:
            latest_approval = max(latest_reviews, key=lambda x: parse_time(x["submitted_at"]))
            t = time_ago(latest_approval["submitted_at"])

            reviewer_logins = [r["login"] for r in requested_reviewers]

            if not all_sun:
                message = f"All reviewers approved ({t}). Please merge this PR."
                status = "🟢 Ready to Merge"
            else:
                # All reviewers are SUN
                if "server" in labels:
                    if not requested_reviewers or all_in_sun(reviewer_logins):
                        message = "Please endorse this for client review."
                        status = "🔴 Needs Action"
                    else:
                        message = "Please follow up on the client review request."
                        status = "🔴 Needs Action"
                else:
                    if not requested_reviewers or all_in_sun(reviewer_logins):
                        message = "If requires client review, please request. Otherwise, please merge this PR."
                        status = "🔴 Needs Action"
                    else:
                        message = "Please follow up on the client review request."
                        status = "🔴 Needs Action"

        # ===== COMMENTED / CHANGES_REQUESTED =====
        else:
            flagged_reviews = [r for r in latest_reviews if r["state"] in ["COMMENTED", "CHANGES_REQUESTED"]]

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
            status = "🔴 Needs Action"

    # -------------------------
    # EXTRA LABEL MESSAGE
    # -------------------------
    if "Can be tested directly in dev" not in labels and "Requires local testing" not in labels:
        extra_message = 'Please add "Can be tested directly in dev" or "Requires local testing" if local testing is needed.'

    # -------------------------
    # FORMAT OUTPUT
    # -------------------------
    opened_time = time_ago(pr["created_at"])
    lines = []
    lines.append(f"• <{pr['url']}|{pr['title']}>")
    lines.append(f"  Author: {author}, opened {opened_time}")
    lines.append(f"  - {message}")
    if extra_message:
        lines.append(f"  - {extra_message}")

    return status, "\n".join(lines)


# =========================
# FORMAT ALL PRs (GROUPED)
# =========================
def format_all(prs):
    if not prs:
        return "No open PRs."

    grouped = {"🔴 Needs Action": [], "🟡 Waiting Review": [], "🟢 Ready to Merge": []}

    for pr in prs:
        status, formatted = format_pr(pr)
        grouped[status].append(formatted)

    output = []

    # Add tracker header
    output.append("🔹 SUN PR Tracker - Overview")
    output.append("This tracker summarizes the current state of open PRs, highlighting required reviews, approvals, comments, and testing labels.\n")

    for section in ["🔴 Needs Action", "🟡 Waiting Review", "🟢 Ready to Merge"]:
        if grouped[section]:
            output.append(section)
            output.append("\n".join(grouped[section]))
            output.append("")  # spacing

    output.append("\n📌 Notes:")
    output.append("  - React with :white_check_mark: once you have completed the required actions.")
    output.append("  - If an action does not apply to you, feel free to disregard it.")
    output.append("  - Ensure testing labels are added for PRs that require local testing.")

    return "\n".join(output).strip()