import json
import os
import google.generativeai as genai
import requests
import re

VAULT_FILE = "vault_config.json"

# დეფოლტ კონფიგურაცია: 5 ველი თითო კატეგორიაზე
DEFAULT_CONFIG = {
    "gemini_text": {"label": "🧠 Google Gemini (ტექსტი/AI)", "type": "key", "count": 5, "keys": [""]*5},
    "hf_image": {"label": "🎨 HuggingFace (ვიზუალი/სურათები)", "type": "key", "count": 5, "keys": [""]*5},
    "groq": {"label": "🐦 Groq (სწრაფი LLM)", "type": "key", "count": 5, "keys": [""]*5},
    "openrouter": {"label": "🌐 OpenRouter (მულტი-მოდელი)", "type": "key", "count": 5, "keys": [""]*5},
    "deepseek": {"label": "🔍 DeepSeek (AI კოდი/ტექსტი)", "type": "key", "count": 5, "keys": [""]*5},
    "github_repos": {"label": "🐙 GitHub რეპოზიტორიები (ლინკები)", "type": "link", "count": 5, "keys": [""]*5},
    "other_apis": {"label": "🔌 სხვა პლატფორმები / დამატებითი", "type": "key", "count": 5, "keys": [""]*5}
}

class VaultManager:
    def __init__(self):
        self.config = {}
        self._load_config()

    def _load_config(self):
        if os.path.exists(VAULT_FILE):
            try:
                with open(VAULT_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                # ახალი კატეგორიების ავტო-დამატება
                for k, v in DEFAULT_CONFIG.items():
                    if k not in self.config: self.config[k] = v
            except:
                self.config = DEFAULT_CONFIG
        else:
            self.config = DEFAULT_CONFIG

    def save_config(self):
        try:
            with open(VAULT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except: return False

    def get_key(self, service_id, index=0):
        try: return self.config[service_id]["keys"][index]
        except: return ""

    def update_key(self, service_id, index, value):
        if service_id in self.config:
            self.config[service_id]["keys"][index] = value

    def validate_key(self, service_id, key):
        if not key or not key.strip(): return False, "ველი ცარიელია"
        try:
            if service_id == "gemini_text":
                genai.configure(api_key=key)
                genai.GenerativeModel("gemini-1.5-flash").generate_content("ping", generation_config={"max_output_tokens": 1})
                return True, "✅ ვალიდური და აქტიური"
            elif service_id == "hf_image":
                resp = requests.get("https://huggingface.co/api/whoami-v2", headers={"Authorization": f"Bearer {key}"}, timeout=10)
                return (True, "✅ ვალიდური ტოკენი") if resp.status_code == 200 else (False, f"❌ შეცდომა: {resp.status_code}")
            elif service_id == "github_repos":
                return (True, "✅ ვალიდური ლინკი") if re.match(r'^https://github\.com/[\w\.-]+/[\w\.-]+/?$', key) else (False, "❌ არასწორი ფორმატი")
            else:
                # Groq, OpenRouter, DeepSeek, Other -> ბაზისური შემოწმება
                return True, "✅ ფორმატი მისაღებია / შენახულია"
        except Exception as e:
            return False, f"❌ შეცდომა: {str(e)[:40]}"
