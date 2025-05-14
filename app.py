from flask import Flask, request, jsonify
import requests
import openai
import os

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY", "super-secret-key-123")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-...")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "ghp-...")

openai.api_key = OPENAI_API_KEY

def fetch_commits_from_github(repo, username="Exxd00"):
    url = f"https://api.github.com/repos/{username}/{repo}/commits"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commits = response.json()
        return [
            {
                "message": c["commit"]["message"],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"]
            }
            for c in commits[:5]
        ]
    else:
        return {"error": "فشل في جلب الكوميتات"}

@app.route("/run-action", methods=["POST"])
def run_action():
    auth = request.headers.get("x-api-key")
    if auth != API_KEY:
        return jsonify({"error": "API Key غير صحيح"}), 403

    data = request.json
    action = data.get("action")

    if action == "fetch_commits":
        repo = data.get("repo")
        result = fetch_commits_from_github(repo)

        prompt = f"هذه هي آخر الكوميتات في مشروع {repo} من GitHub:\n{result}\nحلل النشاط وقدّم ملخصًا."
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        reply = gpt_response["choices"][0]["message"]["content"]
        return jsonify({"result": result, "gpt_analysis": reply})

    return jsonify({"error": "أمر غير معروف"}), 400

@app.route("/", methods=["GET"])
def index():
    return "✅ الوسيط يعمل ومتصِل بـ GPT و GitHub."

if __name__ == "__main__":
    app.run(port=5000)
