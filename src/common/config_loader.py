"""Configuration loader for all YAML config files."""

import yaml
from pathlib import Path


class ConfigLoader:
    """Loads and manages all configuration files."""
    
    def __init__(self, base_path=None):
        """Initialize the config loader.
        
        Args:
            base_path: Base path of the project. If None, auto-detects.
        """
        if base_path is None:
            # Auto-detect: go up from this file to project root
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.config_dir = self.base_path / "configs"
    
    def load_services(self):
        """Load service recipes configuration."""
        config_path = self.config_dir / "service_recipes.yaml"
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    
    def load_benchmarks(self):
        """Load benchmark recipes configuration."""
        config_path = self.config_dir / "benchmark_recipes.yaml"
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    
    def load_all(self):
        """Load all configurations."""
        return {
            "services": self.load_services(),
            "benchmarks": self.load_benchmarks()
        }
