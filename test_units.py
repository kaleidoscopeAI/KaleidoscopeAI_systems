import unittest
from kaleidoscope_ai.core.config_manager import ConfigManager
import os
from pathlib import Path

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        config_dir = Path(__file__).parent.parent / 'config'
        self.paths_config_path = config_dir / 'paths.yaml'
        self.settings_config_path = config_dir / 'settings.yaml'
        config_dir.mkdir(parents=True, exist_ok=True)
        if not self.paths_config_path.exists():
            with open(self.paths_config_path, 'w') as f:
                f.write("model_cache: 'test_models/'\ndata_dir: 'test_data/'\nlog_dir: 'test_logs/'\nresults_dir: 'test_results/'\nvisualization_dir: 'test_visuals/'")
        if not self.settings_config_path.exists():
            with open(self.settings_config_path, 'w') as f:
                f.write("node_base_memory: 256\nlog_level: 'DEBUG'\nengine_max_buffer: 512")

    def test_load_configs_success(self):
        self.config_manager.load_configs()
        self.assertIsNotNone(self.config_manager.configs.get('paths'))
        self.assertIsNotNone(self.config_manager.configs.get('settings'))

    def test_get_path_config(self):
        self.config_manager.load_configs()
        model_cache_path = self.config_manager.get('paths', 'model_cache')
        self.assertEqual(model_cache_path, 'test_models/')

    def test_get_setting_config(self):
        self.config_manager.load_configs()
        node_memory = self.config_manager.get('settings', 'node_base_memory')
        self.assertEqual(node_memory, 256)

    def test_config_not_found_error(self):
        config_manager = ConfigManager()
        with self.assertRaises(FileNotFoundError):
            config_manager.load_configs()

    def test_yaml_parse_error(self):
        config_manager = ConfigManager()
        with open(self.settings_config_path, 'w') as f:
            f.write("node_base_memory: invalid yaml: :")
        with self.assertRaises(Exception):
            config_manager.load_configs()

    def test_environment_variables_set(self):
        self.config_manager.load_configs()
        self.assertIsNotNone(os.environ.get('MODEL_CACHE'))
        self.assertIsNotNone(os.environ.get('DATA_DIR'))
        self.assertIsNotNone(os.environ.get('LOG_DIR'))
        self.assertIsNotNone(os.environ.get('RESULTS_DIR'))
        self.assertIsNotNone(os.environ.get('VISUALIZATION_DIR'))

if __name__ == '__main__':
    unittest.main()

