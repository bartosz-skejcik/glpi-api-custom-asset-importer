"""Configuration file management utilities."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_file: str = "config.json") -> Optional[Dict[str, Any]]:
    """Load configuration from JSON file."""
    config_path = Path(config_file)
    if not config_path.exists():
        return None

    with open(config_path, 'r') as f:
        return json.load(f)


def save_config(config: Dict[str, Any], config_file: str = "config.json"):
    """Save configuration to JSON file."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)


def create_default_config(config_file: str = "config.json"):
    """Create a default configuration file with placeholders."""
    default_config = {
        "base_url": "http://your-glpi-server",
        "client_id": "your_oauth_client_id",
        "client_secret": "your_oauth_client_secret",
        "username": "your_username",
        "password": "your_password",
        "verify_ssl": True
    }
    save_config(default_config, config_file)
    return default_config
