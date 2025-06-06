import os
import openai
import requests
from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# إعداد المفاتيح
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GH_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# تهيئة الاتصال
openai.api_key = OPENAI_API_KEY
g = Github(GH_TOKEN)

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.json
    action = data.get("action")
    repo_name = data.get("repo")

    try:
        repo = g.get_user().get_repo(repo_name)

        if action == "fetch_commits":
            commits = repo.get_commits()[:5]
            result = [{"message": c.commit.message, "author": c.commit.author.name} for c in commits]
            return jsonify(result)

        elif action == "get_file":
            path = data.get("path")
            file = repo.get_contents(path)
            return jsonify({"path": path, "content": file.decoded_content.decode("utf-8")})

        elif action == "update_file":
            path = data.get("path")
            message = data.get("message", "Update file via API")
            new_content = data.get("content")
            file = repo.get_contents(path)
            updated = repo.update_file(
                path=path,
                message=message,
                content=new_content,
                sha=file.sha
            )
            return jsonify({"status": "updated", "path": path, "commit": updated["commit"].sha})

        elif action == "get_repo_info":
            info = {
                "name": repo.name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "private": repo.private
            }
            return jsonify(info)

        elif action == "analyze_file":
            path = data.get("path")
            file = repo.get_contents(path)
            content = file.decoded_content.decode("utf-8")

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "أنت مساعد ذكي يحلل ملفات البرمجة."},
                    {"role": "user", "content": f"حلل هذا الملف:\n\n{content}"}
                ]
            )
            analysis = response.choices[0].message.content
            return jsonify({"analysis": analysis})

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
