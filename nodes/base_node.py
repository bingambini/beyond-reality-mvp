from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseNode(ABC):
    """ბაზის კლასი ყველა ნოდისთვის"""
    
    def __init__(self, node_id: str, config: Dict, logger):
        self.node_id = node_id
        self.config = config
        self.logger = logger
        self.inputs = {}
        self.outputs = {}
    
    @abstractmethod
    def execute(self) -> bool:
        """ნოდის მთავარი ლოგიკა. აბრუნებს წარმატებას/ჩავარდნას"""
        pass
    
    def set_input(self, key: str, value: Any):
        """აყენებს შეყვანის მნიშვნელობას"""
        self.inputs[key] = value
        self.logger.add(self.node_id, f"📥 Input: {key} = {str(value)[:50]}...", indent=1)
    
    def set_output(self, key: str, value: Any):
        """აყენებს გამოტანის მნიშვნელობას"""
        self.outputs[key] = value
        self.logger.add(self.node_id, f"📤 Output: {key} = {str(value)[:50]}...", indent=1)
    
    def get_input(self, key: str, default=None) -> Any:
        """იღებს შეყვანის მნიშვნელობას"""
        return self.inputs.get(key, default)
    
    def get_output(self, key: str, default=None) -> Any:
        """იღებს გამოტანის მნიშვნელობას"""
        return self.outputs.get(key, default)
    
    def log_start(self):
        self.logger.add(self.node_id, f"🚀 დაიწყო: {self.config.get('label', self.node_id)}", "start")
    
    def log_success(self):
        self.logger.add(self.node_id, f"✅ წარმატებით დასრულდა", "success")
    
    def log_error(self, message: str):
        self.logger.add(self.node_id, f"❌ შეცდომა: {message}", "error")
