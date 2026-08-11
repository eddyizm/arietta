import os

from flask import Flask, jsonify, request

from arietta.core.auth import verify_github_signature
from arietta.core.auth import get_installation_access_token
from arietta.core.action import add_reaction
from arietta.core.action import add_label, add_milestone

app = Flask(__name__)

APP_ID           = os.environ.get("GITHUB_APP_ID")
PRIVATE_KEY_PATH = os.environ.get("GITHUB_PRIVATE_KEY_PATH")
WEBHOOK_SECRET   = os.environ.get("GITHUB_WEBHOOK_SECRET")
PORT             = os.environ.get("PORT")

THUMBS_UP        = "+1"
THUMBS_DOWN      = "-1"

API_URL         = "https://api.github.com/repos"
WHITELIST       = {"tvillega"}
BOT_BASE_NAME   = "arietta"
BOT_SUFIX       = " " # could be called like `arietta, add label bug`
BOT_NAME        = BOT_BASE_NAME+BOT_SUFIX


def try_catch_action(token, repo_full_name, issue_number, command_type, value):
    """Executes the specific command requested by the user."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    base_url = f"{API_URL}/{repo_full_name}"

    try:
        if command_type == "add label":
            add_label(f"{base_url}/issues/{issue_number}/labels",
                      headers,
                      value)

        elif command_type == "add milestone":
            add_milestone(f"{base_url}/milestones",
                          f"{base_url}/issues/{issue_number}",
                          headers,
                          value)

        return False
    except Exception:
        return False

@app.route("/webhook", methods=["POST"])
def webhook():

    verify_github_signature(WEBHOOK_SECRET)
    event = request.headers.get("X-GitHub-Event")

    if event != "issue_comment": # Issue tracker + PR's
        return jsonify({"status": "ignored event"}), 200

    payload = request.json
    action  = payload.get("action")

    if action != "created": # Ignore edited messages
        return jsonify({"status": "ignored action"}), 200

    comment  = payload.get("comment", {})
    sender   = payload.get("sender", {})
    username = sender.get("login")

    if username not in WHITELIST: # Only contributors
        return jsonify({"status": "user not whitelisted"}), 200

    comment_body    = comment.get("body", "").strip()
    comment_lower   = comment_body.lower()
    comment_id      = comment.get("id")

    installation_id = payload.get("installation", {}).get("id")
    repo_full_name  = payload.get("repository", {}).get("full_name")
    issue_number    = payload.get("issue", {}).get("number")

    if not comment_lower.startswith(BOT_NAME):
        return jsonify({"status": "not an arietta command"}), 200

    command_str     = comment_body.removeprefix(BOT_NAME).strip()
    token           = get_installation_access_token(installation_id, PRIVATE_KEY_PATH, APP_ID)
    success         = False

    if command_str.startswith("add label "):
        value   = command_str.removeprefix("add label ").strip()
        success = try_catch_action(token, repo_full_name, issue_number, "add tag", value)

    elif command_str.startswith("add milestone "):
        value   = command_str.removeprefix("add milestone ").strip()
        success = try_catch_action(token, repo_full_name, issue_number, "add milestone", value)

    # Feedback to understand if command failed or not
    reaction = THUMBS_UP if success else THUMBS_DOWN
    add_reaction(f"{API_URL}/{repo_full_name}/issues/comments/{comment_id}/reactions",
                 token,
                 reaction)

    return jsonify({"status": "success" if success else "failed command"}), 200

def main():
    app.run(port=PORT, debug=True)

if __name__ == "__main__":
    main()

