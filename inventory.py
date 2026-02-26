import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path


class Inventory:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.nodes: List[Dict[str, Any]] = []
        
    def load(self) -> List[Dict[str, Any]]:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data or 'nodes' not in data:
            raise ValueError("Invalid inventory format: missing 'nodes' key")
        
        self.nodes = data['nodes']
        self._validate_nodes()
        return self.nodes
    
    def _validate_nodes(self):
        for i, node in enumerate(self.nodes):
            if 'host' not in node:
                raise ValueError(f"Node {i}: missing 'host' field")
            if 'user' not in node:
                raise ValueError(f"Node {i}: missing 'user' field")
            node.setdefault('port', 22)
            node.setdefault('auth', 'key')
    
    def get_node(self, host: str) -> Optional[Dict[str, Any]]:
        for node in self.nodes:
            if node['host'] == host:
                return node
        return None
