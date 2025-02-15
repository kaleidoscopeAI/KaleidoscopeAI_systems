#!/usr/bin/env python3
import sys
import os
import logging
import subprocess
from pathlib import Path

# Import key modules from our codebase
from core.config_manager import ConfigManager
from core.membrane import DataMembrane
from core.pipeline_manager import PipelineManager
from core.chatbot import AIChatbot

def init_logging(config_mgr: ConfigManager) -> logging.Logger:
    log_level = config_mgr.get("settings", "log_level")
    log_dir = config_mgr.get("paths", "log_dir")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(os.path.join(log_dir, "orchestrator.log"))]
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized at level: %s", log_level)
    return logger

def ensure_directories(config_mgr: ConfigManager):
    # Ensure required directories exist
    required_dirs = ["config", "core", "web", "data", "results", "results/visualizations"]
    project_root = Path(__file__).parent
    for dirname in required_dirs:
        dir_path = project_root / dirname
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created missing directory: {dir_path}")

def orchestrate_setup():
    """Perform full setup orchestration: load config, ensure directories, check AWS creds."""
    config_mgr = ConfigManager()
    config_mgr.load_configs()
    logger = init_logging(config_mgr)
    ensure_directories(config_mgr)
    # Check if AWS credentials are set; warn if not.
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        logger.warning("AWS credentials not found in environment. For secure AWS access, please run 'source aws_creds_setup.sh'.")
    logger.info("Orchestration setup complete. All required directories are present.")

def run_pipeline(data_source: str):
    """Ingest data from a source and run the multi-phase pipeline."""
    config_mgr = ConfigManager()
    config_mgr.load_configs()
    logger = init_logging(config_mgr)
    membrane = DataMembrane()
    try:
        data = membrane.ingest_data(data_source)
    except Exception as e:
        logger.error("Failed to ingest data: %s", e, exc_info=True)
        sys.exit(1)
    if data.empty:
        logger.error("No data available for pipeline execution.")
        sys.exit(1)
    pipeline = PipelineManager(data)
    pipeline.run_full_pipeline()
    logger.info("Pipeline execution complete.")

def launch_web_app():
    """Launch the web application (Flask app) using module execution."""
    logger = logging.getLogger(__name__)
    project_root = Path(__file__).parent
    web_app_file = project_root / "web" / "app.py"
    if not web_app_file.exists():
        logger.error("Web app file %s not found.", web_app_file)
        sys.exit(1)
    logger.info("Launching web application...")
    # Use module-style execution so that project root is in PYTHONPATH
    try:
        subprocess.run(["python", "-m", "web.app"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to launch web app: %s", e, exc_info=True)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <setup|pipeline|web>")
        sys.exit(1)
    command = sys.argv[1].lower()
    if command == "setup":
        orchestrate_setup()
    elif command == "pipeline":
        if len(sys.argv) < 3:
            print("Usage: python orchestrator.py pipeline <data_source>")
            sys.exit(1)
        data_source = sys.argv[2]
        run_pipeline(data_source)
    elif command == "web":
        launch_web_app()
    else:
        print("Unknown command. Usage: python orchestrator.py <setup|pipeline|web>")
        sys.exit(1)

if __name__ == "__main__":
    main()
