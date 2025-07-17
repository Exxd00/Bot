import os
import json
import traceback
from flask import Flask, request, jsonify
from github import Github
import openai

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
    except Exception as e:
        print("Repo already initialized or error:", e)

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.get_json()
    print(f"===> Received data: {data}")
    
    try:
        action = data.get("action")
        if action == "create_repo":
            return handle_create_repo(data)
        elif action == "upload_file":
            return handle_upload_file(data)
        elif action == "get_file":
            return handle_get_file(data)
        elif action == "update_file":
            return handle_update_file(data)
        elif action == "list_files":
            return handle_list_files(data)
        elif action == "list_repo_names_only":
            return handle_list_repos()
        else:
            return jsonify({"error": f"Unknown action '{action}'"}), 400
    except Exception as e:
        print("===> Error occurred:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def get_github_user():
    token = get_token("GITHUB_TOKEN")
    if not token:
        raise Exception("GitHub token is missing.")
    g = Github(token)
    return g.get_user()

def handle_create_repo(data):
    repo_name = data.get("repo")
    if not repo_name:
        raise Exception("Missing 'repo' field in request.")
    user = get_github_user()
    repo = user.create_repo(repo_name)
    initialize_repo(repo)
    return jsonify({"message": f"Repository '{repo_name}' created successfully."})

def handle_upload_file(data):
    repo_name = data.get("repo")
    path = data.get("path")
    content = data.get("content")
    message = data.get("message", "upload via API")
    if not all([repo_name, path, content]):
        raise Exception("Missing required fields: 'repo', 'path', or 'content'")
    user = get_github_user()
    repo = user.get_repo(repo_name)
    repo.create_file(path, message, content)
    return jsonify({"message": f"File '{path}' uploaded to '{repo_name}'."})

def handle_get_file(data):
    repo_name = data.get("repo")
    path = data.get("path")
    user = get_github_user()
    repo = user.get_repo(repo_name)
    file_content = repo.get_contents(path)
    return jsonify({
        "content": file_content.decoded_content.decode(),
        "sha": file_content.sha
    })

def handle_update_file(data):
    repo_name = data.get("repo")
    path = data.get("path")
    new_content = data.get("content")
    sha = data.get("sha")
    message = data.get("message", "update via API")
    user = get_github_user()
    repo = user.get_repo(repo_name)
    repo.update_file(path, message, new_content, sha)
    return jsonify({"message": f"File '{path}' updated in '{repo_name}'."})

def handle_list_files(data):
    repo_name = data.get("repo")
    user = get_github_user()
    repo = user.get_repo(repo_name)
    contents = repo.get_contents("")
    files = [{"path": c.path, "type": c.type} for c in contents]
    return jsonify(files)

def handle_list_repos():
    user = get_github_user()
    repos = user.get_repos()
    return jsonify([repo.name for repo in repos])

if __name__ == "__main__":
    app.run(debug=True)
