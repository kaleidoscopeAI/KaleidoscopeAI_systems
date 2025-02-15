import logging
import os
from pathlib import Path
import numpy as np
import pandas as pd
from core.config_manager import ConfigManager
from core.membrane import DataMembrane
from core.pipeline_manager import PipelineManager
from core.chatbot import AIChatbot

def setup_logging(config_manager):
    log_level_str = config_manager.get("settings", "log_level")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    log_dir = config_manager.get("paths", "log_dir")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(os.path.join(log_dir, "kaleidoscope_ai.log"))]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at {log_level_str}")
    return logger

def main(data_source):
    config_manager = ConfigManager()
    config_manager.load_configs()
    logger = setup_logging(config_manager)
    membrane = DataMembrane()
    data = membrane.ingest_data(data_source)
    logger.info("Data ingested successfully.")

    pipeline_mgr = PipelineManager(data)
    final_supernode = pipeline_mgr.run_full_pipeline()

    chatbot = AIChatbot()
    if final_supernode is not None:
        chatbot.register_supernode(final_supernode)
        print("System ready. SuperNodes created:")
        print(f"Number of SuperNodes: {len(pipeline_mgr.supernodes)}")
    else:
        print("Pipeline failed to generate SuperNodes.")

if __name__ == "__main__":
    data_source_input = input("Enter data source (local file path or 'example'): ").strip()
    if not data_source_input or data_source_input.lower() == "example":
        data_source_input = "data/example_data.parquet"
    if not Path("data").exists():
        Path("data").mkdir(exist_ok=True)
    example_data_path = "data/example_data.parquet"
    if not Path(example_data_path).exists():
        example_df = pd.DataFrame({
            "molecule_id": range(1, 101),
            "smiles": ["CCO" for _ in range(100)],
            "price": [float(i + 10) for i in range(100)],
            "feature1": np.random.rand(100),
            "feature2": np.random.rand(100)
        })
        example_df.to_parquet(example_data_path)
        print(f"Example data file created at: {example_data_path}")
    main(data_source_input)

