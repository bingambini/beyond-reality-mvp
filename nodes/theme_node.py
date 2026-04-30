from nodes.base_node import BaseNode
from agents.theme_agent import ThemeAgent

class ThemeNode(BaseNode):
    def execute(self) -> bool:
        self.log_start()
        try:
            # ვიყენებთ აგენტს
            agent = ThemeAgent(self.vault)
            result = agent.execute()
            
            # შედეგის შენახვა outputs-ში
            self.set_output("theme", result)
            self.log_success()
            return True
        except Exception as e:
            self.log_error(str(e))
            return False
