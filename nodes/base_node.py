from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseNode(ABC):
    def __init__(self, node_id: str, config: Dict, logger, vault):
        self.node_id = node_id
        self.config = config
        self.logger = logger
        self.vault = vault
        self.inputs = {}
        self.outputs = {}

    def _safe_log(self, msg, level="info", indent=0):
        """ლოგირება მხოლოდ მაშინ, თუ logger მინიჭებულია"""
        if self.logger and hasattr(self.logger, 'add'):
            self.logger.add(self.node_id, msg, level, indent)

    @abstractmethod
    def execute(self) -> bool:
        pass

    def set_input(self, key: str, value: Any):
        self.inputs[key] = value
        self._safe_log(f"📥 Input: {key} = {str(value)[:50]}...", indent=1)

    def get_input(self, key: str, default=None) -> Any:
        return self.inputs.get(key, default)

    def set_output(self, key: str, value: Any):
        self.outputs[key] = value
        self._safe_log(f"📤 Output: {key} = {str(value)[:50]}...", indent=1)

    def log_start(self):
        self._safe_log(f"🚀 დაიწყო: {self.config.get('label', self.node_id)}", "start")

    def log_success(self):
        self._safe_log(f"✅ წარმატებით დასრულდა", "success")

    def log_error(self, message: str):
        self._safe_log(f"❌ შეცდომა: {message}", "error")
