# AI Empire HQ - Agent Abstraction Layer (AAL) Provider Registry
# Version: 1.0

import importlib
import os
import yaml
from typing import Dict, List, Type

from .interfaces import IAgentProvider
from .models import AgentRequest, AgentResponse  # Import for type hints

# Configuration file for providers
PROVIDER_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "agents.yml")


class ProviderRegistry:
    """
    Manages the loading and registration of IAgentProvider implementations
    based on a configuration file.
    """

    _instance: 'ProviderRegistry' = None  # Singleton instance

    def __new__(cls) -> 'ProviderRegistry':
        if cls._instance is None:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._providers: Dict[str, IAgentProvider] = {}
        self._load_providers_from_config()
        self._initialized = True

    def _load_providers_from_config(self):
        """
        Loads provider configurations from agents.yml and initializes providers.
        """
        print(f"Loading providers from: {PROVIDER_CONFIG_FILE}")
        if not os.path.exists(PROVIDER_CONFIG_FILE):
            print(f"Warning: Provider config file not found at {PROVIDER_CONFIG_FILE}")
            return

        with open(PROVIDER_CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)

        if "providers" not in config:
            print("Warning: 'providers' section not found in config.")
            return

        for provider_name, provider_config in config["providers"].items():
            try:
                class_path = provider_config["class"]
                module_name, class_name = class_path.rsplit(".", 1)

                module = importlib.import_module(module_name)
                provider_class: Type[IAgentProvider] = getattr(module, class_name)

                # Extract model_configs to pass to the provider
                model_configs = provider_config.get("models", {})
                
                provider_instance = provider_class(model_configs) # Pass model_configs here
                self._providers[provider_name] = provider_instance
                print(f"Registered provider: {provider_name} (Class: {class_name}) with {len(model_configs)} models.")
            except Exception as e:
                print(f"Error loading provider {provider_name}: {e}")

    def get_provider(self, name: str) -> IAgentProvider | None:
        """Retrieves a registered provider by name."""
        return self._providers.get(name)

    def get_all_providers(self) -> List[IAgentProvider]:
        """Returns a list of all registered providers."""
        return list(self._providers.values())


def get_provider_registry() -> ProviderRegistry:
    """
    Singleton factory function for ProviderRegistry.
    """
    return ProviderRegistry()
