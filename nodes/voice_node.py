import os
import datetime
from nodes.base_node import BaseNode
from agents.voice_agent import VoiceAgent

class VoiceNode(BaseNode):
    def execute(self) -> bool:
        self.log_start()
        try:
            # 1. ვიღებთ ტექსტს
            text = self.get_input("text")
            if not text: raise ValueError("ტექსტი არ არის მიღებული")

            # 2. მზადდება გამოსასვლელი გზა
            os.makedirs("./output", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            output_path = f"./output/voice_{timestamp}.mp3"

            # 3. ვუშვებთ აგენტს
            agent = VoiceAgent(self.vault)
            result_path = agent.execute(text, output_path)

            # 4. ვინახავთ შედეგს
            self.set_output("audio_path", result_path)
            self.log_success()
            return True
        except Exception as e:
            self.log_error(str(e))
            return False
