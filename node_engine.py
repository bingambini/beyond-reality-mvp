import json
from typing import Dict, List, Any
from nodes.base_node import BaseNode

class NodeEngine:
    def __init__(self, config_path: str, logger, vault):
        self.logger = logger
        self.vault = vault
        with open(config_path, "r", encoding="utf-8") as f:
            self.workflow = json.load(f)
        self.nodes: Dict[str, BaseNode] = {}
        self._load_nodes()

    def _log(self, msg, level="info", indent=0):
        """უსაფრთხო ლოგირება Engine-ისთვის"""
        if self.logger and hasattr(self.logger, 'add'):
            self.logger.add("NodeEngine", msg, level, indent)

    def _load_nodes(self):
        for node_cfg in self.workflow["nodes"]:
            node_id = node_cfg["id"]
            try:
                # დინამიური იმპორტი
                module = __import__(f"nodes.{node_id}", fromlist=[node_cfg["type"]])
                node_class = getattr(module, node_cfg["type"])
                self.nodes[node_id] = node_class(
                    node_id=node_id,
                    config=node_cfg.get("config", {}),
                    logger=self.logger, # ჯერ None-ია, მაგრამ უსაფრთხოა _safe_log-ის წყალობით
                    vault=self.vault
                )
            except Exception as e:
                self._log(f"⚠️ ნოდი {node_id} ვერ ჩაიტვირთა: {e}", "warning")

    def _get_execution_order(self) -> List[str]:
        order, visited, visiting = [], set(), set()
        def visit(n_id):
            if n_id in visiting: raise ValueError(f"წრე აღმოჩენილია: {n_id}")
            if n_id in visited: return
            visiting.add(n_id)
            for edge in self.workflow["edges"]:
                if edge["to"] == n_id: visit(edge["from"])
            visiting.remove(n_id)
            visited.add(n_id)
            order.append(n_id)
        for n in self.workflow["nodes"]: visit(n["id"])
        return order

    def execute(self) -> bool:
        self._log("🔄 ნაკადის შესრულება იწყება...", "start")
        try:
            order = self._get_execution_order()
            self._log(f"📋 თანმიმდევრობა: {' → '.join(order)}", indent=1)
            for node_id in order:
                node = self.nodes.get(node_id)
                if not node: continue
                for edge in self.workflow["edges"]:
                    if edge["to"] == node_id:
                        from_node = self.nodes.get(edge["from"])
                        if from_node and edge["output_key"] in from_node.outputs:
                            node.set_input(edge["input_key"], from_node.outputs[edge["output_key"]])
                if not node.execute():
                    self._log(f"❌ ნაკადი შეჩერდა: {node_id}", "error")
                    return False
            self._log("✅ მთლიანი ნაკადი წარმატებით დასრულდა!", "success")
            return True
        except Exception as e:
            self._log(f"❌ კრიტიკული შეცდომა: {str(e)}", "error")
            return False

    def get_mermaid_diagram(self) -> str:
        lines = ["graph LR"]
        for n in self.workflow["nodes"]:
            lines.append(f'    {n["id"].replace("_","")}["{n["label"]}"]')
        for e in self.workflow["edges"]:
            lines.append(f'    {e["from"].replace("_","")} -- "{e["label"]}" --> {e["to"].replace("_","")}')
        return "\n".join(lines)
