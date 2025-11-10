import logging
from typing import List, Dict, Tuple, Optional
import docker

logger = logging.getLogger(__name__)

class Scheduler:
    """Kubernetes-style scheduler with filter, score, and bind phases"""
    
    def __init__(self, client: docker.DockerClient, nodes: Dict, pods: Dict):
        self.client = client
        self.nodes = nodes
        self.pods = pods
    
    def schedule(self, cpu_required: int, image: str = "nginx:latest") -> Tuple[Optional[str], Optional[str]]:
        """
        Schedule a pod using filter->score->bind workflow
        Returns: (node_id, error_message)
        """
        # Phase 1: Filter
        feasible_nodes = self._filter_nodes(cpu_required)
        if not feasible_nodes:
            return None, f"No node has {cpu_required} CPU cores available"
        
        # Phase 2: Score
        scored_nodes = self._score_nodes(feasible_nodes, cpu_required)
        best_node = max(scored_nodes, key=lambda x: x[1])[0]
        
        # Phase 3: Bind
        pod_id, error = self._bind_pod(best_node, cpu_required, image)
        
        return (pod_id, None) if pod_id else (None, error)
    
    def _filter_nodes(self, cpu_required: int) -> List[str]:
        """Filter nodes that can accommodate the pod"""
        feasible = []
        
        for node_id, node_info in self.nodes.items():
            # Filter 1: Node must be healthy
            if node_info['status'] != 'healthy':
                logger.debug(f"Filter: Node {node_id} unhealthy")
                continue
            
            # Filter 2: Container must be running
            try:
                container = self.client.containers.get(node_info['container_id'])
                if container.status != 'running':
                    logger.debug(f"Filter: Node {node_id} container not running")
                    node_info['status'] = 'unhealthy'
                    continue
            except docker.errors.NotFound:
                logger.debug(f"Filter: Node {node_id} container not found")
                node_info['status'] = 'unhealthy'
                continue
            except Exception as e:
                logger.warning(f"Filter: Error checking node {node_id}: {e}")
                continue
            
            # Filter 3: Sufficient CPU resources
            current_usage = sum(
                self.pods[pid]['cpu_required'] 
                for pid in node_info['pods'] 
                if pid in self.pods
            )
            available = node_info['cpu_capacity'] - current_usage
            node_info['cpu_available'] = available
            
            if available >= cpu_required:
                feasible.append(node_id)
                logger.debug(f"Filter: Node {node_id} passed ({available} CPU available)")
            else:
                logger.debug(f"Filter: Node {node_id} insufficient CPU ({available} < {cpu_required})")
        
        logger.info(f"Filter phase: {len(feasible)}/{len(self.nodes)} nodes feasible")
        return feasible
    
    def _score_nodes(self, feasible_nodes: List[str], cpu_required: int) -> List[Tuple[str, float]]:
        """Score feasible nodes (higher is better)"""
        scored = []
        
        for node_id in feasible_nodes:
            node_info = self.nodes[node_id]
            score = 0.0
            
            # Score 1: Least Requested (40% weight)
            # Prefer nodes with more available CPU
            cpu_utilization = 1 - (node_info['cpu_available'] / node_info['cpu_capacity'])
            least_requested_score = (1 - cpu_utilization) * 40
            
            # Score 2: Balanced Resource Allocation (30% weight)
            # Prefer nodes where this pod doesn't create imbalance
            post_alloc_util = 1 - ((node_info['cpu_available'] - cpu_required) / node_info['cpu_capacity'])
            balance_score = (1 - abs(0.7 - post_alloc_util)) * 30
            
            # Score 3: Pod Density (30% weight)
            # Prefer nodes with fewer pods for better distribution
            max_pods = node_info['cpu_capacity'] * 2
            pod_count = len(node_info['pods'])
            density_score = (1 - (pod_count / max_pods)) * 30
            
            score = least_requested_score + balance_score + density_score
            scored.append((node_id, score))
            
            logger.debug(
                f"Score: Node {node_id} = {score:.2f} "
                f"(LeastReq={least_requested_score:.2f}, "
                f"Balance={balance_score:.2f}, "
                f"Density={density_score:.2f})"
            )
        
        scored.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Score phase: Best node is {scored[0][0]} with score {scored[0][1]:.2f}")
        return scored
    
    def _bind_pod(self, node_id: str, cpu_required: int, image: str) -> Tuple[Optional[str], Optional[str]]:
        """Bind pod to node by creating container and updating state"""
        import uuid
        
        pod_id = str(uuid.uuid4())
        node_info = self.nodes[node_id]
        
        try:
            # Create pod container
            host_port = 10000 + (hash(pod_id) % 10000)
            
            pod_container = self.client.containers.run(
                image=image,
                detach=True,
                name=f'pod-{pod_id}',
                ports={'80/tcp': host_port},
                environment={
                    'POD_ID': pod_id,
                    'NODE_ID': node_id
                }
            )
            
            logger.info(f"Bind: Created container {pod_container.name} on node {node_id}")
            
            # Update node state
            node_info['cpu_available'] -= cpu_required
            node_info['pods'].append(pod_id)
            
            # Update pod state
            self.pods[pod_id] = {
                'node_id': node_id,
                'cpu_required': cpu_required,
                'created_at': __import__('datetime').datetime.now().isoformat(),
                'container_id': pod_container.id,
                'status': 'running',
                'image': image,
                'host_port': host_port
            }
            
            logger.info(
                f"Bind: Pod {pod_id} bound to node {node_id} "
                f"(accessible at http://localhost:{host_port})"
            )
            return pod_id, None
            
        except docker.errors.APIError as e:
            logger.error(f"Bind: Docker API error: {e}")
            return None, f"Failed to create pod container: {str(e)}"
        except Exception as e:
            logger.error(f"Bind: Unexpected error: {e}")
            return None, f"Unexpected error: {str(e)}"