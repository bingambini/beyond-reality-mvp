import json
import os
import google.generativeai as genai
import requests

# კონფიგურაციის ფაილი, სადაც ინახება გასაღებები
VAULT_FILE = "vault_config.json"

class VaultManager:
    def __init__(self):
        self.keys = {}
        self._load_keys()

    def _load_keys(self):
        """იტვირთებს გასაღებებს JSON ფაილიდან"""
        if os.path.exists(VAULT_FILE):
            try:
                with open(VAULT_FILE, "r", encoding="utf-8") as f:
                    self.keys = json.load(f)
            except Exception:
                self.keys = {}
        else:
            # დეფოლტ სტრუქტურა
            self.keys = {
                "gemini_text": "",
                "hf_image": ""
            }

    def save_key(self, service, key):
        """ინახავს გასაღებს და ანახლებს JSON-ს"""
        self.keys[service] = key
        try:
            with open(VAULT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.keys, f, indent=4)
            return True
        except Exception as e:
            print(f"Vault Error: {e}")
            return False

    def get_key(self, service):
        """აბრუნებს გასაღებს კონკრეტული სერვისისთვის"""
        return self.keys.get(service, "")

    def validate_and_test(self, service, key):
        """ამოწმებს: 1. არის თუ არა ცარიელი, 2. მუშაობს თუ არა API"""
        if not key:
            return False, "გასაღები ცარიელია"
        
        try:
            if service == "gemini_text":
                genai.configure(api_key=key)
                # ვცდილობთ მარტივ მოთხოვნას
                model = genai.GenerativeModel("gemini-1.5-flash")
                model.generate_content("ping", generation_config={"max_output_tokens": 1})
                return True, "✅ გასაღები ვალიდურია და აქტიურია"
            
            elif service == "hf_image":
                resp = requests.get("https://huggingface.co/api/whoami-v2", headers={"Authorization": f"Bearer {key}"}, timeout=10)
                if resp.status_code == 200:
                    return True, "✅ HF ტოკენი ვალიდურია"
                else:
                    return False, f"❌ HF შეცდომა: {resp.status_code}"
            
            return False, "უცნობი სერვისი"
            
        except Exception as e:
            return False, f"❌ შეცდომა: {str(e)[:50]}"
