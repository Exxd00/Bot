from flask import Flask, request, jsonify, render_template_string
import requests
import os
import base64

app = Flask(__name__)

# إعدادات المستودع
GITHUB_TOKEN = os.getenv("GH_TOKEN")  # أو ضع التوكين هنا مباشرة
REPO = "your-username/your-repo"      # مثل: "Exxd00/Bot"
BRANCH = "main"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

html_template = """
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Upload to GitHub via API</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0e1a2b; color: #ffffff; display: flex; flex-direction: column; align-items: center; padding: 40px; }
        textarea { width: 500px; height: 200px; margin-bottom: 20px; padding: 10px; border-radius: 8px; border: none; resize: vertical; }
        button { padding: 12px 20px; font-size: 16px; background-color: #4dd0e1; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
        #status { margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Upload File to GitHub</h1>
    <textarea id="fileContent">&lt;h1&gt;Hello from the browser!&lt;/h1&gt;</textarea>
    <button onclick="uploadFile()">Upload index.html</button>
    <div id="status"></div>
    <script>
        async function uploadFile() {
            const content = document.getElementById('fileContent').value;
            const response = await fetch('/api/push-to-github', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: 'index.html', content })
            });
            const result = await response.json();
            const status = document.getElementById('status');
            if (response.ok) {
                status.innerText = `✅ File uploaded: ${result.file}`;
                status.style.color = 'lightgreen';
            } else {
                status.innerText = `❌ Error: ${result.error?.message || 'Unknown error'}`;
                status.style.color = 'red';
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def ui():
    return render_template_string(html_template)

@app.route("/api/push-to-github", methods=["POST"])
def push_to_github():
    data = request.get_json()
    filename = data.get("filename")
    content = data.get("content")

    if not filename or not content:
        return jsonify({"error": "Missing filename or content"}), 400

    encoded_content = base64.b64encode(content.encode()).decode()
    github_url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    r = requests.get(github_url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    payload = {
        "message": f"Upload {filename} via Web UI",
        "content": encoded_content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(github_url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        return jsonify({"status": "success", "file": filename}), 200
    else:
        return jsonify({"error": response.json()}), response.status_code

if __name__ == "__main__":
    app.run(debug=True)
