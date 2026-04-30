from nodes.base_node import BaseNode
from agents.storage_agent import StorageAgent

class StorageNode(BaseNode):
    def execute(self) -> bool:
        self.log_start()
        try:
            vid_path = self.get_input("video_path")
            if not vid_path:
                raise ValueError("ვიდეოს გზა არ არის მიღებული")
            
            agent = StorageAgent(self.vault)
            meta = agent.execute(vid_path)
            
            self.set_output("metadata", meta)
            self.log_success()
            return True
        except Exception as e:
            self.log_error(str(e))
            return False
