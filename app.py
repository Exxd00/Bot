import os
import json
from flask import Flask, request, jsonify, send_from_directory
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
                # قراءة الملف الحالي
                file = repo_obj.get_contents(path)
                old_content = file.decoded_content.decode("utf-8")

                # دمج المحتوى الجديد فوق القديم (يمكن تعديله حسب الحاجة)
                new_content = content + "\n\n" + old_content

                # التحديث
                repo_obj.update_file(file.path, "Merged update via API", new_content, file.sha)
                return jsonify({"message": "File updated with merged content"})
            except Exception as e:
                try:
                    repo_obj.create_file(path, "create via API", content)
                    return jsonify({"message": "File created"})
                except Exception as ex:
                    return jsonify({"error": f"Create failed: {str(ex)}"}), 500

        elif action == "fetch_limited_commits":
            limit = data.get("limit", 10)
            repo_obj = g.get_user().get_repo(repo)
            commits = repo_obj.get_commits()[:limit]
            return jsonify({"commits": [c.sha for c in commits]})

        elif action == "init_repo_if_empty":
            repo_obj = g.get_user().get_repo(repo)
            try:
                _ = repo_obj.get_branch(repo_obj.default_branch)
                return jsonify({"message": "Repo already initialized."})
            except:
                readme_content = "# Initial Commit\n\nThis repo was initialized via API."
                blob = repo_obj.create_git_blob(readme_content, "utf-8")

                tree = repo_obj.create_git_tree([{
                    "path": "README.md",
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob.sha
                }], base_tree=None)

                commit = repo_obj.create_git_commit("Initial commit", tree, [])

                repo_obj.create_git_ref(ref='refs/heads/main', sha=commit.sha)
                repo_obj.edit(default_branch="main")

                return jsonify({"message": "Repo initialized with first commit on 'main'"})

        elif action == "create_repo":
            repo_name = data.get("repo")
            private = data.get("private", True)
            template = data.get("template", None)

            user = g.get_user()
            new_repo = user.create_repo(repo_name, private=private)

            readme_content = f"# {repo_name}\n\nCreated via API"
            blob = new_repo.create_git_blob(readme_content, "utf-8")
            tree = new_repo.create_git_tree([{
                "path": "README.md",
                "mode": "100644",
                "type": "blob",
                "sha": blob.sha
            }], base_tree=None)
            commit = new_repo.create_git_commit("Initial commit", tree, [])
            new_repo.create_git_ref(ref='refs/heads/main', sha=commit.sha)
            new_repo.edit(default_branch="main")

            if template:
                template_path = os.path.join("templates", "menu", template)
                if os.path.exists(template_path):
                    for root, _, files in os.walk(template_path):
                        for filename in files:
                            full_path = os.path.join(root, filename)
                            with open(full_path, "r", encoding="utf-8") as f:
                                file_content = f.read()

                            relative_path = os.path.relpath(full_path, template_path).replace("\\", "/")
                            try:
                                existing_file = new_repo.get_contents(relative_path, ref="main")
                                new_repo.update_file(
                                    existing_file.path,
                                    f"Update {relative_path}",
                                    file_content,
                                    existing_file.sha,
                                    branch="main"
                                )
                            except:
                                try:
                                    new_repo.create_file(
                                        relative_path,
                                        f"Add {relative_path}",
                                        file_content,
                                        branch="main"
                                    )
                                except Exception as e:
                                    print(f"⚠️ خطأ أثناء رفع {relative_path}: {e}")

            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "create_repo",
                "repo": repo_name,
                "template": template,
                "status": "success"
            }
            os.makedirs("data", exist_ok=True)
            log_path = os.path.join("data", "logs.json")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []
            logs.append(log_entry)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)

            return jsonify({"message": f"Repo '{repo_name}' created and initialized."})

        return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/docs")
def serve_docs():
    return send_from_directory("docs", "index.html")
