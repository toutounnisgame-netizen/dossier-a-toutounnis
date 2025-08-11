import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    def __init__(self, config_path: str = "config/default.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "system": {
                "name": "ALMAA",
                "version": "2.0",
                "debug": False,
                "max_workers": 10
            },
            "agents": {
                "max_agents": 20,
                "default_model": "llama3.2",
                "timeout": 30,
                "retry_count": 3
            },
            "memory": {
                "max_size": 1000000,
                "embedding_model": "all-MiniLM-L6-v2",
                "persist_directory": "./data/memory/vectors",
                "compression_threshold": 0.85
            },
            "debate": {
                "max_rounds": 5,
                "min_participants": 2,
                "max_participants": 7,
                "consensus_threshold": 0.7,
                "timeout_per_round": 60
            },
            "logging": {
                "level": "INFO",
                "file": "./data/logs/almaa.log",
                "rotation": "500 MB",
                "retention": "7 days"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self):
        """Sauvegarde la configuration"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
