import json
import importlib
from typing import Dict, List, Any

class NodeEngine:
    """გამშვები ძრავა: ტვირთავს ნოდებს, აკავშირებს მათ და ასრულებს"""
    
    def __init__(self, config_path: str, logger):
        self.logger = logger
        with open(config_path, "r", encoding="utf-8") as f:
            self.workflow = json.load(f)
        
        self.nodes: Dict[str, Any] = {}
        self._load_nodes()
    
    def _load_nodes(self):
        """ტვირთავს ყველა ნოდს კონფიგურაციიდან"""
        for node_config in self.workflow["nodes"]:
            node_type = node_config["type"]
            module = importlib.import_module(f"nodes.{node_type.lower().replace('node', '')}_node")
            node_class = getattr(module, node_type)
            
            node = node_class(
                node_id=node_config["id"],
                config=node_config["config"],
                logger=self.logger
            )
            self.nodes[node_config["id"]] = node
    
    def _get_execution_order(self) -> List[str]:
        """განსაზღვრავს ნოდების შესრულების თანმიმდევრობას (topological sort)"""
        # მარტივი ვერსია: ეყრდნობა edges-ის თანმიმდევრობას
        order = []
        visited = set()
        
        def visit(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            # ჯერ შეიყვანე წინამორბედები
            for edge in self.workflow["edges"]:
                if edge["to"] == node_id and edge["from"] not in visited:
                    visit(edge["from"])
            order.append(node_id)
        
        for node in self.workflow["nodes"]:
            visit(node["id"])
        
        return order
    
    def execute(self, start_node: str = None) -> bool:
        """ასრულებს მთელ ნაკადს"""
        order = self._get_execution_order()
        self.logger.add("NodeEngine", f"🔄 შესრულების თანმიმდევრობა: {' → '.join(order)}", "start")
        
        for node_id in order:
            if start_node and node_id != start_node:
                continue
            
            node = self.nodes[node_id]
            
            # გადაეცი შეყვანები edges-ის მიხედვით
            for edge in self.workflow["edges"]:
                if edge["to"] == node_id:
                    from_node = self.nodes[edge["from"]]
                    value = from_node.get_output(edge["output_key"])
                    if value is not None:
                        node.set_input(edge["input_key"], value)
            
            # შეასრულე ნოდი
            success = node.execute()
            if not success:
                self.logger.add("NodeEngine", f"❌ ნაკადი შეჩერდა {node_id}-ზე", "error")
                return False
        
        self.logger.add("NodeEngine", "✅ მთლიანი ნაკადი წარმატებით დასრულდა", "success")
        return True
    
    def get_mermaid_diagram(self) -> str:
        """ქმნის Mermaid.js დიაგრამას ვიზუალიზაციისთვის"""
        lines = ["graph LR"]
        
        # ნოდები
        for node in self.workflow["nodes"]:
            color = node.get("color", "#999")
            lines.append(f'    {node["id"]}["{node["label"]}"]:::nodeStyle')
        
        # კავშირები
        for edge in self.workflow["edges"]:
            label = edge.get("label", "")
            lines.append(f'    {edge["from"]} -- "{label}" --> {edge["to"]}')
        
        # სტილები
        lines.append("    classDef nodeStyle fill:#f9f,stroke:#333,stroke-width:2px")
        
        return "\n".join(lines)
