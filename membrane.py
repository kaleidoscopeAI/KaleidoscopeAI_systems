import math
import logging
import numpy as np
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from botocore.config import Config as BotoConfig
from rdkit import Chem
from rdkit.Chem import Descriptors
import joblib

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class DataMembrane:
    def __init__(self):
        self.cfg = ConfigManager()
        self.cfg.load_configs()
        self.node_memory = self.cfg.get("settings", "node_base_memory")

    def calculate_resources(self, data):
        data_size = data.memory_usage(deep=True).sum() / 1e6
        min_nodes = math.ceil(data_size / self.node_memory)
        insight_factor = max(0.1, min(0.9, data_size / 1000))
        target_nodes = math.ceil(min_nodes * (1 + insight_factor))
        logger.info(f"Data size: {data_size:.2f}MB, allocating {target_nodes} nodes")
        return target_nodes, self.node_memory

    def ingest_data(self, source):
        try:
            if source.startswith("s3://"):
                data = self._ingest_s3(source)
            elif Path(source).exists():
                data = self._ingest_local(source)
            else:
                raise ValueError(f"Unsupported data source: {source}")

            data = self._validate_data(data)
            data = self._filter_data(data)
            data = self._impute_data(data)
            logger.info(f"Data ingestion complete from: {source}")
            return data
        except Exception as e:
            logger.error(f"Data ingestion failed from {source}: {e}", exc_info=True)
            raise

    def _ingest_s3(self, uri):
        bucket, key = uri[5:].split("/", 1)
        retry_config = BotoConfig(retries={"max_attempts": 3, "mode": "standard"})
        s3 = boto3.client("s3", config=retry_config)
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
            file_format = key.split(".")[-1].lower()
            if file_format == "parquet":
                return pd.read_parquet(obj["Body"])
            elif file_format == "csv":
                return pd.read_csv(obj["Body"])
            elif file_format == "json":
                return pd.read_json(obj["Body"])
            else:
                raise ValueError(f"Unsupported S3 file format: {file_format}")
        except ClientError as e:
            logger.error(f"S3 ingestion error: {e}", exc_info=True)
            raise

    def _ingest_local(self, path):
        file_format = Path(path).suffix[1:].lower()
        if file_format == "parquet":
            return pd.read_parquet(path)
        elif file_format == "csv":
            return pd.read_csv(path)
        elif file_format == "json":
            return pd.read_json(path)
        else:
            raise ValueError(f"Unsupported local file format: {file_format}")

    def _validate_data(self, data):
        logger.info("Validating data...")
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Data is not a Pandas DataFrame.")
        if data.empty:
            raise ValueError("Data is empty.")
        for col in ["molecule_id", "smiles"]:
            if col not in data.columns:
                raise ValueError(f"Required column '{col}' missing from data.")
        logger.info("Data validation successful.")
        return data

    def _filter_data(self, data):
        logger.info("Filtering data...")
        initial = len(data)
        if "price" in data.columns:
            data = data[data["price"] >= 0]
        logger.info(f"Filtered out {initial - len(data)} rows.")
        return data

    def _impute_data(self, data):
        logger.info("Imputing data with optimized types...")
        dtype_map = {"price": "float32", "molecule_id": "int32"}
        for col, dtype in dtype_map.items():
            if col in data.columns:
                data[col] = data[col].astype(dtype)
        if data.isnull().any().any():
            for col in data.select_dtypes(include=np.number).columns:
                if data[col].isnull().any():
                    mean_val = data[col].mean()
                    data[col].fillna(mean_val, inplace=True)
                    logger.warning(f"Imputed '{col}' with mean {mean_val:.2f}")
        return data

    def ingest_crawled_data(self, crawled_data):
        processed = []
        for entry in crawled_data:
            smiles = entry.get("smiles", "CCO")
            processed.append({
                "molecule_id": 0,
                "smiles": smiles,
                "title": entry.get("title", "No Title"),
                "url": entry.get("url", "N/A")
            })
        df = pd.DataFrame(processed)
        logger.info(f"Ingesting crawled data with {len(df)} entries.")
        df = self._validate_data(df)
        df = self._filter_data(df)
        df = self._impute_data(df)
        return df

# Advanced Toxicity Predictor using a pre-trained model (if available)
class AdvancedToxicityPredictor:
    def __init__(self, model_path="models/toxicity_model.pkl"):
        try:
            self.model = joblib.load(model_path)
            logger.info("AdvancedToxicityPredictor: Loaded pre-trained model.")
        except Exception as e:
            logger.error(f"Error loading toxicity model: {e}", exc_info=True)
            self.model = None

    def submit_molecules(self, molecules_df):
        try:
            features = molecules_df["smiles"].apply(self._extract_features)
            features = list(features)
            predictions = self.model.predict(features) if self.model is not None else [0] * len(features)
            molecules_df["toxicity"] = predictions
            logger.info(f"Toxicity predictions complete for {len(molecules_df)} molecules.")
        except Exception as e:
            logger.error(f"Toxicity prediction failed: {e}", exc_info=True)

    def _extract_features(self, smiles):
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return [0, 0]
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        return [mw, logp]

