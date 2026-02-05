"""Configuration file management utilities."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from .console import print_info, print_error, print_success, print_warning, Colors


def load_config(config_file: str = "config.json") -> Optional[Dict[str, Any]]:
    """Load configuration from JSON file."""
    config_path = Path(config_file)
    if not config_path.exists():
        return None

    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Check if it's a multi-instance config
    if 'instances' in config:
        # Multi-instance config
        return config
    else:
        # Legacy single-instance config - wrap it
        return {
            'instances': {
                'default': config
            },
            'default_instance': 'default'
        }


def save_config(config: Dict[str, Any], config_file: str = "config.json"):
    """Save configuration to JSON file."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)


def create_default_config(config_file: str = "config.json"):
    """Create a default configuration file with placeholders."""
    default_config = {
        "instances": {
            "production": {
                "base_url": "http://your-glpi-server",
                "client_id": "your_oauth_client_id",
                "client_secret": "your_oauth_client_secret",
                "username": "your_username",
                "password": "your_password",
                "verify_ssl": True,
                "description": "Production GLPI instance"
            },
            "development": {
                "base_url": "http://dev-glpi-server",
                "client_id": "dev_client_id",
                "client_secret": "dev_client_secret",
                "username": "dev_user",
                "password": "dev_password",
                "verify_ssl": False,
                "description": "Development GLPI instance"
            }
        },
        "default_instance": "production"
    }
    save_config(default_config, config_file)
    print_success(f"Created config file: {config_file}")
    print_info("\nThe config file supports multiple GLPI instances.")
    print_info("Edit the file to add your GLPI credentials for each instance.")
    print_info("\nYou can:")
    print_info("  - Add more instances by adding entries under 'instances'")
    print_info("  - Set 'default_instance' to your most-used instance")
    print_info("  - Use --instance flag to specify which instance to use")
    return default_config


def get_instance_config(
    config: Dict[str, Any], 
    instance_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific instance.
    
    Args:
        config: Full configuration dictionary
        instance_name: Name of the instance (None = use default)
    
    Returns:
        Instance configuration or None if not found
    """
    # Handle legacy single-instance config
    if 'instances' not in config:
        if instance_name and instance_name != 'default':
            print_error(f"Instance '{instance_name}' not found in config (legacy single-instance config)")
            return None
        return config
    
    # Multi-instance config
    instances = config.get('instances', {})
    
    if instance_name is None:
        instance_name = config.get('default_instance')
        if instance_name:
            print_info(f"Using default instance: {instance_name}")
    
    if instance_name not in instances:
        print_error(f"Instance '{instance_name}' not found in config")
        print_info(f"Available instances: {', '.join(instances.keys())}")
        return None
    
    return instances[instance_name]


def list_instances(config: Dict[str, Any]) -> List[str]:
    """
    List all configured instances.
    
    Args:
        config: Full configuration dictionary
    
    Returns:
        List of instance names
    """
    if 'instances' not in config:
        return ['default']
    return list(config.get('instances', {}).keys())


def get_instance_description(config: Dict[str, Any], instance_name: str) -> str:
    """
    Get description for an instance.
    
    Args:
        config: Full configuration dictionary
        instance_name: Name of the instance
    
    Returns:
        Description string
    """
    instance_config = get_instance_config(config, instance_name)
    if not instance_config:
        return ""
    
    description = instance_config.get('description', '')
    base_url = instance_config.get('base_url', '')
    
    if description:
        return f"{description} ({base_url})"
    return base_url


def interactive_select_instance(
    config: Dict[str, Any], 
    prompt: str = "Select GLPI instance"
) -> Optional[str]:
    """
    Interactively select an instance from available instances.
    
    Args:
        config: Full configuration dictionary
        prompt: Prompt message to display
    
    Returns:
        Selected instance name or None if cancelled
    """
    instances = list_instances(config)
    
    if len(instances) == 1:
        print_info(f"Using only available instance: {instances[0]}")
        return instances[0]
    
    print_info(f"\n{prompt}:")
    for i, instance_name in enumerate(instances, 1):
        desc = get_instance_description(config, instance_name)
        is_default = instance_name == config.get('default_instance', '')
        default_marker = " [default]" if is_default else ""
        print(f"  {i}. {instance_name}{default_marker}")
        if desc:
            print(f"     {Colors.OKBLUE}{desc}{Colors.ENDC}")
    
    while True:
        try:
            selection = input(f"\n{Colors.OKGREEN}Select instance (1-{len(instances)}): {Colors.ENDC}").strip()
            if not selection:
                # Use default if available
                default_instance = config.get('default_instance')
                if default_instance and default_instance in instances:
                    print_info(f"Using default: {default_instance}")
                    return default_instance
                print_warning("No default instance set")
                continue
            
            index = int(selection) - 1
            if 0 <= index < len(instances):
                selected = instances[index]
                print_success(f"Selected: {selected}")
                return selected
            else:
                print_warning(f"Please enter a number between 1 and {len(instances)}")
        except ValueError:
            print_warning("Please enter a valid number")
        except KeyboardInterrupt:
            print_warning("\nCancelled")
            return None
