from flask import Flask, request, jsonify
import os
import openai
import requests
from github import Github

app = Flask(__name__)

# إعداد المفاتيح
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GH_TOKEN")
GITHUB_USERNAME = "Exxd00"

# تهيئة الاتصال بـ OpenAI و GitHub
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
            result = []
            for commit in commits:
                result.append({
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.strftime("%Y-%m-%d")
                })

            prompt = f"حلل لي التعديلات التالية:\n" + "\n".join([c["message"] for c in result])
            gpt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return jsonify({"result": result, "gpt_analysis": gpt_response["choices"][0]["message"]["content"]})

        elif action == "create_repo":
            repo_name = data.get("repo")
            template = data.get("template", "landing_page")
            user = g.get_user()
            for repo in user.get_repos():
                if repo.name == repo_name:
                    return jsonify({"error": "المستودع موجود مسبقًا."}), 400

            repo = user.create_repo(name=repo_name, private=False)

            if template == "landing_page":
                content = {
                    "index.html": "<html><body><h1>Landing Page</h1></body></html>",
                    "style.css": "body { font-family: sans-serif; }"
                }
            elif template == "restaurant_menu":
                content = {
                    "index.html": "<html><body><h1>Menu</h1><ul><li>Pizza</li><li>Burger</li></ul></body></html>",
                    "style.css": "ul { list-style: none; }"
                }
            else:
                return jsonify({"error": "Invalid template name"}), 400

            for filename, filecontent in content.items():
                repo.create_file(filename, f"add {filename}", filecontent)

            repo.edit(has_pages=True)
            repo.update_branch_protection("main", required_approving_review_count=0)

            return jsonify({"status": "repository_created", "url": repo.html_url})

        elif action == "update_file":
            repo_name = data.get("repo")
            filename = data.get("file")
            new_content = data.get("content")
            commit_message = data.get("message", "تحديث الملف")
            repo = g.get_user().get_repo(repo_name)
            contents = repo.get_contents(filename)
            repo.update_file(contents.path, commit_message, new_content, contents.sha)
            return jsonify({"status": "file_updated", "file": filename})

        elif action == "create_branch":
            repo_name = data.get("repo")
            new_branch = data.get("branch")
            repo = g.get_user().get_repo(repo_name)
            source = repo.get_branch("main")
            repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=source.commit.sha)
            return jsonify({"status": "branch_created", "branch": new_branch})

        elif action == "create_issue":
            repo_name = data.get("repo")
            title = data.get("title")
            body = data.get("body", "")
            repo = g.get_user().get_repo(repo_name)
            issue = repo.create_issue(title=title, body=body)
            return jsonify({"status": "issue_created", "issue_url": issue.html_url})

        elif action == "list_files":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            contents = repo.get_contents("")
            files = [c.path for c in contents]
            return jsonify({"files": files})

        elif action == "delete_repo":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            repo.delete()
            return jsonify({"status": "repository_deleted", "repo": repo_name})

        elif action == "get_repo_info":
            repo_name = data.get("repo")
            repo = g.get_user().get_repo(repo_name)
            info = {
                "name": repo.name,
                "description": repo.description,
                "private": repo.private,
                "url": repo.html_url
            }
            return jsonify(info)

        else:
            return jsonify({"error": "Invalid action."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "✅ الوسيط يعمل ومتصِل بـ GPT و GitHub."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
