import os
import requests
import base64

# إعداداتك
GITHUB_TOKEN = os.getenv("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")  # أو ضع التوكين مباشرة كنص
REPO = "ُExxd00/Bot"      # مثال: Exxd00/Bot
BRANCH = "main"
FILES_TO_UPLOAD = {
    "index.html": "index.html",
    "style.css": "style.css",
    "update_content.py": "update_content.py"
}

# ترويسة المصادقة
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

for local_path, github_path in FILES_TO_UPLOAD.items():
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        continue

    # تحويل المحتوى إلى base64
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    # الحصول على SHA إن وُجد
    sha = None
    sha_url = f"https://api.github.com/repos/{REPO}/contents/{github_path}"
    r = requests.get(sha_url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")

    # رفع الملف
    upload_url = sha_url
    data = {
        "message": f"Auto upload {github_path}",
        "content": content,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha

    res = requests.put(upload_url, headers=headers, json=data)
    if res.status_code in [200, 201]:
        print(f"✅ Uploaded: {github_path}")
    else:
        print(f"❌ Failed to upload {github_path}: {res.status_code}")
        print(res.json())
