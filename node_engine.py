import json
import os
from typing import Dict, List, Any
from nodes.base_node import BaseNode

class NodeEngine:
    """ნოდების გამშვები ძრავა"""
    def __init__(self, config_path: str, logger, vault):
        self.logger = logger
        self.vault = vault
        with open(config_path, "r", encoding="utf-8") as f:
            self.workflow = json.load(f)
        self.nodes: Dict[str, BaseNode] = {}
        self._load_nodes()

    def _load_nodes(self):
        """ტვირთავს ნოდებს workflow_config.json-დან"""
        for node_cfg in self.workflow["nodes"]:
            node_id = node_cfg["id"]
            module_name = f"nodes.{node_id}"
            try:
                module = __import__(module_name, fromlist=[node_cfg["type"]])
                node_class = getattr(module, node_cfg["type"])
                self.nodes[node_id] = node_class(
                    node_id=node_id,
                    config=node_cfg["config"],
                    logger=self.logger,
                    vault=self.vault
                )
            except Exception as e:
                self.logger.add("NodeEngine", f"⚠️ ნოდი {node_id} ვერ ჩაიტვირთა: {e}", "warning")

    def _get_execution_order(self) -> List[str]:
        """ტოპოლოგიური დალაგება (DAG)"""
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
        """ასრულებს მთელ ნაკადს"""
        self.logger.add("NodeEngine", "🔄 ნაკადის შესრულება იწყება...", "start")
        try:
            order = self._get_execution_order()
            self.logger.add("NodeEngine", f"📋 თანმიმდევრობა: {' → '.join(order)}", indent=1)
            for node_id in order:
                node = self.nodes.get(node_id)
                if not node: continue
                # ინპუტების გადაცემა
                for edge in self.workflow["edges"]:
                    if edge["to"] == node_id:
                        from_node = self.nodes.get(edge["from"])
                        if from_node and edge["output_key"] in from_node.outputs:
                            node.set_input(edge["input_key"], from_node.outputs[edge["output_key"]])
                # შესრულება
                if not node.execute():
                    self.logger.add("NodeEngine", f"❌ ნაკადი შეჩერდა: {node_id}", "error")
                    return False
            self.logger.add("NodeEngine", "✅ მთლიანი ნაკადი წარმატებით დასრულდა!", "success")
            return True
        except Exception as e:
            self.logger.add("NodeEngine", f"❌ კრიტიკული შეცდომა: {str(e)}", "error")
            return False

    def get_mermaid_diagram(self) -> str:
        """ქმნის Mermaid.js დიაგრამას"""
        lines = ["graph LR"]
        for n in self.workflow["nodes"]:
            lines.append(f'    {n["id"].replace("_","")}["{n["label"]}"]')
        for e in self.workflow["edges"]:
            lines.append(f'    {e["from"].replace("_","")} -- "{e["label"]}" --> {e["to"].replace("_","")}')
        return "\n".join(lines)
