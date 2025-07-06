import os
import json
from flask import Flask, request, jsonify, send_from_directory
from github import Github
import openai

app = Flask(__name__)

# ملف حفظ التوكنات
TOKENS_FILE_PATH = os.path.join("data", "tokens.json")
if os.path.exists(TOKENS_FILE_PATH):
    with open(TOKENS_FILE_PATH, "r") as f:
        TEMP_TOKENS = json.load(f)
else:
    TEMP_TOKENS = {}

def save_tokens():
    os.makedirs("data", exist_ok=True)
    with open(TOKENS_FILE_PATH, "w") as f:
        json.dump(TEMP_TOKENS, f)

def get_token(name):
    return TEMP_TOKENS.get(name) or os.environ.get(name)

def initialize_repo(repo_obj):
    """تهيئة المستودع بملف README.md إذا كان فارغًا"""
    try:
        repo_obj.create_file("README.md", "Initial commit", "# Initialized")
    except Exception:
        pass  # المستودع قد يكون مهيأ بالفعل

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.get_json()
    action = data.get("action")
    repo = data.get("repo")
    path = data.get("path")
    content = data.get("content")
    token = get_token("GITHUB_TOKEN")
    api_key = request.headers.get("x-api-key")

    if api_key != os.environ.get("API_KEY", "super-secret-key-123"):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        g = Github(token)

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
                return jsonify({"link": link, "note": "Edit manually in Canva."})
            else:
                return jsonify({"error": "Template not found"}), 404

        elif action == "list_repo_names_only":
            user = g.get_user()
            repos = [repo.name for repo in user.get_repos()]
            return jsonify({"repos": repos})

        elif action == "list_files":
            repo_obj = g.get_user().get_repo(repo)
            contents = repo_obj.get_contents("")
            file_names = [c.name for c in contents]
            return jsonify({"files": file_names})

        elif action == "get_file":
            repo_obj = g.get_user().get_repo(repo)
            file = repo_obj.get_contents(path)
            return jsonify({"content": file.decoded_content.decode()})

        elif action == "update_file":
            repo_obj = g.get_user().get_repo(repo)
            try:
                file = repo_obj.get_contents(path)
                repo_obj.update_file(file.path, "update via API", content, file.sha)
                return jsonify({"message": "File updated"})
            except Exception as e:
                try:
                    repo_obj.create_file(path, "create via API", content)
                    return jsonify({"message": "File created"})
                except Exception as ex:
                    try:
                        initialize_repo(repo_obj)
                        repo_obj.create_file(path, "create after init", content)
                        return jsonify({"message": "File created after init"})
                    except Exception as final_ex:
                        return jsonify({"error": f"Final create failed: {str(final_ex)}"}), 500

        elif action == "fetch_limited_commits":
            limit = data.get("limit", 10)
            repo_obj = g.get_user().get_repo(repo)
            commits = repo_obj.get_commits()[:limit]
            return jsonify({"commits": [c.sha for c in commits]})

        return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/docs")
def serve_docs():
    return send_from_directory("docs", "index.html")
