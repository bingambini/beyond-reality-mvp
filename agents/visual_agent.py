import requests
import io
from PIL import Image
import random

class VisualAgent:
    """აგენტი, რომელიც ქმნის სურათს Pollinations-ით (უფასო, გასაღების გარეშე)"""
    
    def __init__(self, vault):
        self.vault = vault

    def execute(self, prompt_context: str) -> Image.Image:
        """ქმნის სურათს და აბრუნებს PIL ობიექტს"""
        
        # ვქმნით პრომპტს თემის მიხედვით
        prompt = f"Cinematic vertical shot (9:16). {prompt_context}. Moody, emotional, high detail, 8k."
        
        # Pollinations URL
        seed = random.randint(1, 99999)
        width, height = 1080, 1920
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width={width}&height={height}&nologo=true&seed={seed}&model=flux"

        # 3 ცდა მაღალი timeout-ით
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=120) # 2 წუთი
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content)).convert('RGB')
                    return img
            except Exception as e:
                print(f"[VisualAgent] ცდა {attempt+1} ჩავარდა: {e}")
                
        raise Exception("სურათის გენერაცია ვერ მოხერხდა (Pollinations)")
