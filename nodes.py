from dataclasses import dataclass
import numpy as np
import threading
import logging
import pandas as pd
import psutil
from .membrane import AdvancedToxicityPredictor
from .engines import KaleidoscopeEngine, PerspectiveEngine

logger = logging.getLogger(__name__)

@dataclass
class NodeConfig:
    memory_limit: float
    insight_threshold: float = 0.7
    dump_ratio: float = 0.4
    batch_size: int = 32

class AINode:
    def __init__(self, node_id, config: NodeConfig):
        self.id = node_id
        self.config = config
        self.memory_buffer = []
        self.insights = []
        self.lock = threading.Lock()

    def ingest(self, data_chunk: pd.DataFrame):
        if psutil.virtual_memory().available / 1e9 < 2:
            self._emergency_dump()
        if not isinstance(data_chunk, pd.DataFrame):
            logger.error(f"Node {self.id}: Data chunk is not a DataFrame.")
            return
        with self.lock:
            chunk_size = data_chunk.memory_usage(deep=True).sum() / 1e6
            if self._current_usage() + chunk_size > self.config.memory_limit:
                if self.memory_buffer:
                    self._dump_data()
                else:
                    logger.warning(f"Node {self.id}: Memory limit reached but buffer empty.")
            self.memory_buffer.append(data_chunk)
            self._generate_insights(data_chunk)

    def _generate_insights(self, data: pd.DataFrame):
        batch_size = self.config.batch_size
        for i in range(0, len(data), batch_size):
            batch = data.iloc[i:i+batch_size]
            insight = {
                "stats": batch.describe().to_dict(),
                "nulls": batch.isnull().sum().to_dict(),
                "correlations": batch.corr(numeric_only=True).abs().mean().mean() if not batch.select_dtypes(include=np.number).empty else 0
            }
            self.insights.append(insight)
        if len(self.insights) >= self.config.insight_threshold * len(self.memory_buffer):
            self._dump_insights()

    def _dump_data(self):
        try:
            if not self.memory_buffer:
                logger.warning(f"Node {self.id}: Dump data called but buffer empty.")
                return
            combined_data = pd.concat(self.memory_buffer)
            portion_size = int(len(self.insights) * self.config.dump_ratio)
            light_insights = self.insights[-portion_size:] if portion_size else []
            KaleidoscopeEngine.receive(combined_data, light_insights)
            PerspectiveEngine.receive(combined_data.sample(frac=0.5), light_insights)
            predictor = AdvancedToxicityPredictor()
            predictor.submit_molecules(combined_data[['molecule_id', 'smiles']])
            self.memory_buffer.clear()
            self.insights = self.insights[:-portion_size] if portion_size else self.insights
            logger.info(f"Node {self.id}: Data dumped and toxicity predictions complete.")
        except Exception as e:
            logger.error(f"Node {self.id}: Error during dump: {e}", exc_info=True)

    def _dump_insights(self):
        if not self.insights:
            logger.warning(f"Node {self.id}: No insights to dump.")
            return
        dumped = self.insights[:-int(len(self.insights) * self.config.dump_ratio)]
        avg_corr = np.mean([ins.get("correlations", 0) for ins in dumped])
        logger.info(f"Node {self.id}: Dumping {len(dumped)} insights; Avg Corr: {avg_corr:.4f}")
        self.insights = self.insights[-int(len(self.insights) * self.config.dump_ratio):]

    def _current_usage(self):
        return sum(chunk.memory_usage(deep=True).sum() / 1e6 for chunk in self.memory_buffer) if self.memory_buffer else 0

    def _emergency_dump(self):
        logger.warning(f"Node {self.id}: Low memory detected; emergency dump triggered.")
        self._dump_data()

