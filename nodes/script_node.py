from nodes.base_node import BaseNode
from agents.script_agent import ScriptAgent

class ScriptNode(BaseNode):
    def execute(self) -> bool:
        self.log_start()
        try:
            # 1. ვიღებთ თემას წინა ნოდიდან (Input)
            theme = self.get_input("theme")
            if not theme:
                raise ValueError("თემა არ არის მიღებული (Input missing)")
            
            # 2. ვუშვებთ აგენტს
            agent = ScriptAgent(self.vault)
            result = agent.execute(theme)
            
            # 3. ვინახავთ შედეგს (Output)
            self.set_output("script", result)
            self.log_success()
            return True
        except Exception as e:
            self.log_error(str(e))
            return False
