import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional


logger = logging.getLogger(__name__)

class AutoScaler:
    """Intelligent auto-scaling based on ML predictions and current load"""
    
    def __init__(self, nodes: Dict, pods: Dict, predictor, node_manager, email_alerter=None, config: Dict = None):

        self.nodes = nodes
        self.pods = pods
        self.predictor = predictor
        self.node_manager = node_manager
        self.email_alerter = email_alerter
        self.alerted = False
        # Configuration
        self.enabled = False
        self.config = config or {
            'scale_up_threshold': 75,      # % CPU predicted
            'scale_down_threshold': 30,    # % CPU predicted
            'min_nodes': 1,
            'max_nodes': 10,
            'scale_up_cpu': 4,            # CPU for new nodes
            'cooldown_seconds': 60,       # Wait between scaling actions
            'prediction_window': 5,       # Check predictions for 5 intervals
        }
        
        self.last_scale_action = None
        self.scaling_history = []
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        logger.info("AutoScaler initialized")
    
    def enable(self):
        """Enable auto-scaling"""
        with self.lock:
            self.enabled = True
        logger.info("Auto-scaling ENABLED")
    
    def disable(self):
        """Disable auto-scaling"""
        with self.lock:
            self.enabled = False
        logger.info("Auto-scaling DISABLED")
    
    def is_enabled(self) -> bool:
        """Check if auto-scaling is enabled"""
        with self.lock:
            return self.enabled
    
    def update_config(self, config: Dict):
        """Update auto-scaling configuration"""
        with self.lock:
            self.config.update(config)
        logger.info(f"Auto-scaler config updated: {config}")
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        with self.lock:
            return self.config.copy()
    
    def start(self):
        """Start the auto-scaling loop"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._autoscale_loop, daemon=True)
        self.thread.start()
        logger.info("AutoScaler thread started")
    
    def stop(self):
        """Stop the auto-scaling loop"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("AutoScaler thread stopped")
    
    def _can_scale(self) -> bool:
        """Check if we're in cooldown period"""
        if self.last_scale_action is None:
            return True
        
        elapsed = (datetime.now() - self.last_scale_action).total_seconds()
        return elapsed >= self.config['cooldown_seconds']
    
    def _calculate_cluster_metrics(self) -> Dict:
        """Calculate cluster-wide metrics"""
        if not self.nodes:
            return {
                'avg_cpu_usage': 0,
                'avg_cpu_predicted': 0,
                'total_nodes': 0,
                'healthy_nodes': 0,
                'total_pods': 0
            }
        
        total_cpu = 0
        used_cpu = 0
        predicted_cpu = 0
        healthy_count = 0
        prediction_count = 0
        
        for node_id, node in self.nodes.items():
            total_cpu += node['cpu_capacity']
            used_cpu += (node['cpu_capacity'] - node['cpu_available'])
            
            if node['status'] == 'healthy':
                healthy_count += 1
            
            # Get prediction
            pred = self.predictor.get_prediction(node_id)
            if pred and pred.get('predicted_cpu'):
                predicted_cpu += pred['predicted_cpu']
                prediction_count += 1
        
        avg_cpu_usage = (used_cpu / total_cpu * 100) if total_cpu > 0 else 0
        avg_cpu_predicted = (predicted_cpu / prediction_count) if prediction_count > 0 else avg_cpu_usage
        
        return {
            'avg_cpu_usage': avg_cpu_usage,
            'avg_cpu_predicted': avg_cpu_predicted,
            'total_nodes': len(self.nodes),
            'healthy_nodes': healthy_count,
            'total_pods': sum(len(n['pods']) for n in self.nodes.values())
        }
    
    def _should_scale_up(self, metrics: Dict) -> bool:
        """Determine if we should scale up"""
        # Check thresholds
        if metrics['avg_cpu_predicted'] < self.config['scale_up_threshold']:
            return False
        
        # Check max nodes limit
        if metrics['total_nodes'] >= self.config['max_nodes']:
            logger.info(f"Cannot scale up: at max nodes ({self.config['max_nodes']})")
            return False
        
        return True
    
    def _should_scale_down(self, metrics: Dict) -> bool:
        """Determine if we should scale down"""
        # Check thresholds
        if metrics['avg_cpu_predicted'] > self.config['scale_down_threshold']:
            return False
        
        # Check min nodes limit
        if metrics['total_nodes'] <= self.config['min_nodes']:
            logger.info(f"Cannot scale down: at min nodes ({self.config['min_nodes']})")
            return False
        
        # Only scale down if we have very low load
        if metrics['avg_cpu_usage'] > self.config['scale_down_threshold']:
            return False
        
        return True
    
    def _find_node_to_remove(self) -> Optional[str]:
        """Find the best node to remove (least loaded)"""
        min_usage = float('inf')
        target_node = None
        
        for node_id, node in self.nodes.items():
            if node['status'] != 'healthy':
                continue
            
            usage = node['cpu_capacity'] - node['cpu_available']
            if usage < min_usage:
                min_usage = usage
                target_node = node_id
        
        return target_node
    
    def _scale_up(self, metrics: Dict):
        """Add a new node"""
        logger.info(
            f"SCALING UP: Predicted CPU {metrics['avg_cpu_predicted']:.1f}% "
            f"exceeds threshold {self.config['scale_up_threshold']}%"
        )
        
        result = self.node_manager.add_node(self.config['scale_up_cpu'])
        # ===== REMOVE THE EXACT OVERLOADED NODE =====
        try:
            overloaded_node = max(
                self.nodes,
                key=lambda nid: self.nodes[nid]['cpu_capacity'] - self.nodes[nid]['cpu_available']
            )

            if overloaded_node != result:
                logger.info(f"Removing overloaded node {overloaded_node} to trigger pod reschedule")
                self.node_manager.remove_node(overloaded_node)
            else:
                logger.info("New node is the overloaded node (rare case); skipping removal")

        except Exception as e:
            logger.error(f"Failed to remove overloaded node after scale-up: {e}")
        # ============================================

        if isinstance(result, dict) and 'error' in result:
            logger.error(f"Scale up failed: {result['error']}")
            return False
        
        self.last_scale_action = datetime.now()
        self.scaling_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'scale_up',
            'reason': f"Predicted CPU {metrics['avg_cpu_predicted']:.1f}%",
            'node_id': result,
            'nodes_before': metrics['total_nodes'],
            'nodes_after': metrics['total_nodes'] + 1
        })
        
        logger.info(f"Successfully scaled up: Added node {result}")
        return True
    
    def _scale_down(self, metrics: Dict):
        """Remove a node"""
        target_node = self._find_node_to_remove()
        
        if not target_node:
            logger.warning("Scale down aborted: No suitable node found")
            return False
        
        logger.info(
            f"SCALING DOWN: Predicted CPU {metrics['avg_cpu_predicted']:.1f}% "
            f"below threshold {self.config['scale_down_threshold']}%"
        )
        
        result = self.node_manager.remove_node(target_node)
        
        if 'error' in result:
            logger.error(f"Scale down failed: {result['error']}")
            return False
        
        self.last_scale_action = datetime.now()
        self.scaling_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'scale_down',
            'reason': f"Predicted CPU {metrics['avg_cpu_predicted']:.1f}%",
            'node_id': target_node,
            'nodes_before': metrics['total_nodes'],
            'nodes_after': metrics['total_nodes'] - 1,
            'rescheduled_pods': result.get('rescheduled_pods', 0)
        })
        
        logger.info(f"Successfully scaled down: Removed node {target_node}")
        return True
    
    def _autoscale_loop(self):
        """Main auto-scaling loop"""
        logger.info("Auto-scaling loop started")
        
        while self.running:
            try:
                # Only run if enabled
                if not self.is_enabled():
                    time.sleep(10)
                    continue
                
                # Check if we can scale (cooldown)
                if not self._can_scale():
                    time.sleep(5)
                    continue
                
                # Calculate metrics
                metrics = self._calculate_cluster_metrics()
                # ===== EMAIL ALERT FOR HIGH CPU USAGE =====
                cpu_percent = metrics['avg_cpu_usage']
                threshold = self.config['scale_up_threshold']

                if cpu_percent >= threshold:
                    if not self.alerted and self.email_alerter:
                        self.email_alerter.high_load_alert(cpu_percent)
                        logger.info(f"EMAIL ALERT SENT: CPU={cpu_percent:.1f}% >= threshold {threshold}%")
                        self.alerted = True
                else:
                    self.alerted = False
                # Skip if no nodes
                if metrics['total_nodes'] == 0:
                    time.sleep(10)
                    continue
                
                logger.debug(
                    f"Auto-scaler check: Current={metrics['avg_cpu_usage']:.1f}%, "
                    f"Predicted={metrics['avg_cpu_predicted']:.1f}%, "
                    f"Nodes={metrics['total_nodes']}"
                )
                
                # Decide scaling action (scale up takes priority)
                if self._should_scale_up(metrics):
                    self._scale_up(metrics)
                elif self._should_scale_down(metrics):
                    self._scale_down(metrics)
                                
            except Exception as e:
                logger.error(f"Auto-scaler loop error: {e}")
            time.sleep(20)
    
    def get_status(self) -> Dict:
        """Get auto-scaler status"""
        with self.lock:
            metrics = self._calculate_cluster_metrics()
            
            return {
                'enabled': self.enabled,
                'config': self.config.copy(),
                'last_action': self.last_scale_action.isoformat() if self.last_scale_action else None,
                'can_scale_now': self._can_scale(),
                'current_metrics': metrics,
                'scaling_history': self.scaling_history[-10:],  # Last 10 actions
                'recommendations': {
                    'should_scale_up': self._should_scale_up(metrics),
                    'should_scale_down': self._should_scale_down(metrics)
                }
            }
    
    def get_history(self, limit: int = 50) -> list:
        """Get scaling history"""
        with self.lock:
            return self.scaling_history[-limit:]
    
    def clear_history(self):
        """Clear scaling history"""
        with self.lock:
            self.scaling_history = []
        logger.info("Scaling history cleared")