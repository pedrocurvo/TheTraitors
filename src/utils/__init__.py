"""
Utility functions for TheTraitors.
"""

import yaml


def load_config(config_path):
    """
    Load a YAML configuration file.

    Args:
        config_path (str): Path to the configuration file

    Returns:
        dict: Loaded configuration
    """
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
