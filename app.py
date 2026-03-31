from flask import Flask, request, jsonify
from threading import Thread
from services.github import fetch_prs, fetch_sun_devs
from services.formatter import format_all
from services.slack import send_message
import logging

app = Flask(__name__)


@app.route("/")
def home():
    return "PR Tracker is running 🚀"


@app.route("/prs")
def get_prs():
    try:
        prs = fetch_prs()
        return jsonify(prs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/send-to-slack")
def send_to_slack():
    try:
        prs = fetch_prs()
        message = format_all(prs)
        send_message(message)
        return {"status": "sent"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/slack")
def slack_devs():
    try:
        devs = fetch_sun_devs()
        return jsonify(devs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/slack/command", methods=["POST"])
def slack_command():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    data = request.form
    response_url = data.get("response_url")
    command = request.form.get("command")
    
    def process():
        try:
            prs = fetch_prs()
            message = format_all(prs)
            logger.info("Received Slack command: %s", command)
            logger.info("Fetching PRs started")
            logger.info("PRs fetched: %d", len(prs))

            requests.post(response_url, json={
                "response_type": "in_channel",
                "text": message
            })
        except Exception as e:
            requests.post(response_url, json={
                "text": f"Error: {str(e)}"
            })

    Thread(target=process).start()

    # MUST return within 3 seconds
    return {"text": "Fetching PRs... please wait ⏳"}

if __name__ == "__main__":
    app.run(debug=True)