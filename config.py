import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "ae_title": "PZDR",
    "pacs_host": "localhost",
    "pacs_port": 11112,
    "called_ae": "DCM4CHEE",
    "portal_url": "http://localhost",
    "portal_api_key": "change-me-in-production",
}


def load():
    if not CONFIG_PATH.exists():
        save(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
