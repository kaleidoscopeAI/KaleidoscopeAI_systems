from queue import Queue
from threading import Thread
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class EngineBase:
    _instance = None
    MAX_BUFFER = 1024

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.buffer = Queue()
            cls._instance.process_thread = Thread(target=cls._instance._process_buffer, daemon=True)
            cls._instance.process_thread.start()
            cls._instance.visualization_dir = os.environ.get("VISUALIZATION_DIR")
            os.makedirs(cls._instance.visualization_dir, exist_ok=True)
            cls._instance.latest_insights = None
            cls._instance.cfg = ConfigManager()
            cls._instance.cfg.load_configs()
            EngineBase.MAX_BUFFER = cls._instance.cfg.get("settings", "engine_max_buffer")
        return cls._instance

    def receive(self, data, insights):
        if data is not None and not data.empty:
            self.buffer.put((data, insights))
            logger.info(f"{self.__class__.__name__} received data; buffer size: {self.buffer.qsize()}")
        else:
            logger.warning(f"{self.__class__.__name__} received empty data; ignoring.")

    def _process_buffer(self):
        while True:
            data_insight_pair = self.buffer.get()
            if data_insight_pair is None:
                logger.info(f"{self.__class__.__name__} received termination signal.")
                break
            data, insights = data_insight_pair
            if self._should_process():
                try:
                    self.process(data, insights)
                except Exception as e:
                    logger.error(f"{self.__class__.__name__} process error: {e}", exc_info=True)
            self.buffer.task_done()

    def _should_process(self):
        return self.buffer.qsize() >= 3 or self._memory_usage() > self.MAX_BUFFER

    def _memory_usage(self):
        return sum(data.memory_usage(deep=True).sum()/1e6 for data, _ in list(self.buffer.queue)) if not self.buffer.empty() else 0

    def process(self, data, insights):
        raise NotImplementedError("Subclasses must implement process.")

    def _save_visualization(self, fig, filename):
        filepath = os.path.join(self.visualization_dir, filename)
        fig.savefig(filepath)
        plt.close(fig)
        logger.info(f"Visualization saved to: {filepath}")

class KaleidoscopeEngine(EngineBase):
    def process(self, data, insights):
        logger.info(f"KaleidoscopeEngine processing data: {data.shape}")
        try:
            refined = {
                "enhanced_stats": self._calculate_weighted_stats(data, insights),
                "data_relationships_heatmap": self._find_complex_relationships(data),
                "anomalies_iqr": self._detect_anomalies(data)
            }
            self.latest_insights = refined
            self._send_to_environment(refined)
            logger.info("KaleidoscopeEngine: Insights refined.")
        except Exception as e:
            logger.error(f"KaleidoscopeEngine process error: {e}", exc_info=True)

    def _calculate_weighted_stats(self, data, insights):
        logger.info("KaleidoscopeEngine: Calculating weighted statistics.")
        if "price" in data.columns and not data.empty:
            wm = np.average(data["price"], weights=data.index).round(2)
            return {"weighted_mean_price": wm}
        return {"weighted_mean_price": "N/A"}

    def _find_complex_relationships(self, data):
        logger.info("KaleidoscopeEngine: Generating correlation heatmap.")
        numeric = data.select_dtypes(include=np.number)
        if numeric.empty or numeric.shape[1] < 2:
            return "Correlation heatmap not generated."
        corr = numeric.corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr, cmap="coolwarm", ax=ax)
        ax.set_title("Correlation Heatmap")
        filename = f"corr_heatmap_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        self._save_visualization(fig, filename)
        return filename

    def _detect_anomalies(self, data):
        logger.info("KaleidoscopeEngine: Detecting anomalies.")
        anomalies = {}
        iqr_mult = self.cfg.get("settings", "anomaly_iqr_multiplier")
        for col in data.select_dtypes(include=np.number):
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - iqr_mult*IQR, Q3 + iqr_mult*IQR
            outs = data[(data[col] < lower) | (data[col] > upper)][col].tolist()
            if outs:
                anomalies[col] = outs
        if anomalies:
            logger.warning(f"Anomalies: {list(anomalies.keys())}")
        else:
            logger.info("No anomalies detected.")
        return anomalies if anomalies else "No anomalies detected."

    def _send_to_environment(self, refined):
        logger.info(f"KaleidoscopeEngine sending insights: {refined.keys()}")
        print("\n--- Kaleidoscope Engine Insights ---")
        for key, value in refined.items():
            print(f"{key}: {value}")
        print("--- End Insights ---")

class PerspectiveEngine(EngineBase):
    def process(self, data, insights):
        logger.info(f"PerspectiveEngine processing data: {data.shape}")
        try:
            speculative = {
                "future_trends_lr": self._predict_trends(data),
                "data_scenarios_kmeans": self._generate_scenarios(data),
                "feature_weaknesses_importance": self._find_weaknesses(data)
            }
            self.latest_insights = speculative
            self._send_to_environment(speculative)
            logger.info("PerspectiveEngine: Speculative insights generated.")
        except Exception as e:
            logger.error(f"PerspectiveEngine process error: {e}", exc_info=True)

    def _predict_trends(self, data):
        logger.info("PerspectiveEngine: Predicting trends.")
        if "price" not in data.columns or data.empty:
            return "Trend prediction unavailable."
        lookback = self.cfg.get("settings", "trend_prediction_lookback")
        if len(data) < lookback:
            return "Insufficient data for trend prediction."
        ts = data["price"].tail(lookback).reset_index(drop=True)
        X = np.array(ts.index).reshape(-1, 1)
        y = ts.values
        model = LinearRegression().fit(X, y)
        future = np.array([[lookback]])
        pred = model.predict(future)[0].round(2)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(ts.index, ts.values, label="Historical Price")
        ax.plot(future, pred, "ro-", label=f"Predicted: {pred}")
        ax.set_title("Trend Prediction")
        ax.legend()
        filename = f"trend_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        self._save_visualization(fig, filename)
        return {"predicted_price": pred, "visualization": filename}

    def _generate_scenarios(self, data):
        logger.info("PerspectiveEngine: Generating clustering scenarios.")
        if data.empty:
            return "Scenario generation unavailable."
        features = ["price"]
        if not all(col in data.columns for col in features):
            return "Required features missing."
        n_clusters = self.cfg.get("settings", "scenario_clustering_n_clusters")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(data[features].fillna(0))
        data["cluster"] = clusters
        profiles = data.groupby("cluster")[features].mean().to_dict("index")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(x=data.index, y=data["price"], hue=data["cluster"], palette="viridis", ax=ax)
        ax.set_title("Clustering Scenarios")
        filename = f"cluster_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        self._save_visualization(fig, filename)
        return {"scenario_profiles": profiles, "visualization": filename}

    def _find_weaknesses(self, data):
        logger.info("PerspectiveEngine: Evaluating feature weaknesses.")
        if "price" not in data.columns or data.empty or data.shape[1] < 2:
            return "Weakness analysis unavailable."
        X = data.drop(columns=["price"], errors="ignore").select_dtypes(include=np.number).fillna(0)
        y = data["price"]
        if X.empty:
            return "Weakness analysis unavailable."
        model = RandomForestRegressor(random_state=42)
        model.fit(X, y)
        perm = permutation_importance(model, X, y, n_repeats=10, random_state=42)
        importance = pd.Series(perm.importances_mean, index=X.columns).sort_values(ascending=False)
        threshold = self.cfg.get("settings", "weakness_feature_importance_threshold")
        weak_features = importance[importance < threshold].to_dict()
        fig, ax = plt.subplots(figsize=(8, 6))
        importance.plot(kind="bar", ax=ax)
        ax.set_title("Feature Importance")
        filename = f"feature_importance_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        self._save_visualization(fig, filename)
        if weak_features:
            return {"weak_features": weak_features, "visualization": filename}
        return "No significant weaknesses detected."

    def _send_to_environment(self, speculative):
        logger.info(f"PerspectiveEngine sending insights: {speculative.keys()}")
        print("\n--- Perspective Engine Insights ---")
        for key, value in speculative.items():
            print(f"{key}: {value}")
        print("--- End Insights ---")

