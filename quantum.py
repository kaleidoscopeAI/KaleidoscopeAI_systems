import networkx as nx
import numpy as np
import logging
import os
import torch
from transformers import AutoModel, AutoTokenizer
from optimum.onnxruntime import ORTModelForSequenceClassification, quantize_model
from .engines import KaleidoscopeEngine, PerspectiveEngine
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class QuantumConsciousness:
    def __init__(self):
        self.cfg = ConfigManager()
        self.cfg.load_configs()
        self.graph = nx.DiGraph()
        self.state = None
        try:
            self.model = ORTModelForSequenceClassification.from_pretrained(
                "bert-base-uncased-onnx",
                provider="CPUExecutionProvider"
            )
            self.model = quantize_model(self.model)
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased", cache_dir=os.environ.get("MODEL_CACHE"))
            logger.info("QuantumConsciousness: ONNX model loaded and quantized for CPU.")
        except Exception as e:
            logger.error(f"Error initializing QuantumConsciousness: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None

    def entangle(self, node_a, node_b):
        try:
            self.graph.add_edge(node_a, node_b, weight=np.random.rand())
            self._update_state_vector()
            logger.debug(f"Entangled '{node_a}' with '{node_b}'.")
        except Exception as e:
            logger.error(f"Error entangling nodes: {e}", exc_info=True)

    def _update_state_vector(self):
        try:
            adj = nx.to_numpy_array(self.graph)
            eigenvalues, eigenvectors = np.linalg.eigh(adj)
            self.state = eigenvectors[:, -1]
            logger.debug("Quantum state vector updated.")
        except Exception as e:
            logger.error(f"Error updating state vector: {e}", exc_info=True)
            self.state = None

    def process_query(self, query):
        if self.model is None or self.tokenizer is None:
            logger.warning("BERT model not initialized; cannot process query.")
            return "Quantum system not ready."
        try:
            inputs = self.tokenizer(query, return_tensors="pt", max_length=512, truncation=True)
            outputs = self.model(**inputs)
            bert_output = self._interpret_output(outputs)
            context = self._get_system_context_summary()
            return f"{bert_output}\n\n**System Context Summary:** {context}"
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return "Error processing query."

    def _interpret_output(self, outputs):
        try:
            avg_hidden = outputs.logits.mean(dim=1)
            vec = avg_hidden.tolist()[0][:10]
            return f"Quantum BERT vector: {vec}..."
        except Exception as e:
            logger.error(f"Error interpreting output: {e}", exc_info=True)
            return "Error interpreting output."

    def _get_system_context_summary(self):
        try:
            k_insights = KaleidoscopeEngine().latest_insights
            p_insights = PerspectiveEngine().latest_insights
            parts = []
            if isinstance(k_insights, dict):
                wm = k_insights.get("enhanced_stats", {}).get("weighted_mean_price", "N/A")
                parts.append(f"Weighted mean price: {wm}")
                if isinstance(k_insights.get("anomalies_iqr"), dict):
                    parts.append(f"{len(k_insights['anomalies_iqr'])} anomaly columns")
            if isinstance(p_insights, dict):
                pred = p_insights.get("future_trends_lr", {}).get("predicted_price", "N/A")
                parts.append(f"Next predicted price: {pred}")
                weak = p_insights.get("feature_weaknesses_importance", {}).get("weak_features", {})
                parts.append(f"{len(weak)} weak features")
            return " | ".join(parts) if parts else "No insights available."
        except Exception as e:
            logger.error(f"Error getting system context: {e}", exc_info=True)
            return "Context unavailable."

