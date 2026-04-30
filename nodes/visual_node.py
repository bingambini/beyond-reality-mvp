import os
import datetime
from nodes.base_node import BaseNode
from agents.visual_agent import VisualAgent

class VisualNode(BaseNode):
    def execute(self) -> bool:
        self.log_start()
        try:
            # 1. ვიღებთ თემას (რადგან ვიზუალი თემაზეა დამოკიდებული, არა სცენარზე)
            theme = self.get_input("prompt_context") # workflow_config.json-ში input_key არის prompt_context
            if not theme: 
                # fallback: თუ prompt_context არ არის, ვცდილობთ theme-ის აღებას
                theme = self.get_input("theme")
            if not theme: raise ValueError("კონტექსტი არ არის მიღებული")

            # 2. ვუშვებთ აგენტს
            agent = VisualAgent(self.vault)
            img_obj = agent.execute(theme)

            # 3. ვინახავთ სურათს ფაილად
            os.makedirs("./output", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            image_path = f"./output/image_{timestamp}.png"
            img_obj.save(image_path)

            # 4. ვინახავთ გზას outputs-ში
            self.set_output("image_path", image_path)
            self.log_success()
            return True
        except Exception as e:
            self.log_error(str(e))
            return False
