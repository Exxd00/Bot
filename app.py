import os
from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv
import base64

# تحميل متغيرات البيئة
load_dotenv()

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GH_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "Exxd00")

g = Github(GH_TOKEN)

@app.route("/run-action", methods=["POST"])
def run_action():
    data = request.json
    action = data.get("action")
    repo_name = data.get("repo")
    file_path = data.get("file_path")
    new_content = data.get("new_content")

    if not action or not repo_name:
        return jsonify({"error": "الرجاء إرسال action و repo"}), 400

    try:
        repo = g.get_user().get_repo(repo_name)

        if action == "list_files":
            contents = repo.get_contents("")
            return jsonify({"files": [c.name for c in contents]})

        elif action == "fetch_commits":
            commits = repo.get_commits()[:5]
            return jsonify({
                "commits": [
                    {
                        "message": c.commit.message,
                        "author": c.commit.author.name,
                        "date": c.commit.author.date.isoformat(),
                    }
                    for c in commits
                ]
            })

        elif action == "get_file":
            if not file_path:
                return jsonify({"error": "file_path مطلوب"}), 400
            file_content = repo.get_contents(file_path)
            decoded = base64.b64decode(file_content.content).decode("utf-8")
            return jsonify({"content": decoded})

        elif action == "update_file":
            if not file_path or new_content is None:
                return jsonify({"error": "file_path و new_content مطلوبان"}), 400
            file = repo.get_contents(file_path)
            repo.update_file(
                path=file.path,
                message="تحديث الملف عبر API",
                content=new_content,
                sha=file.sha
            )
            return jsonify({"message": "تم تحديث الملف بنجاح"})

        else:
            return jsonify({"error": f"الإجراء '{action}' غير مدعوم"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
