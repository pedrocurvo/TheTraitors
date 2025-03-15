"""Configuration utilities for TheTraitors game."""

import yaml
from typing import Dict, Any, Optional, List

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dict containing the configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        ValueError: If config is missing required fields or has invalid values
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing configuration file: {e}")
    
    validate_config(config)
    return config

def validate_llm_config(llm_config: Dict[str, Any], config_name: str = "llm") -> None:
    """Validate an LLM configuration section.
    
    Args:
        llm_config: LLM configuration dictionary to validate
        config_name: Name of the configuration section for error messages
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_llm_fields = {
        'model': str,
        'client_type': str,
    }
    
    for field, field_type in required_llm_fields.items():
        if field not in llm_config:
            raise ValueError(f"Missing required field in {config_name} config: {field}")
        if not isinstance(llm_config[field], field_type):
            raise ValueError(f"Invalid type for {field} in {config_name}. Expected {field_type}")
    
    # Validate client_type
    valid_client_types = ['openai', 'hf', 'mlx']
    if llm_config['client_type'] not in valid_client_types:
        raise ValueError(f"Invalid client_type in {config_name}. Must be one of: {valid_client_types}")

def validate_config(config: Dict[str, Any]) -> None:
    """Validate the configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Check required sections
    required_sections = ['game', 'llm']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section in config: {section}")
    
    # Validate game section
    game_config = config['game']
    required_game_fields = {
        'agent_count': int,
        'traitor_count': int,
    }
    
    for field, field_type in required_game_fields.items():
        if field not in game_config:
            raise ValueError(f"Missing required field in game config: {field}")
        if not isinstance(game_config[field], field_type):
            raise ValueError(f"Invalid type for {field}. Expected {field_type}")
    
    # Validate agent/traitor counts
    if game_config['traitor_count'] >= game_config['agent_count']:
        raise ValueError("traitor_count must be less than agent_count")
    
    # Validate default LLM configuration
    validate_llm_config(config['llm'])
    
    # Validate per-agent configurations if present
    if 'agents' in config:
        if not isinstance(config['agents'], dict):
            raise ValueError("agents section must be a dictionary")
        
        # Validate each agent's configuration
        for agent_id, agent_config in config['agents'].items():
            try:
                agent_id = int(agent_id)
                if agent_id < 0 or agent_id >= game_config['agent_count']:
                    raise ValueError(
                        f"Invalid agent ID {agent_id}. Must be between 0 and {game_config['agent_count']-1}"
                    )
            except ValueError:
                raise ValueError(f"Invalid agent ID {agent_id}. Must be an integer")
            
            validate_llm_config(agent_config, f"agent {agent_id}")

def get_agent_config(config: Dict[str, Any], agent_id: int) -> Dict[str, Any]:
    """Get the LLM configuration for a specific agent.
    
    Args:
        config: Full configuration dictionary
        agent_id: ID of the agent to get configuration for
        
    Returns:
        Dictionary containing the agent's LLM configuration
    """
    # Start with the default LLM configuration
    agent_config = config['llm'].copy()
    
    # Override with per-agent configuration if present
    if 'agents' in config and str(agent_id) in config['agents']:
        agent_config.update(config['agents'][str(agent_id)])
    
    return agent_config

def merge_config_with_args(config: Dict[str, Any], args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Merge configuration from file with command line arguments.
    
    Command line arguments take precedence over config file values.
    
    Args:
        config: Configuration dictionary from file
        args: Optional dictionary of command line arguments
        
    Returns:
        Merged configuration dictionary
    """
    if not args:
        return config
    
    merged = config.copy()
    
    # Map argument names to config paths
    arg_map = {
        'agents': ('game', 'agent_count'),
        'traitors': ('game', 'traitor_count'),
        'model': ('llm', 'model'),
        'client': ('llm', 'client_type'),
        'provider': ('llm', 'provider'),
        'seed': ('game', 'seed'),
        'experiment_name': ('game', 'experiment_name'),
    }
    
    # Update config with command line arguments if they're not None
    for arg_name, config_path in arg_map.items():
        if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
            section, key = config_path
            if section not in merged:
                merged[section] = {}
            merged[section][key] = getattr(args, arg_name)
    
    return merged 