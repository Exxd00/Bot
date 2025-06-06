import os
import openai
import requests
from github import Github
from flask import Flask, request, jsonify

app = Flask(__name__)

# إعداد المتغيرات
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = "Exxd00"

# إعداد الاتصال بـ GitHub و OpenAI
g = Github(GH_TOKEN)
openai.api_key = OPENAI_API_KEY

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.json
    action = data.get("action")

    try:
        if action == "fetch_commits":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            commits = repo.get_commits()[:5]
            result = [{"message": c.commit.message, "author": c.commit.author.name} for c in commits]

        elif action == "get_repo_info":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            result = {
                "name": repo.name,
                "description": repo.description,
                "private": repo.private,
                "default_branch": repo.default_branch
            }

        elif action == "list_files":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            contents = repo.get_contents("")
            result = []

            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    result.append(file_content.path)

        else:
            return jsonify({"error": f"Invalid action: {action}"}), 400

        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
