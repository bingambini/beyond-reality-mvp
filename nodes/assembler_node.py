import os
import datetime
from nodes.base_node import BaseNode
from agents.assembler_agent import AssemblerAgent

class AssemblerNode(BaseNode):
    def execute(self) -> bool:
        self.log_start()
        try:
            img_path = self.get_input("image_path")
            aud_path = self.get_input("audio_path")
            if not img_path or not aud_path:
                raise ValueError("სურათი ან ხმა არ არის მიღებული")

            os.makedirs("./output", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            output_path = f"./output/video_{timestamp}.mp4"

            agent = AssemblerAgent(self.vault)
            result = agent.execute(img_path, aud_path, output_path)

            self.set_output("video_path", result)
            self.log_success()
            return True
        except Exception as e:
            self.log_error(str(e))
            return False
