import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant generating updated welcome text for a website."},
        {"role": "user", "content": "Generate a new welcome heading for an AI assistant website. Keep it short and friendly."}
    ]
)

new_text = response['choices'][0]['message']['content'].strip()

with open("index.html", "r+", encoding="utf-8") as file:
    content = file.read()
    if "Welcome to the AI Assistant" in content:
        content = content.replace("Welcome to the AI Assistant", new_text)
        file.seek(0)
        file.write(content)
        file.truncate()
    else:
        print("Target text not found.")
