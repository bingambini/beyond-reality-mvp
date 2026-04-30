import asyncio
import edge_tts
import os

class VoiceAgent:
    """აგენტი, რომელიც ქმნის ხმოვან ნარაციას Edge-TTS-ით"""
    
    def __init__(self, vault):
        self.vault = vault # აგენტს სჭირდება vault, თუმცა Edge-TTS-ს არ სჭირდება API გასაღები

    def execute(self, text: str, output_path: str) -> str:
        """ქმნის აუდიო ფაილს და აბრუნებს მის გზას"""
        voices = ["ka-GE-NinoNeural", "ka-GE-GiorgiNeural"]
        
        for voice in voices:
            try:
                # ასინქრონული შესრულება
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                communicate = edge_tts.Communicate(text, voice)
                loop.run_until_complete(communicate.save(output_path))
                
                # ვამოწმებთ ფაილის ზომას
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            except Exception as e:
                print(f"[VoiceAgent] {voice} ვერ იმუშავა: {e}")
                continue
            finally:
                loop.close()
                
        raise Exception("ხმის გენერაცია ვერ მოხერხდა (ყველა ხმა ჩავარდა)")
