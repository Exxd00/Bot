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

            # تحليل التعديلات باستخدام GPT
            prompt = "حلل لي التعديلات التالية:
" + "\n".join([c["message"] for c in result])
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            gpt_reply = response.choices[0].message.content
            return jsonify({"commits": result, "gpt_analysis": gpt_reply})

        elif action == "chat_with_openai":
            prompt = data.get("prompt", "اكتب شيئاً")
            completion = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return jsonify({"reply": completion.choices[0].message.content})

        else:
            return jsonify({"error": "الإجراء غير معروف"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ الخادم يعمل باستخدام OpenAI v1.0+"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
