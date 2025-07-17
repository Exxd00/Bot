import os
import json
import traceback
from flask import Flask, request, jsonify
from github import Github
import openai
from base64 import b64encode
from datetime import datetime

app = Flask(__name__)

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
    try:
        data = request.get_json()
        action = data.get("action")
        print(f">>> Action Received: {action}")

        if action == "create_repo":
            token = get_token("GITHUB_TOKEN")
            g = Github(token)
            user = g.get_user()
            repo_name = data["repo"]
            repo = user.create_repo(repo_name)
            initialize_repo(repo)
            return jsonify({"status": "repo created", "url": repo.clone_url})

        elif action == "list_repo_names_only":
            token = get_token("GITHUB_TOKEN")
            g = Github(token)
            user = g.get_user()
            repo_names = [repo.name for repo in user.get_repos()]
            return jsonify({"repos": repo_names})

        elif action == "list_files":
            token = get_token("GITHUB_TOKEN")
            g = Github(token)
            repo = g.get_repo(data["repo"])
            branch = data.get("branch", "main")
            files = repo.get_contents("", ref=branch)
            result = []

            while files:
                file_content = files.pop(0)
                if file_content.type == "dir":
                    files.extend(repo.get_contents(file_content.path))
                else:
                    result.append(file_content.path)

            return jsonify({"files": result})

        elif action == "get_file":
            token = get_token("GITHUB_TOKEN")
            g = Github(token)
            repo = g.get_repo(data["repo"])
            file = repo.get_contents(data["path"], ref=data.get("branch", "main"))
            return jsonify({"content": file.decoded_content.decode()})

        elif action == "update_file":
            token = get_token("GITHUB_TOKEN")
            g = Github(token)
            repo = g.get_repo(data["repo"])
            path = data["path"]
            branch = data.get("branch", "main")
            file = repo.get_contents(path, ref=branch)
            repo.update_file(path, data.get("message", "update via API"), data["content"], file.sha, branch=branch)
            return jsonify({"status": "updated"})

        elif action == "upload_file":
            token = get_token("GITHUB_TOKEN")
            g = Github(token)
            repo = g.get_repo(data["repo"])
            path = data["path"]
            content = data["content"]
            branch = data.get("branch", "main")

            try:
                existing_file = repo.get_contents(path, ref=branch)
                repo.update_file(path, "update file", content, existing_file.sha, branch=branch)
                return jsonify({"status": "file updated"})
            except:
                repo.create_file(path, "create file", content, branch=branch)
                return jsonify({"status": "file created"})

        return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        traceback.print_exc()
        print("خطأ أثناء تنفيذ run-action:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Bot API is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # يستخدم PORT المناسب من البيئة
    app.run(host="0.0.0.0", port=port)         # يسمح بالوصول من الإنترنت
