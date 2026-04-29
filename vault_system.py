import json
import os
import google.generativeai as genai
import requests
import re

VAULT_FILE = "vault_config.json"

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
                genai.GenerativeModel("gemini-pro").generate_content("ping", generation_config={"max_output_tokens": 1})
                return True, "✅ ვალიდური და აქტიური"
            elif service_id == "hf_image":
                resp = requests.get("https://huggingface.co/api/whoami-v2", headers={"Authorization": f"Bearer {key}"}, timeout=10)
                return (True, "✅ ვალიდური ტოკენი") if resp.status_code == 200 else (False, f"❌ HF შეცდომა: {resp.status_code}")
            elif service_id == "github_repos":
                return (True, "✅ ვალიდური ლინკი") if re.match(r'^https://github\.com/[\w\.-]+/[\w\.-]+/?$', key) else (False, "❌ არასწორი ფორმატი")
            else:
                return True, "✅ ფორმატი მისაღებია / შენახულია"
        except Exception as e:
            return False, f"❌ შეცდომა: {str(e)[:40]}"

    # ============================================================
    # ჭკვიანი მოდელის აღმოჩენა (განახლებული: პირდაპირი ტესტირება)
    # ============================================================
    def discover_and_test_model(self, service_id, key):
        if not key: return None, "გასაღები არ არის"

        try:
            if service_id == "gemini_text":
                genai.configure(api_key=key)
                models = genai.list_models()
                candidates = [m.name.replace("models/", "") for m in models if 'generateContent' in m.supported_generation_methods]
                priority = ["gemini-1.5-pro", "gemini-pro", "gemini-1.0-pro", "gemini-1.5-flash"]
                model_name = next((p for p in priority if p in candidates), candidates[0] if candidates else None)
                if not model_name: return None, "❌ ხელმისაწვდომი მოდელები ვერ მოიძებნა"
                genai.GenerativeModel(model_name).generate_content("ping", generation_config={"max_output_tokens": 1})
                return model_name, f"✅ გამოვლენილია: {model_name}"

            elif service_id == "openrouter":
                headers = {"Authorization": f"Bearer {key}", "HTTP-Referer": "http://localhost", "X-Title": "BeyondReality"}
                # ცნობილი უფასო მოდელების პირდაპირი ტესტირება (ფასების ფილტრის ნაცვლად)
                free_ids = [
                    "meta-llama/llama-3-8b-instruct:free",
                    "google/gemini-2.0-flash-exp:free",
                    "microsoft/phi-3-mini-128k-instruct:free"
                ]
                for m_id in free_ids:
                    try:
                        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={"model": m_id, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}, timeout=10)
                        if resp.status_code == 200:
                            return m_id, f"✅ გამოვლენილია: {m_id}"
                    except: pass
                return None, "❌ OpenRouter უფასო მოდელები დაბლოკილია ან ლიმიტი ამოიწურა"

            elif service_id == "groq":
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                # აქტუალური Groq უფასო მოდელები
                free_ids = ["llama-3.1-8b-instant", "llama3-8b-8192", "gemma2-9b-it"]
                for m_id in free_ids:
                    try:
                        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json={"model": m_id, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}, timeout=5)
                        if resp.status_code == 200:
                            return m_id, f"✅ გამოვლენილია: {m_id}"
                    except: pass
                return None, "❌ Groq უფასო მოდელები დაბლოკილია ან ლიმიტი ამოიწურა"

            elif service_id == "deepseek":
                try:
                    resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}, timeout=10)
                    if resp.status_code == 200: return "deepseek-chat", "✅ გამოვლენილია: deepseek-chat"
                except: pass
                return None, "❌ DeepSeek ტესტი ვერ გაიარა"

            else:
                return None, "❌ ამ სერვისისთვის ავტომატური ძიება არ არის მხარდაჭერილი"

        except Exception as e:
            return None, f"❌ შეცდომა ძიებისას: {str(e)[:50]}"
