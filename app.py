from flask import Flask, jsonify
from services.github import fetch_prs
from services.formatter import format_all
from services.slack import send_message

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


if __name__ == "__main__":
    app.run(debug=True)