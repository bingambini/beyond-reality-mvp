from nodes.base_node import BaseNode
from vault_system import VaultManager
import google.generativeai as genai
import requests

class ThemeNode(BaseNode):
    def execute(self) -> bool:
        self.log_start()
        
        vault = VaultManager()  # ან გადაეცე კონსტრუქტორში
        providers = self.config.get("providers", [])
        prompt_template = self.config.get("prompt_template", "")
        
        for service_id in providers:
            key = vault.get_key(service_id, 0)
            if not key:
                self.logger.add(self.node_id, f"⚠️ {service_id}: გასაღები არ არის", "warning")
                continue
            
            self.logger.add(self.node_id, f"🔄 ვცდილობ {service_id}...", indent=1)
            
            try:
                if service_id == "gemini_text":
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    result = model.generate_content(prompt_template, generation_config={"max_output_tokens": 500})
                    theme = result.text.strip()
                elif service_id == "groq":
                    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                       headers=headers, 
                                       json={"model": "llama-3.1-8b-instant", 
                                             "messages": [{"role": "user", "content": prompt_template}], 
                                             "max_tokens": 500}, 
                                       timeout=20)
                    if resp.status_code == 200:
                        theme = resp.json()["choices"][0]["message"]["content"].strip()
                    else:
                        continue
                # ... სხვა პროვაიდერები
                
                # ტექსტის გასუფთავება
                theme = self._clean_text(theme)
                self.set_output("theme", theme)
                self.log_success()
                return True
                
            except Exception as e:
                self.logger.add(self.node_id, f"❌ {service_id} შეცდომა: {str(e)[:40]}", "error")
                continue
        
        self.log_error("ყველა პროვაიდერი ჩავარდა")
        return False
    
    def _clean_text(self, text: str) -> str:
        """ასრულებს წინადადებას თუ წყდება"""
        text = text.strip().replace('"', '')
        if text and text[-1] not in ['.', '!', '?', '…']:
            last_dot = text.rfind('.')
            if last_dot > len(text) // 2:
                return text[:last_dot+1]
            return text + "."
        return text
