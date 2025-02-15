import logging
import math
import psutil
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

from .nodes import AINode, NodeConfig
from .membrane import DataMembrane
from .engines import KaleidoscopeEngine, PerspectiveEngine
from .quantum import QuantumConsciousness
from .cube_visualizer import generate_wireframe_cube, upload_to_s3
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class SuperNode:
    _counter = 0
    def __init__(self, dna_data: pd.DataFrame = None):
        SuperNode._counter += 1
        self.id = f"SuperNode-{SuperNode._counter}"
        self.dna = dna_data if dna_data is not None else pd.DataFrame()
        logger.info(f"[SuperNode] Created {self.id}, shape={self.dna.shape}")

class PipelineManager:
    def __init__(self, data: pd.DataFrame = None):
        self.config_mgr = ConfigManager()
        self.config_mgr.load_configs()
        self.settings = self.config_mgr.get("settings")
        self.max_phases = self.settings.get("max_phases", 2)
        self.supernodes = []
        self.qc = QuantumConsciousness()
        self.data = data

    def run_full_pipeline(self, data_source: str = None):
        if data_source and (self.data is None):
            membrane = DataMembrane()
            self.data = membrane.ingest_data(data_source)
        if self.data is None or self.data.empty:
            logger.error("[PipelineManager] No data available to run pipeline.")
            return
        logger.info(f"[PipelineManager] Starting multi-phase flow, up to {self.max_phases} phases.")
        current_data = self.data
        for phase_num in range(1, self.max_phases + 1):
            logger.info(f"----- PHASE {phase_num} -----")
            current_data = self._run_phase(current_data, phase_num)
            if current_data is None or current_data.empty:
                logger.info(f"[PipelineManager] Data empty after phase {phase_num}; stopping.")
                break
        logger.info("[PipelineManager] Phases complete. SuperNodes:")
        for sn in self.supernodes:
            logger.info(f"  - {sn.id}, shape={sn.dna.shape}")
        if self.supernodes:
            return self.supernodes[-1]
        return None

    def _run_phase(self, data: pd.DataFrame, phase_num: int) -> pd.DataFrame:
        self._check_resources()
        logger.info(f"[Phase {phase_num}] Creating nodes, distributing data.")
        nodes = self._create_and_distribute_nodes(data)
        if not nodes:
            return None
        logger.info(f"[Phase {phase_num}] Forcing final dump to engines.")
        for node in nodes:
            node._dump_data()
        self._check_resources()
        supernode_df = self._create_supernode_data(nodes, phase_num)
        super_node = SuperNode(supernode_df)
        self.supernodes.append(super_node)
        self.qc.entangle(super_node.id, f"phase_{phase_num}")
        logger.info(f"[Phase {phase_num}] Quantum entangled SuperNode {super_node.id}.")
        wireframe_file = generate_wireframe_cube(super_node.dna)
        if wireframe_file:
            logger.info(f"[Phase {phase_num}] 3D wireframe file: {wireframe_file}")
        return super_node.dna

    def _create_and_distribute_nodes(self, data: pd.DataFrame):
        node_count = self._calculate_node_count(data)
        if node_count <= 0:
            logger.error("[PipelineManager] Node count is zero; cannot proceed.")
            return []
        mem_limit = self.settings.get("node_base_memory", 500)
        nodes = [
            AINode(i, NodeConfig(
                memory_limit=mem_limit,
                insight_threshold=self.settings.get("insight_threshold_ratio", 0.7),
                dump_ratio=self.settings.get("node_dump_ratio", 0.4),
                batch_size=self.settings.get("batch_size", 32)
            ))
            for i in range(node_count)
        ]
        logger.info(f"[PipelineManager] Created {node_count} nodes. Distributing data.")
        chunk_size = len(data) // node_count if node_count else len(data)
        start_idx = 0
        for i, node in enumerate(nodes):
            end_idx = start_idx + chunk_size if i < node_count - 1 else len(data)
            chunk = data.iloc[start_idx:end_idx]
            node.ingest(chunk)
            start_idx = end_idx
        return nodes

    def _create_supernode_data(self, nodes, phase_num: int) -> pd.DataFrame:
        combined = []
        domain_idx = 0
        for node in nodes:
            if node.insights:
                all_corrs = [ins["correlations"] for ins in node.insights if "correlations" in ins]
                avg_corr = float(np.mean(all_corrs)) if all_corrs else 0.0
                combined.append({
                    "node_index": node.id,
                    "phase_num": phase_num,
                    "domain_idx": domain_idx,
                    "dimension_val": avg_corr,
                    "avg_corr": avg_corr
                })
            else:
                combined.append({
                    "node_index": node.id,
                    "phase_num": phase_num,
                    "domain_idx": domain_idx,
                    "dimension_val": 0.0,
                    "avg_corr": 0.0
                })
        if combined:
            return pd.DataFrame(combined)
        return pd.DataFrame()

    def _check_resources(self):
        mem_usage = psutil.virtual_memory().percent
        if mem_usage > 90:
            logger.warning(f"[ResourceCheck] Memory usage high: {mem_usage}%")
        cpu_usage = psutil.cpu_percent()
        if cpu_usage > 85:
            logger.warning(f"[ResourceCheck] CPU usage high: {cpu_usage}%")

    def _calculate_node_count(self, data: pd.DataFrame) -> int:
        base_mem = self.settings.get("node_base_memory", 500)
        data_size_mb = data.memory_usage(deep=True).sum() / 1e6
        node_count = math.ceil(data_size_mb / base_mem)
        available_gb = psutil.virtual_memory().available / 1e9
        max_nodes = math.floor(available_gb / (base_mem / 1024))
        final_count = max(1, min(node_count, max_nodes))
        logger.info(f"[PipelineManager] Data ~{data_size_mb:.2f}MB => NodeCount={final_count} (system-limited)")
        return final_count

