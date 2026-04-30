import google.generativeai as genai
import requests
import json

class ThemeAgent:
    """აგენტი, რომელიც ქმნის კინემატოგრაფიულ თემას"""
    
    def __init__(self, vault):
        self.vault = vault

    def execute(self) -> str:
        providers = ["gemini_text", "groq", "openrouter"] # რიგითი მნიშვნელობით
        
        prompt = """
        შექმენი უნიკალური კინემატოგრაფიული თემა 9:16 ვიდეოსთვის.
        მიმართულება: "მელანქოლიური, რომანტიკული, ქალაქური ან ბუნებრივი სცენა".
        
        მოითხოვნები:
        1. აღწერე ვიზუალი (განათება, კომპოზიცია, ფერები).
        2. დაამატე ემოციური კონტექსტი.
        3. იყავი ლაკონიური! მაქსიმუმ 5-8 წინადადება.
        4. ენა: ქართული.
        """

        for provider in providers:
            key = self.vault.get_key(provider, 0)
            if not key: continue
            
            try:
                if provider == "gemini_text":
                    return self._call_gemini(key, prompt)
                elif provider == "groq":
                    return self._call_groq(key, prompt)
                # OpenRouter-ის ლოგიკა მოგვიანებით დაემატება
            except Exception as e:
                print(f"[ThemeAgent] {provider} შეცდომა: {e}")
                continue
                
        raise Exception("ვერცერთმა პროვაიდერმა იმუშავა")

    def _call_gemini(self, key, prompt):
        genai.configure(api_key=key)
        # ვპოულობთ ხელმისაწვდომ მოდელს
        models = genai.list_models()
        candidates = [m.name.replace("models/", "") for m in models if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in candidates if 'pro' in m or 'flash' in m), candidates[0])
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, generation_config={"max_output_tokens": 500})
        return self._clean_text(response.text)

    def _call_groq(self, key, prompt):
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant", # ან სხვა ხელმისაწვდომი
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return self._clean_text(resp.json()["choices"][0]["message"]["content"])
        raise Exception(f"Groq Error: {resp.status_code}")

    def _clean_text(self, text):
        text = text.strip().replace('"', '')
        # თუ ტექსტი წყდება, ვასრულებთ
        if text and text[-1] not in ['.', '!', '?']:
            last_dot = text.rfind('.')
            if last_dot > -1: return text[:last_dot+1]
            return text + "."
        return text
