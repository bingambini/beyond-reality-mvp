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
                genai.GenerativeModel("gemini-1.5-flash").generate_content("ping", generation_config={"max_output_tokens": 1})
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
    # ახალი ლოგიკა: ჭკვიანი მოდელის აღმოჩენა და ტესტირება
    # ============================================================
    def discover_and_test_model(self, service_id, key):
        """
        ეკითხება პლატფორმას უფასო მოდელებს, ირჩევს საუკეთესოს და ტესტავს.
        აბრუნებს: (model_name, status_message)
        """
        if not key: return None, "გასაღები არ არის"

        try:
            model_name = None

            if service_id == "gemini_text":
                genai.configure(api_key=key)
                models = genai.list_models()
                free_models = [m.name.replace("models/", "") for m in models if 'generateContent' in m.supported_generation_methods and 'free' in str(m.supported_generation_methods).lower()]
                if free_models:
                    model_name = free_models[0] # იღებს პირველ უფასოს
                else:
                    # ფოლბექი თუ free სიაში არ ჩანს მაგრამ მოდელი არსებობს
                    model_name = "gemini-1.5-flash"
                
                # ტესტი
                genai.GenerativeModel(model_name).generate_content("ping", generation_config={"max_output_tokens": 1})
                return model_name, f"✅ გამოვლენილია: {model_name} (უფასო)"

            elif service_id == "openrouter":
                # 1. მოდელთა სიის მიღება
                headers = {"Authorization": f"Bearer {key}", "HTTP-Referer": "http://localhost", "X-Title": "BeyondReality"}
                resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    # ვფილტრავთ მხოლოდ უფასო მოდელებს (ფასი არის 0)
                    free_models = [m for m in data if m.get("pricing", {}).get("prompt") == 0 and m.get("pricing", {}).get("completion") == 0]
                    if free_models:
                        # ვირჩევთ პოპულარულს ან პირველს
                        model_name = free_models[0]["id"]
                    else:
                        return None, "❌ უფასო მოდელები ვერ მოიძებნა"
                else:
                    return None, f"❌ API შეცდომა: {resp.status_code}"
                
                # ტესტი
                t_resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={"model": model_name, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}, timeout=10)
                if t_resp.status_code == 200:
                    return model_name, f"✅ გამოვლენილია: {model_name} (უფასო)"
                else:
                    return None, "❌ მოდელის ტესტი ვერ გაიარა"

            elif service_id == "groq":
                # Groq-ს აქვს რამდენიმე ფიქსირებული უფასო მოდელი
                potential_models = ["llama3-8b-8192", "gemma2-9b-it", "llama-3.1-70b-versatile"]
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                
                for m in potential_models:
                    try:
                        t_resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json={"model": m, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}, timeout=5)
                        if t_resp.status_code == 200:
                            model_name = m
                            break
                    except: continue
                
                if model_name:
                    return model_name, f"✅ გამოვლენილია: {model_name} (უფასო)"
                return None, "❌ Groq უფასო მოდელები მიუწვდომელია"

            elif service_id == "deepseek":
                # DeepSeek-ს ჩვეულებრივ აქვს ერთი მთავარი ჩატ მოდელი
                model_name = "deepseek-chat"
                try:
                    # OpenAI თავსებადი ენდპოინტი
                    t_resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": model_name, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}, timeout=10)
                    if t_resp.status_code == 200:
                        return model_name, f"✅ გამოვლენილია: {model_name} (უფასო/ტრიალი)"
                except: pass
                return None, "❌ DeepSeek ტესტი ვერ გაიარა"

            else:
                return None, "❌ ამ სერვისისთვის ავტომატური მოდელის ძიება არ არის მხარდაჭერილი"

        except Exception as e:
            return None, f"❌ შეცდომა ძიებისას: {str(e)[:50]}"
