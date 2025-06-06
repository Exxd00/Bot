import os
from flask import Flask, request, jsonify
from github import Github
import openai

app = Flask(__name__)

# إعداد المفاتيح
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = "Exxd00"  # اسم المستخدم الخاص بك على GitHub

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

        elif action == "analyze_repo":
            repo = g.get_user().get_repo(repo_name)
            files = repo.get_contents("")
            results = []

            for file in files:
                if file.type == "file" and file.name.endswith((".py", ".js", ".html", ".md")):
                    content = file.decoded_content.decode()
                    prompt = f"حلل لي التعديلات التالية:\n\n{content[:1500]}"
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.4,
                        max_tokens=300
                    )
                    summary = response.choices[0].message.content.strip()
                    results.append({"file": file.name, "summary": summary})

            return jsonify({"analysis": results})

        else:
            return jsonify({"error": f"Action '{action}' غير مدعوم"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
