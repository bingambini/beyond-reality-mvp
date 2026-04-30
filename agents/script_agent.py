import google.generativeai as genai
import requests

class ScriptAgent:
    """აგენტი, რომელიც წერს მიკრო-ისტორიას"""
    
    def __init__(self, vault):
        self.vault = vault

    def execute(self, theme_context: str) -> str:
        prompt = f"""
        დაწერე ემოციური მიკრო-ისტორია (2-4 წინადადება) ქართულად.
        თემა: '{theme_context}'
        სტილი: მელანქოლიური, კინემატოგრაფიული. 
        პირდაპირ შედი სცენაში, არ დაიწყო 'აი' ან 'წარმოიდგინე'.
        """
        
        # ჯერ ვცდილობთ Gemini-ს
        key = self.vault.get_key("gemini_text", 0)
        if key:
            try:
                return self._call_gemini(key, prompt)
            except: pass

        # თუ Gemini ვერ მუშაობს, ვცდილობთ Groq-ს
        key_groq = self.vault.get_key("groq", 0)
        if key_groq:
            try:
                return self._call_groq(key_groq, prompt)
            except: pass

        raise Exception("სცენარის წერა ვერ მოხერხდა (ყველა პროვაიდერი ჩავარდა)")

    def _call_gemini(self, key, prompt):
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash") # ან auto-detect
        resp = model.generate_content(prompt, generation_config={"max_output_tokens": 300})
        return resp.text.strip().replace('"', '')

    def _call_groq(self, key, prompt):
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300
        }
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        raise Exception(f"Groq Script Error: {resp.status_code}")
