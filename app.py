import os
from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعداد Flask
app = Flask(__name__)

# متغيرات البيئة
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GH_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "Exxd00")

# تهيئة GitHub
g = Github(GH_TOKEN)

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.json
    action = data.get("action")
    repo_name = data.get("repo")

    try:
        if not action or not repo_name:
            return jsonify({"error": "يرجى إرسال action و repo"}), 400

        repo = g.get_user().get_repo(repo_name)

        if action == "list_files":
            contents = repo.get_contents("")
            files = [file.name for file in contents]
            return jsonify({"files": files})

        elif action == "fetch_commits":
            commits = repo.get_commits()[:5]
            result = [
                {
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                }
                for commit in commits
            ]
            return jsonify({"commits": result})

        else:
            return jsonify({"error": f"الإجراء '{action}' غير مدعوم"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
