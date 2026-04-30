from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseNode(ABC):
    """ბაზის კლასი ყველა ნოდისთვის"""
    def __init__(self, node_id: str, config: Dict, logger, vault):
        self.node_id = node_id
        self.config = config
        self.logger = logger
        self.vault = vault
        self.inputs = {}
        self.outputs = {}

    @abstractmethod
    def execute(self) -> bool:
        """ნოდის მთავარი ლოგიკა. აბრუნებს True წარმატებისას, False-ს ჩავარდნისას"""
        pass

    def set_input(self, key: str, value: Any):
        self.inputs[key] = value
        self.logger.add(self.node_id, f"📥 Input: {key} = {str(value)[:50]}...", indent=1)

    def get_input(self, key: str, default=None) -> Any:
        return self.inputs.get(key, default)

    def set_output(self, key: str, value: Any):
        self.outputs[key] = value
        self.logger.add(self.node_id, f"📤 Output: {key} = {str(value)[:50]}...", indent=1)

    def log_start(self):
        self.logger.add(self.node_id, f"🚀 დაიწყო: {self.config.get('label', self.node_id)}", "start")

    def log_success(self):
        self.logger.add(self.node_id, f"✅ წარმატებით დასრულდა", "success")

    def log_error(self, message: str):
        self.logger.add(self.node_id, f"❌ შეცდომა: {message}", "error")
