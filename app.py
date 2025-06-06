import os
import requests
from flask import Flask, request, jsonify
from github import Github
from openai import OpenAI  # ✅ واجهة OpenAI الحديثة

app = Flask(__name__)

# مفاتيح البيئة
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GH_TOKEN")
GITHUB_USERNAME = "Exxd00"

# تحقق من وجود المفاتيح
if not GH_TOKEN:
    raise EnvironmentError("❌ لم يتم العثور على GH_TOKEN")
if not OPENAI_API_KEY:
    raise EnvironmentError("❌ لم يتم العثور على OPENAI_API_KEY")

# تهيئة GitHub و OpenAI
g = Github(GH_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.json
    action = data.get("action")

    try:
        if action == "fetch_commits":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            commits = repo.get_commits()[:5]
            result = []
            for commit in commits:
                result.append({
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat()
                })
            return jsonify(result)

        elif action == "list_files":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            contents = repo.get_contents("")
            file_list = []
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    file_list.append(file_content.path)
            return jsonify({"files": file_list})

        elif action == "get_file":
            repo_name = data.get("repo")
            file_path = data.get("file_path")
            repo = g.get_user().get_repo(repo_name)
            file_content = repo.get_contents(file_path)
            decoded_content = file_content.decoded_content.decode("utf-8")
            return jsonify({"path": file_path, "content": decoded_content})

        else:
            return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ لتشغيل الخادم على Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
