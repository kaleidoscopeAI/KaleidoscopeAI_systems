import os
import yaml
from pathlib import Path
import logging
import psutil
import torch
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Pydantic models for configuration validation
class PathsConfig(BaseModel):
    model_cache: str
    data_dir: str
    log_dir: str
    results_dir: str
    visualization_dir: str

class SettingsConfig(BaseModel):
    node_base_memory: int
    log_level: str
    engine_max_buffer: int
    insight_threshold_ratio: float
    node_dump_ratio: float
    anomaly_iqr_multiplier: float
    trend_prediction_lookback: int
    scenario_clustering_n_clusters: int
    weakness_feature_importance_threshold: float
    max_phases: int
    cpu_threads: int
    batch_size: int
    enable_mlk: bool

class ConfigManager:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.configs = {}

    def load_configs(self):
        """Load and validate configuration files, then create required directories."""
        config_paths = {
            'paths': self.base_path / 'config' / 'paths.yaml',
            'settings': self.base_path / 'config' / 'settings.yaml'
        }
        for name, path in config_paths.items():
            if not path.exists():
                raise FileNotFoundError(f"Config file {path} not found: {path}")
            try:
                with open(path) as f:
                    raw_config = yaml.safe_load(f)
                    if name == 'paths':
                        self.configs[name] = PathsConfig(**raw_config)
                    elif name == 'settings':
                        self.configs[name] = SettingsConfig(**raw_config)
            except (yaml.YAMLError, ValidationError) as e:
                raise Exception(f"Error parsing or validating config file {path}: {e}")

        paths_config = self.configs['paths']
        os.environ['MODEL_CACHE'] = str(self.base_path / paths_config.model_cache)
        os.environ['DATA_DIR'] = str(self.base_path / paths_config.data_dir)
        os.environ['LOG_DIR'] = str(self.base_path / paths_config.log_dir)
        os.environ['RESULTS_DIR'] = str(self.base_path / paths_config.results_dir)
        os.environ['VISUALIZATION_DIR'] = str(self.base_path / paths_config.visualization_dir)

        # Ensure directories exist
        for key in paths_config.dict():
            directory = self.base_path / getattr(paths_config, key)
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

        self._auto_config_cpu()

    def _auto_config_cpu(self):
        physical_cores = psutil.cpu_count(logical=False)
        self.configs['settings'].cpu_threads = max(1, physical_cores - 1)
        torch.set_num_threads(self.configs['settings'].cpu_threads)
        logger.info(f"Configured {self.configs['settings'].cpu_threads} CPU threads.")

    def get(self, section, key=None):
        if section not in self.configs:
            raise ValueError(f"Configuration section '{section}' not found.")
        data = self.configs[section].dict() if hasattr(self.configs[section], "dict") else self.configs[section]
        return data.get(key) if key else data

