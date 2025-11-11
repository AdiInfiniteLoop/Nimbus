import logging
import numpy as np
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import threading
import time

logger = logging.getLogger(__name__)

class CPUPredictor:
    """ML-based CPU usage predictor using Random Forest"""
    
    def __init__(self, history_window=60, prediction_interval=30):
        """
        Args:
            history_window: Number of historical data points to keep (default: 60 = 5min at 5s intervals)
            prediction_interval: Seconds into future to predict (default: 30s)
        """
        self.history_window = history_window
        self.prediction_interval = prediction_interval
        self.node_histories = {}  # {node_id: deque of metrics}
        self.models = {}  # {node_id: trained model}
        self.scalers = {}  # {node_id: feature scaler}
        self.predictions = {}  # {node_id: latest prediction}
        self.lock = threading.Lock()
        
        # Model hyperparameters
        self.n_estimators = 50
        self.max_depth = 10
        self.min_samples_split = 5
        
        logger.info(f"CPUPredictor initialized (window={history_window}, interval={prediction_interval}s)")
    
    def add_metric(self, node_id: str, cpu_percent: float, memory_percent: float, 
                   pod_count: int, total_cpu_capacity: int):
        """Add a new metric data point for a node"""
        with self.lock:
            if node_id not in self.node_histories:
                self.node_histories[node_id] = deque(maxlen=self.history_window)
            
            metric = {
                'timestamp': datetime.now(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'pod_count': pod_count,
                'total_cpu_capacity': total_cpu_capacity
            }
            
            self.node_histories[node_id].append(metric)
            logger.debug(f"Added metric for node {node_id}: CPU={cpu_percent:.2f}%")
    
    def _extract_features(self, history: List[Dict]) -> np.ndarray:
        """Extract features from historical metrics"""
        if len(history) < 5:
            return None
        
        recent = history[-10:]  # Last 10 data points (50 seconds)
        cpu_values = [m['cpu_percent'] for m in recent]
        memory_values = [m['memory_percent'] for m in recent]
        
        features = [
            # Current state
            history[-1]['cpu_percent'],
            history[-1]['memory_percent'],
            history[-1]['pod_count'],
            history[-1]['total_cpu_capacity'],
            
            # Statistical features
            np.mean(cpu_values),
            np.std(cpu_values),
            np.min(cpu_values),
            np.max(cpu_values),
            
            # Trend features
            cpu_values[-1] - cpu_values[0],  # CPU change
            np.mean(memory_values),
            
            # Time-based features
            datetime.now().hour,
            datetime.now().minute,
            len(history)  # How much history we have
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _prepare_training_data(self, history: List[Dict]) -> tuple:
        """Prepare X and y for training"""
        if len(history) < 15:
            return None, None
        
        X, y = [], []
        
        # Create training samples with sliding window
        for i in range(10, len(history) - 6):  # -6 for prediction offset
            snapshot = list(history)[:i]
            features = self._extract_features(snapshot)
            
            if features is not None:
                # Target: CPU usage 6 steps ahead (30 seconds at 5s intervals)
                future_idx = min(i + 6, len(history) - 1)
                target_cpu = history[future_idx]['cpu_percent']
                
                X.append(features[0])
                y.append(target_cpu)
        
        if len(X) == 0:
            return None, None
        
        return np.array(X), np.array(y)
    
    def train_model(self, node_id: str) -> bool:
        """Train or retrain model for a specific node"""
        with self.lock:
            if node_id not in self.node_histories:
                return False
            
            history = list(self.node_histories[node_id])
        
        if len(history) < 15:
            logger.debug(f"Node {node_id}: Insufficient data for training ({len(history)} points)")
            return False
        
        X, y = self._prepare_training_data(history)
        
        if X is None or len(X) < 5:
            logger.debug(f"Node {node_id}: Could not prepare training data")
            return False
        
        try:
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train Random Forest
            model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_scaled, y)
            
            # Calculate training score
            score = model.score(X_scaled, y)
            
            with self.lock:
                self.models[node_id] = model
                self.scalers[node_id] = scaler
            
            logger.info(f"Node {node_id}: Model trained (R²={score:.3f}, samples={len(X)})")
            return True
            
        except Exception as e:
            logger.error(f"Node {node_id}: Training failed - {e}")
            return False
    
    def predict(self, node_id: str) -> Optional[float]:
        """Predict CPU usage for next interval"""
        with self.lock:
            if node_id not in self.node_histories:
                return None
            
            if node_id not in self.models:
                return None
            
            history = list(self.node_histories[node_id])
            model = self.models[node_id]
            scaler = self.scalers[node_id]
        
        if len(history) < 5:
            return None
        
        try:
            # Extract current features
            features = self._extract_features(history)
            if features is None:
                return None
            
            # Scale and predict
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)[0]
            
            # Clamp prediction to valid range
            prediction = max(0.0, min(100.0, prediction))
            
            with self.lock:
                self.predictions[node_id] = {
                    'predicted_cpu': prediction,
                    'timestamp': datetime.now(),
                    'current_cpu': history[-1]['cpu_percent']
                }
            
            logger.debug(
                f"Node {node_id}: Predicted CPU={prediction:.2f}% "
                f"(current={history[-1]['cpu_percent']:.2f}%)"
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Node {node_id}: Prediction failed - {e}")
            return None
    
    def get_prediction(self, node_id: str) -> Optional[Dict]:
        """Get the latest prediction for a node"""
        with self.lock:
            return self.predictions.get(node_id)
    
    def get_all_predictions(self) -> Dict:
        """Get predictions for all nodes"""
        with self.lock:
            return {
                node_id: pred.copy() 
                for node_id, pred in self.predictions.items()
            }
    
    def cleanup_node(self, node_id: str):
        """Remove all data for a node"""
        with self.lock:
            self.node_histories.pop(node_id, None)
            self.models.pop(node_id, None)
            self.scalers.pop(node_id, None)
            self.predictions.pop(node_id, None)
        logger.info(f"Node {node_id}: Cleaned up predictor data")


class PredictorManager:
    """Manages continuous prediction updates"""
    
    def __init__(self, predictor: CPUPredictor, nodes: Dict, pods: Dict):
        self.predictor = predictor
        self.nodes = nodes
        self.pods = pods
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the prediction loop"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._prediction_loop, daemon=True)
        self.thread.start()
        logger.info("PredictorManager started")
    
    def stop(self):
        """Stop the prediction loop"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("PredictorManager stopped")
    
    def _prediction_loop(self):
        """Continuously train and predict"""
        train_counter = 0
        
        while self.running:
            try:
                for node_id in list(self.nodes.keys()):
                    # Train every 12 iterations (60 seconds at 5s intervals)
                    if train_counter % 12 == 0:
                        self.predictor.train_model(node_id)
                    
                    # Predict every iteration
                    self.predictor.predict(node_id)
                
                train_counter += 1
                time.sleep(5)  # Match heartbeat interval
                
            except Exception as e:
                logger.error(f"Prediction loop error: {e}")
                time.sleep(5)