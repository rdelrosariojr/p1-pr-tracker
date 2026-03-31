from flask import Flask, request, jsonify
from services.github import fetch_prs, fetch_sun_devs
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

@app.route("/slack")
def slack_devs():
    try:
        devs = fetch_sun_devs()
        return jsonify(devs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/slack/command", methods=["POST"])
def slack_command():
    try:
        command = request.form.get("command")

        if command == "/pro-one-pr-tracker":
            prs = fetch_prs()
            message = format_all(prs)

            return {
                "response_type": "in_channel",  # visible to everyone
                "text": message
            }

        return {"text": "Unknown command"}, 400

    except Exception as e:
        return {"text": f"Error: {str(e)}"}, 500

if __name__ == "__main__":
    app.run(debug=True)