import os
import json
from flask import Flask, request, jsonify, send_from_directory
from github import Github
import openai

app = Flask(__name__)

# المسار إلى ملف التوكنات
TOKENS_FILE_PATH = os.path.join("data", "tokens.json")

# تحميل التوكنات من الملف (إن وجدت)
if os.path.exists(TOKENS_FILE_PATH):
    with open(TOKENS_FILE_PATH, "r") as f:
        TEMP_TOKENS = json.load(f)
else:
    TEMP_TOKENS = {}

# الدوال المساعدة لحفظ التوكنات
def save_tokens():
    os.makedirs("data", exist_ok=True)
    with open(TOKENS_FILE_PATH, "w") as f:
        json.dump(TEMP_TOKENS, f)

# جلب التوكنات
def get_token(name):
    return TEMP_TOKENS.get(name) or os.environ.get(name)

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.get_json()
    action = data.get("action")
    api_key = request.headers.get("x-api-key")

    if api_key != os.environ.get("API_KEY", "super-secret-key-123"):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        if action == "status_check":
            return jsonify({"status": "ok"})

        elif action == "set_token":
            token_type = data.get("token_type")
            token_value = data.get("value")
            TEMP_TOKENS[token_type] = token_value
            save_tokens()
            return jsonify({"message": f"{token_type} set successfully."})

        elif action == "revoke_token":
            token_type = data.get("token_type")
            if token_type in TEMP_TOKENS:
                del TEMP_TOKENS[token_type]
                save_tokens()
            return jsonify({"message": f"{token_type} removed."})

        elif action == "generate_canva_link":
            template = data.get("template")
            links = {
                "smm_strategy": "https://www.canva.com/design/DAGlHUGRn4s/BK8hrc0RjN2eZQ_bVyy7xg/edit"
            }
            link = links.get(template)
            if link:
                return jsonify({
                    "link": link,
                    "note": "Edit the SMM Strategy template manually in Canva. Direct content injection is not supported."
                })
            else:
                return jsonify({"error": "Template not found."}), 404

        return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/docs")
def serve_docs():
    return send_from_directory("docs", "index.html")