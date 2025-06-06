import os
from flask import Flask, request, jsonify
from github import Github
import openai

app = Flask(__name__)

# إعداد المفاتيح
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = "Exxd00"  # غيّره لاسم المستخدم الخاص بك

g = Github(GH_TOKEN)
openai.api_key = OPENAI_API_KEY


@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.json
    action = data.get("action")
    repo_name = data.get("repo")

    try:
        if action == "fetch_commits":
            repo = g.get_user().get_repo(repo_name)
            commits = repo.get_commits()[:5]
            result = [f"{commit.commit.author.name}: {commit.commit.message}" for commit in commits]
            return jsonify({"result": result})

        elif action == "get_file":
            file_path = data.get("file_path")
            repo = g.get_user().get_repo(repo_name)
            file_content = repo.get_contents(file_path)
            return jsonify({"file_path": file_path, "content": file_content.decoded_content.decode()})

        elif action == "update_file":
            file_path = data.get("file_path")
            new_content = data.get("content")
            commit_msg = data.get("commit_message", "update via API")
            repo = g.get_user().get_repo(repo_name)
            file = repo.get_contents(file_path)
            repo.update_file(file.path, commit_msg, new_content, file.sha)
            return jsonify({"message": f"{file_path} updated successfully"})

        elif action == "create_repo":
            repo_name = data.get("repo")
            description = data.get("description", "")
            private = data.get("private", False)
            repo = g.get_user().create_repo(name=repo_name, description=description, private=private)
            return jsonify({"message": f"Repo '{repo_name}' created successfully."})

        elif action == "list_files":
            repo = g.get_user().get_repo(repo_name)
            contents = repo.get_contents("")
            files = [{"name": file.name, "path": file.path, "type": file.type} for file in contents]
            return jsonify({"files": files})

        elif action == "get_repo_info":
            repo = g.get_user().get_repo(repo_name)
            info = {
                "name": repo.name,
                "description": repo.description,
                "url": repo.html_url,
                "private": repo.private,
                "default_branch": repo.default_branch,
                "created_at": str(repo.created_at),
                "updated_at": str(repo.updated_at)
            }
            return jsonify(info)

        else:
            return jsonify({"error": f"Unsupported action: {action}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
