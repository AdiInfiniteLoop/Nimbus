import logging
import numpy as np
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import threading
import time
import csv
import os
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class CPUPredictor:
    """Enhanced ML-based CPU usage predictor with monitoring and parallel training"""
    
    def __init__(self, history_window=120, prediction_interval=30):
        self.history_window = history_window
        self.prediction_interval = prediction_interval
        self.node_histories = {}
        self.models = {}
        self.scalers = {}
        self.predictions = {}
        self.training_metrics = {}
        self.training_times = {}  # Track training duration
        self.last_training = {}   # Track when last trained
        self.lock = threading.Lock()
        
        # Model hyperparameters (tuned for speed vs accuracy)
        self.n_estimators = 100
        self.max_depth = 15
        self.min_samples_split = 4
        self.min_samples_leaf = 2
        
        logger.info(f"CPUPredictor initialized (window={history_window}, interval={prediction_interval}s)")
    
    def add_metric(self, node_id: str, cpu_percent: float, memory_percent: float, 
                   pod_count: int, total_cpu_capacity: int):
        """Add a new metric data point for a node"""
        with self.lock:
            if node_id not in self.node_histories:
                self.node_histories[node_id] = deque(maxlen=self.history_window)
            
            now = datetime.now()
            metric = {
                'timestamp': now,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'pod_count': pod_count,
                'total_cpu_capacity': total_cpu_capacity,
                'hour': now.hour,
                'minute': now.minute,
                'day_of_week': now.weekday(),
                'is_business_hours': 9 <= now.hour <= 17,
            }
            
            self.node_histories[node_id].append(metric)
            logger.debug(f"Added metric for node {node_id}: CPU={cpu_percent:.2f}%")
    
    def _calculate_advanced_features(self, history: List[Dict]) -> Optional[np.ndarray]:
        """Extract rich features focusing on patterns, NOT current value"""
        if len(history) < 15:
            return None
        
        # Get different time windows
        very_recent = history[-6:]
        recent = history[-12:]
        short_term = history[-24:]
        medium_term = history[-48:]
        long_term = history[-96:] if len(history) >= 96 else history
        
        cpu_very_recent = [m['cpu_percent'] for m in very_recent]
        cpu_recent = [m['cpu_percent'] for m in recent]
        cpu_short = [m['cpu_percent'] for m in short_term]
        cpu_medium = [m['cpu_percent'] for m in medium_term]
        cpu_long = [m['cpu_percent'] for m in long_term]
        
        features = []
        
        # Trend features
        features.append(np.mean(cpu_very_recent[-3:]) - np.mean(cpu_very_recent[:3]))
        features.append(np.mean(cpu_recent[-6:]) - np.mean(cpu_recent[:6]))
        features.append(np.mean(cpu_short[-12:]) - np.mean(cpu_short[:12]))
        
        # Acceleration
        if len(cpu_short) >= 8:
            trend1 = cpu_short[-4] - cpu_short[-8]
            trend2 = cpu_short[-1] - cpu_short[-4]
            features.append(trend2 - trend1)
        else:
            features.append(0)
        
        # Volatility
        features.append(np.std(cpu_recent))
        features.append(np.std(cpu_short))
        features.append(np.std(cpu_medium))
        
        # Rate of change
        if len(cpu_recent) >= 4:
            changes = [cpu_recent[i] - cpu_recent[i-1] for i in range(1, len(cpu_recent))]
            features.append(np.mean(changes))
            features.append(np.std(changes))
            features.append(max(changes))
            features.append(min(changes))
        else:
            features.extend([0, 0, 0, 0])
        
        # Moving averages
        features.append(np.mean(cpu_very_recent))
        features.append(np.mean(cpu_recent))
        features.append(np.mean(cpu_short))
        features.append(np.mean(cpu_medium))
        
        # Momentum
        if len(cpu_medium) >= 12:
            ma_fast = np.mean(cpu_medium[-12:])
            ma_slow = np.mean(cpu_medium)
            features.append(ma_fast - ma_slow)
        else:
            features.append(0)
        
        # Statistical features
        features.append(np.min(cpu_recent))
        features.append(np.max(cpu_recent))
        features.append(np.percentile(cpu_short, 25))
        features.append(np.percentile(cpu_short, 75))
        
        # Historical context
        if len(cpu_long) > 24:
            current_avg = np.mean(cpu_recent)
            historical_avg = np.mean(cpu_long[:-24])
            features.append(current_avg - historical_avg)
            features.append(current_avg / (historical_avg + 0.1))
        else:
            features.extend([0, 1])
        
        # Workload features
        features.append(history[-1]['pod_count'])
        features.append(history[-1]['total_cpu_capacity'])
        
        if len(history) >= 12:
            pod_change = history[-1]['pod_count'] - history[-12]['pod_count']
            features.append(pod_change)
        else:
            features.append(0)
        
        # Memory
        memory_values = [m['memory_percent'] for m in recent]
        features.append(np.mean(memory_values))
        features.append(np.std(memory_values))
        
        # Temporal features
        current = history[-1]
        features.append(current['hour'] / 24.0)
        features.append(current['minute'] / 60.0)
        features.append(current['day_of_week'] / 7.0)
        features.append(float(current['is_business_hours']))
        features.append(np.sin(2 * np.pi * current['hour'] / 24))
        features.append(np.cos(2 * np.pi * current['hour'] / 24))
        
        return np.array(features).reshape(1, -1)
    
    def _prepare_training_data(self, history: List[Dict]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare X and y for training with enhanced features"""
        if len(history) < 30:
            return None, None
        
        X, y = [], []
        steps_ahead = max(1, self.prediction_interval // 5)
        
        for i in range(20, len(history) - steps_ahead):
            snapshot = list(history)[:i]
            features = self._calculate_advanced_features(snapshot)
            
            if features is not None:
                future_idx = min(i + steps_ahead, len(history) - 1)
                target_cpu = history[future_idx]['cpu_percent']
                
                X.append(features[0])
                y.append(target_cpu)
        
        if len(X) == 0:
            return None, None
        
        return np.array(X), np.array(y)
    
    def train_model(self, node_id: str) -> bool:
        """Train or retrain model for a specific node with timing"""
        start_time = time.time()
        
        with self.lock:
            if node_id not in self.node_histories:
                return False
            history = list(self.node_histories[node_id])
        
        if len(history) < 30:
            logger.debug(f"Node {node_id}: Insufficient data ({len(history)}/30 points)")
            return False
        
        X, y = self._prepare_training_data(history)
        
        if X is None or len(X) < 10:
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
                min_samples_leaf=self.min_samples_leaf,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_scaled, y)
            
            # Calculate metrics
            train_score = model.score(X_scaled, y)
            y_pred = model.predict(X_scaled)
            mae = np.mean(np.abs(y - y_pred))
            rmse = np.sqrt(np.mean((y - y_pred) ** 2))
            
            training_duration = time.time() - start_time
            
            with self.lock:
                self.models[node_id] = model
                self.scalers[node_id] = scaler
                self.training_times[node_id] = training_duration
                self.last_training[node_id] = datetime.now()
                self.training_metrics[node_id] = {
                    'r2_score': train_score,
                    'mae': mae,
                    'rmse': rmse,
                    'samples': len(X),
                    'trained_at': datetime.now().isoformat(),
                    'training_duration_ms': int(training_duration * 1000),
                    'features_count': X.shape[1]
                }
            
            logger.info(
                f"Node {node_id}: Model trained in {training_duration:.3f}s - "
                f"R²={train_score:.3f}, MAE={mae:.2f}%, samples={len(X)}"
            )
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
        
        if len(history) < 15:
            return None
        
        try:
            features = self._calculate_advanced_features(history)
            if features is None:
                return None
            
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)[0]
            prediction = max(0.0, min(100.0, prediction))
            
            # Calculate freshness metrics
            now = datetime.now()
            data_age = (now - history[-1]['timestamp']).total_seconds()
            model_age = (now - self.last_training.get(node_id, now)).total_seconds()
            
            with self.lock:
                metrics = self.training_metrics.get(node_id, {})
                self.predictions[node_id] = {
                    'predicted_cpu': prediction,
                    'timestamp': now,
                    'current_cpu': history[-1]['cpu_percent'],
                    'confidence': metrics.get('r2_score', 0),
                    'freshness': {
                        'data_age_seconds': data_age,
                        'model_age_seconds': model_age,
                        'is_stale': data_age > 30 or model_age > 300,
                        'last_training': self.last_training.get(node_id, now).isoformat()
                    },
                    'quality': {
                        'r2_score': metrics.get('r2_score', 0),
                        'mae': metrics.get('mae', 0),
                        'rmse': metrics.get('rmse', 0),
                        'samples': metrics.get('samples', 0),
                        'is_accurate': metrics.get('r2_score', 0) > 0.5
                    }
                }
            
            logger.debug(
                f"Node {node_id}: Predicted={prediction:.2f}%, "
                f"Current={history[-1]['cpu_percent']:.2f}%, "
                f"DataAge={data_age:.1f}s"
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Node {node_id}: Prediction failed - {e}")
            return None
    
    def get_prediction(self, node_id: str) -> Optional[Dict]:
        """Get the latest prediction with freshness info"""
        with self.lock:
            pred = self.predictions.get(node_id)
            if pred:
                return pred.copy()
            return None
    
    def get_all_predictions(self) -> Dict:
        """Get predictions for all nodes"""
        with self.lock:
            return {
                node_id: pred.copy() 
                for node_id, pred in self.predictions.items()
            }
    
    def get_monitoring_stats(self) -> Dict:
        """Get comprehensive monitoring statistics"""
        with self.lock:
            stats = {
                'total_nodes': len(self.node_histories),
                'trained_models': len(self.models),
                'active_predictions': len(self.predictions),
                'nodes': {}
            }
            
            now = datetime.now()
            for node_id in self.node_histories.keys():
                history = self.node_histories[node_id]
                last_training = self.last_training.get(node_id)
                
                node_stat = {
                    'data_points': len(history),
                    'data_age_seconds': (now - history[-1]['timestamp']).total_seconds() if history else None,
                    'model_exists': node_id in self.models,
                    'model_age_seconds': (now - last_training).total_seconds() if last_training else None,
                    'last_training_duration_ms': self.training_times.get(node_id, 0) * 1000,
                    'metrics': self.training_metrics.get(node_id, {}),
                    'ready_for_training': len(history) >= 30,
                    'needs_retraining': last_training and (now - last_training).total_seconds() > 300 if last_training else True
                }
                
                stats['nodes'][node_id] = node_stat
            
            return stats
    
    def export_to_csv(self, node_id: Optional[str] = None, filepath: str = 'predictions_export.csv'):
        """Export predictions and metrics to CSV"""
        with self.lock:
            if node_id:
                nodes_to_export = {node_id: self.node_histories.get(node_id)}
            else:
                nodes_to_export = self.node_histories
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                writer.writerow([
                    'node_id', 'timestamp', 'cpu_percent', 'memory_percent', 
                    'pod_count', 'predicted_cpu', 'prediction_error', 
                    'model_r2', 'model_mae', 'model_rmse', 'training_time_ms',
                    'data_age_seconds', 'model_age_seconds'
                ])
                
                for nid, history in nodes_to_export.items():
                    if not history:
                        continue
                    
                    prediction = self.predictions.get(nid)
                    metrics = self.training_metrics.get(nid, {})
                    
                    for record in history:
                        pred_cpu = prediction['predicted_cpu'] if prediction else None
                        error = abs(record['cpu_percent'] - pred_cpu) if pred_cpu else None
                        
                        data_age = prediction.get('freshness', {}).get('data_age_seconds') if prediction else None
                        model_age = prediction.get('freshness', {}).get('model_age_seconds') if prediction else None
                        
                        writer.writerow([
                            nid,
                            record['timestamp'].isoformat(),
                            record['cpu_percent'],
                            record['memory_percent'],
                            record['pod_count'],
                            pred_cpu,
                            error,
                            metrics.get('r2_score'),
                            metrics.get('mae'),
                            metrics.get('rmse'),
                            metrics.get('training_duration_ms'),
                            data_age,
                            model_age
                        ])
            
            logger.info(f"Exported predictions to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None
    
    def cleanup_node(self, node_id: str):
        """Remove all data for a node"""
        with self.lock:
            self.node_histories.pop(node_id, None)
            self.models.pop(node_id, None)
            self.scalers.pop(node_id, None)
            self.predictions.pop(node_id, None)
            self.training_metrics.pop(node_id, None)
            self.training_times.pop(node_id, None)
            self.last_training.pop(node_id, None)
        logger.info(f"Node {node_id}: Cleaned up predictor data")


class PredictorManager:
    """Manages continuous prediction updates with parallel training"""
    
    def __init__(self, predictor: CPUPredictor, nodes: Dict, pods: Dict, max_workers: int = 4):
        self.predictor = predictor
        self.nodes = nodes
        self.pods = pods
        self.max_workers = max_workers
        self.running = False
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"PredictorManager initialized with {max_workers} workers")
    
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
        self.executor.shutdown(wait=True)
        logger.info("PredictorManager stopped")
    
    def _prediction_loop(self):
        """Continuously train and predict with parallel training"""
        train_counter = 0
        
        while self.running:
            try:
                node_ids = list(self.nodes.keys())
                
                # Parallel training every 24 iterations (2 minutes)
                if train_counter % 24 == 0 and node_ids:
                    logger.info(f"Starting parallel training for {len(node_ids)} nodes")
                    start_time = time.time()
                    
                    # Submit all training jobs
                    futures = [
                        self.executor.submit(self.predictor.train_model, nid)
                        for nid in node_ids
                    ]
                    
                    # Wait for completion
                    results = [f.result() for f in futures]
                    
                    duration = time.time() - start_time
                    success_count = sum(1 for r in results if r)
                    
                    logger.info(
                        f"Parallel training completed in {duration:.2f}s: "
                        f"{success_count}/{len(node_ids)} successful"
                    )
                
                # Predict for all nodes every iteration
                for node_id in node_ids:
                    self.predictor.predict(node_id)
                
                train_counter += 1
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Prediction loop error: {e}")
                time.sleep(5)