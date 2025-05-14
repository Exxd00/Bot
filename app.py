from flask import Flask, request, jsonify
import os
import openai
import requests
from github import Github

app = Flask(__name__)

# التأكد من وجود مفاتيح البيئة
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GH_TOKEN")
GITHUB_USERNAME = "Exxd00"

if not GH_TOKEN:
    raise EnvironmentError("❌ لم يتم العثور على GH_TOKEN في المتغيرات البيئية")
if not OPENAI_API_KEY:
    raise EnvironmentError("❌ لم يتم العثور على OPENAI_API_KEY في المتغيرات البيئية")

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

        # باقي الأوامر (كما هي في ملفك السابق)
        # create_repo, update_file, create_branch, etc...

        else:
            return jsonify({"error": "Invalid action."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "✅ الوسيط يعمل ومتصِل بـ GPT و GitHub."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
