import os
import random
import time
import sys
import yaml

from dotenv import load_dotenv
from pathlib import Path

from utils import compute_traitors_game_metrics
from agent import Agent  # Import the Agent class
from llm_client import LLMClientFactory  # Import the LLM client factory
from utils.config import load_config, merge_config_with_args
from traitors_game import TraitorsGame  # Import the TraitorsGame class from the new file

# TODO: Keep metrics and overall conversation
# TODO: For each agent, keep all information in a folder/file, because their toughts are not shared with others
# TODO: Include an introduction phase, like: Player 1. [PROFESSION] [ETHNICITY] [COUNTRY] [AGE] [CIVIL STATUS] [CHILDREN]
# TODO: Decide on which models to run + number of times + temperature + top_p
# TODO: Write Paper
# TODO: README.md + Documentation
# TODO: MULTIAGENTS (?)
# TODO: Game through a config file

load_dotenv()


# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run a Traitors Game simulation with AI agents"
    )
    
    # Add config file argument
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML configuration file"
    )
    
    # Keep existing arguments as optional overrides
    parser.add_argument(
        "--agents",
        type=int,
        help="Number of agents in the game (overrides config file)"
    )
    parser.add_argument(
        "--traitors",
        type=int,
        help="Number of traitor agents (overrides config file)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model name to use (overrides config file)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility (overrides config file)"
    )
    parser.add_argument(
        "--client",
        type=str,
        choices=["openai", "hf", "mlx"],
        help="Client type (overrides config file)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["deepseek", "openai", "together"],
        help="Provider for HF client (overrides config file)"
    )
    parser.add_argument(
        "--experiment_name",
        type=str,
        help="Name of the experiment (overrides config file)"
    )

    args = parser.parse_args()

    # Load configuration
    if args.config:
        try:
            config = load_config(args.config)
            # Merge with command line arguments (args override config)
            config = merge_config_with_args(config, args)
        except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
    else:
        # Use default values if no config file is provided
        config = {
            'game': {
                'agent_count': args.agents or 10,
                'traitor_count': args.traitors or 3,
                'seed': args.seed or 42,
                'experiment_name': args.experiment_name,
            },
            'llm': {
                'model': args.model or "deepseek-chat",
                'client_type': args.client or "openai",
                'provider': args.provider or "deepseek",
            }
        }

    try:
        # Create and run the game with the configuration
        game = TraitorsGame(
            config=config,
            agent_count=config['game']['agent_count'],
            traitor_count=config['game']['traitor_count'],
            model=config['llm']['model'],
            seed=config['game']['seed'],
            client_type=config['llm']['client_type'],
            provider=config['llm'].get('provider'),
            experiment_name=config['game'].get('experiment_name'),
        )
        game.run()
        game.post_game_analysis()
    except Exception as e:
        print(f"Error running game: {e}")
        sys.exit(1)
