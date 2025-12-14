from pathlib import Path
import yaml
from typing import Dict, Any

CONFIG_DIR = Path(__file__).parent
PROMPTS_PATH = CONFIG_DIR / "prompts.yaml"
ROUTING_RULES_PATH = CONFIG_DIR / "routing_rules.yaml"


def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_prompt(key: str) -> str:
    data = load_yaml(PROMPTS_PATH)
    return data.get(key, {}).get("system", "")


def load_routing_rules() -> Dict[str, Dict[str, list]]:
    return load_yaml(ROUTING_RULES_PATH)
