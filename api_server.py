from flask import Flask, request, jsonify
import docker
import threading
import time
from datetime import datetime
import uuid
import sys
import os
import logging
import multiprocessing
import json

from flask_cors import CORS
from scheduling import Scheduler
from ml_predictor import CPUPredictor, PredictorManager
from sklearn.ensemble import RandomForestRegressor  

from auto_scaler import AutoScaler
from config_manager import ClusterConfigManager, LogExporter, EmailAlerter
from flask import send_file
import tempfile


# Configure logging with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Get system CPU count
SYSTEM_CPU_COUNT = multiprocessing.cpu_count()
MAX_NODE_CPU = min(8, SYSTEM_CPU_COUNT)  # Cap at 8 or system CPU count, whichever is lower
MAX_POD_CPU = min(6, SYSTEM_CPU_COUNT)   # Cap at 6 or system CPU count, whichever is lower

logger.info(f"System CPU count: {SYSTEM_CPU_COUNT}")
logger.info(f"Maximum node CPU capacity: {MAX_NODE_CPU}")
logger.info(f"Maximum pod CPU requirement: {MAX_POD_CPU}")

app = Flask(__name__)
CORS(app)

# In-memory storage for cluster state
nodes = {}  # {node_id: {cpu_capacity, cpu_available, pods, last_heartbeat, status}}
pods = {}   # {pod_id: {node_id, cpu_required}}

def cleanup_orphaned_containers():
    """Clean up containers that exist in our state but not in Docker"""
    logger.info("Cleaning up orphaned containers...")
    
    # Get all Docker containers
    docker_containers = {c.id: c for c in client.containers.list(all=True)}
    
    # Clean up nodes
    for node_id, node_info in list(nodes.items()):
        if 'container_id' in node_info:
            if node_info['container_id'] not in docker_containers:
                logger.warning(f"Removing node {node_id} - container not found in Docker")
                del nodes[node_id]
    
    # Clean up pods
    for pod_id, pod_info in list(pods.items()):
        if 'container_id' in pod_info:
            if pod_info['container_id'] not in docker_containers:
                logger.warning(f"Removing pod {pod_id} - container not found in Docker")
                # Remove pod from its node's pod list
                if pod_info['node_id'] in nodes:
                    nodes[pod_info['node_id']]['pods'] = [p for p in nodes[pod_info['node_id']]['pods'] if p != pod_id]
                del pods[pod_id]

# Initialize the system
try:
    client = docker.from_env()
    # Test Docker connection
    client.ping()
    logger.info("Successfully connected to Docker")    

    cpu_predictor = CPUPredictor(history_window=60, prediction_interval=30)
    predictor_manager = None 

    config_manager = ClusterConfigManager(nodes, pods, client)
    log_exporter = LogExporter()
    email_alerter = EmailAlerter() 
    autoscaler = None  # Will be initialized after Flask app starts

    email_alerter.update_config({
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "pleasedontbyteme@gmail.com",
        "sender_password": "haoa xedk hheu vlge",
        "recipient_emails": ["2022cs_adityapradhan_a@nie.ac.in"]
    })
    email_alerter.enable()

    # List all existing containers
    existing_containers = client.containers.list()
    logger.info(f"Found {len(existing_containers)} existing containers")
    for container in existing_containers:
        logger.info(f"Container: {container.name} (ID: {container.short_id})")
    
    # Clean up any orphaned containers
    cleanup_orphaned_containers()
    
except docker.errors.DockerException as e:
    logger.error("Error: Docker is not running or not properly installed.")
    logger.error("Please make sure Docker Desktop is installed and running.")
    logger.error("You can download Docker Desktop from: https://www.docker.com/products/docker-desktop/")
    sys.exit(1)

class NodeManager:
    @staticmethod
    def get_total_allocated_cpu():
        return sum(node['cpu_capacity'] for node in nodes.values())

    @staticmethod
    def add_node(cpu_capacity):
        node_id = str(uuid.uuid4())
        try:
            logger.info(f"Creating new node container with ID: {node_id}")
            logger.info(f"CPU Capacity: {cpu_capacity} cores")
            
            # Validate CPU capacity
            if cpu_capacity <= 0:
                error_msg = f"Invalid CPU capacity: {cpu_capacity} (must be positive)"
                logger.error(error_msg)
                return {'error': error_msg}
            
            if cpu_capacity > MAX_NODE_CPU:
                error_msg = f"CPU capacity too high: {cpu_capacity} (maximum is {MAX_NODE_CPU})"
                logger.error(error_msg)
                return {'error': error_msg}
            
            # Check if adding this node would exceed system capacity
            total_allocated = NodeManager.get_total_allocated_cpu()
            if total_allocated + cpu_capacity > SYSTEM_CPU_COUNT:
                error_msg = f"Cannot add node: Total CPU capacity ({total_allocated + cpu_capacity}) would exceed system capacity ({SYSTEM_CPU_COUNT})"
                logger.error(error_msg)
                return {'error': error_msg}
            
            try:
                container = client.containers.run(
                    'python:3.9-slim',
                    command='tail -f /dev/null',
                    detach=True,
                    name=f'node-{node_id}'
                )
                
                logger.info(f"Container created successfully: {container.name} (ID: {container.short_id})")
                
                # Only add the node to our data structure if container creation succeeded
                nodes[node_id] = {
                    'cpu_capacity': cpu_capacity,
                    'cpu_available': cpu_capacity,
                    'pods': [],
                    'last_heartbeat': datetime.now(),
                    'status': 'healthy',
                    'container_id': container.id
                }
                
                # Start heartbeat thread for this node
                threading.Thread(target=HealthMonitor.start_heartbeat, args=(node_id,), daemon=True).start()
                logger.info(f"Started heartbeat monitoring for node {node_id}")
                return node_id
            except docker.errors.APIError as e:
                logger.error(f"Docker API error while creating container: {str(e)}")
                return {'error': f'Docker API error: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error while creating node: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def remove_node(node_id):
        if node_id in nodes:
            try:
                logger.info(f"Removing node: {node_id}")
                
                # Store pods that need to be rescheduled
                pods_to_reschedule = nodes[node_id]['pods'].copy()
                logger.info(f"Found {len(pods_to_reschedule)} pods to reschedule")
                
                # Get container information from our data structure
                container_id = nodes[node_id]['container_id']
                
                # Try to get the container from Docker
                try:
                    container = client.containers.get(container_id)
                    
                    # Try to stop and remove the container
                    try:
                        container.stop()
                        container.remove()
                        logger.info(f"Container for node {node_id} stopped and removed successfully")
                    except docker.errors.APIError as e:
                        logger.error(f"Error stopping/removing container: {str(e)}")
                        return {'error': f'Docker API error: {str(e)}'}
                except docker.errors.NotFound:
                    logger.warning(f"Container for node {node_id} not found in Docker, may have been already removed")
                
                # Remove the node from our data structure
                del nodes[node_id]
                logger.info(f"Successfully removed node {node_id} from cluster")

                cpu_predictor.cleanup_node(node_id)

                # Now reschedule all pods from the removed node
                rescheduled_pods = []
                failed_pods = []
                
                for pod_id in pods_to_reschedule:
                    if pod_id in pods:
                        pod_info = pods[pod_id]
                        logger.info(f"Attempting to reschedule pod {pod_id}")
                        
                        # Try to stop and remove the pod container
                        try:
                            if 'container_id' in pod_info:
                                container = client.containers.get(pod_info['container_id'])
                                container.stop()
                                container.remove()
                        except (docker.errors.NotFound, docker.errors.APIError) as e:
                            logger.warning(f"Error removing pod container: {str(e)}")
                        
                        # Try to reschedule the pod
                        new_pod_id = PodScheduler.schedule_pod(pod_info['cpu_required'], pod_info.get('image', 'nginx:latest'))
                        
                        if isinstance(new_pod_id, dict):  # Scheduling failed
                            failed_pods.append(pod_id)
                            logger.error(f"Failed to reschedule pod {pod_id}")
                        else:
                            rescheduled_pods.append(pod_id)
                            logger.info(f"Successfully rescheduled pod {pod_id}")
                email_alerter.node_recovery_alert(node_id)  # If node was unhealthy

                return {
                    'message': f'Node {node_id} removed successfully',
                    'rescheduled_pods': len(rescheduled_pods),
                    'failed_pods': len(failed_pods)
                }
            except Exception as e:
                logger.error(f"Error removing node {node_id}: {str(e)}")
                return {'error': str(e)}
        logger.error(f"Node not found: {node_id}")
        return {'error': 'Node not found'}

class PodScheduler:
    @staticmethod
    def schedule_pod(cpu_required, image="nginx:latest"):
        logger.info(f"Attempting to schedule pod requiring {cpu_required} CPU cores, image: {image}")
        
        # Validate CPU requirement
        if cpu_required <= 0:
            logger.error(f"Invalid CPU requirement: {cpu_required} (must be positive)")
            return {'error': 'CPU requirement must be positive'}
        
        if cpu_required > MAX_POD_CPU:
            logger.error(f"CPU requirement too high: {cpu_required} (maximum is {MAX_POD_CPU})")
            return {'error': f'Maximum CPU requirement per pod is {MAX_POD_CPU} cores'}
        
        # Check if we have any nodes
        if not nodes:
            logger.error("No nodes available in the cluster")
            return {'error': 'No nodes available in the cluster'}
        
        scheduler = Scheduler(client, nodes, pods)
        pod_id, error = scheduler.schedule(cpu_required, image)
    
        if error:
            logger.error(f"Scheduling failed: {error}")
            return {'error': error}
        
        return pod_id

    @staticmethod
    def reschedule_pods(failed_node_id):
        if failed_node_id not in nodes:
            logger.error(f"Failed node not found: {failed_node_id}")
            return
        
        failed_pods = nodes[failed_node_id]['pods']
        logger.info(f"Rescheduling {len(failed_pods)} pods from failed node {failed_node_id}")
        
        for pod_id in failed_pods:
            if pod_id not in pods:
                logger.warning(f"Pod {pod_id} not found in pods list, skipping")
                continue
                
            pod_info = pods[pod_id]
            logger.info(f"Attempting to reschedule pod {pod_id}")
            
            # Try to stop and remove the failed pod container if it exists
            try:
                if 'container_id' in pod_info:
                    container = client.containers.get(pod_info['container_id'])
                    container.stop()
                    container.remove()
                    logger.info(f"Removed failed pod container for pod {pod_id}")
            except docker.errors.NotFound:
                logger.warning(f"Failed pod container not found in Docker, may have been already removed")
            except Exception as e:
                logger.warning(f"Error removing failed pod container: {str(e)}")
            
            # Try to reschedule the pod
            image = pod_info.get('image', 'nginx:latest')
            new_node_id = PodScheduler.schedule_pod(pod_info['cpu_required'], image)
            
            if isinstance(new_node_id, dict):
                # If rescheduling failed, mark pod as failed
                pods[pod_id]['status'] = 'failed'
                logger.error(f"Failed to reschedule pod {pod_id}")
            else:
                logger.info(f"Successfully rescheduled pod {pod_id} to node {new_node_id}")
                
        # Clear the failed node's pod list after rescheduling
        nodes[failed_node_id]['pods'] = []

class HealthMonitor:
    @staticmethod
    def start_heartbeat(node_id):
        logger.info(f"Starting heartbeat monitoring for node {node_id}")
        while True:
            if node_id in nodes:
                try:
                    # Get container stats for the node
                    container = client.containers.get(nodes[node_id]['container_id'])
                    stats = container.stats(stream=False)  # Get current stats
                    
                    # Calculate health metrics for the node
                    cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 1)
                    memory_percent = (memory_usage / memory_limit) * 100
                    
                    # Collect pod-specific metrics
                    pod_stats = {}
                    for pod_id in nodes[node_id]['pods']:
                        if pod_id in pods and 'container_id' in pods[pod_id]:
                            try:
                                pod_container = client.containers.get(pods[pod_id]['container_id'])
                                pod_container_stats = pod_container.stats(stream=False)
                                
                                # Calculate pod-specific metrics
                                pod_cpu_usage = pod_container_stats['cpu_stats']['cpu_usage']['total_usage']
                                pod_memory_usage = pod_container_stats['memory_stats'].get('usage', 0)
                                pod_memory_limit = pod_container_stats['memory_stats'].get('limit', 1)
                                pod_memory_percent = (pod_memory_usage / pod_memory_limit) * 100
                                
                                # Store pod metrics
                                pod_stats[pod_id] = {
                                    'cpu_usage': pod_cpu_usage,
                                    'memory_usage': pod_memory_usage,
                                    'memory_limit': pod_memory_limit,
                                    'memory_percent': pod_memory_percent,
                                    'status': pod_container.status
                                }
                                
                                # Update pod status in the pods dictionary
                                pods[pod_id]['status'] = pod_container.status
                            except Exception as e:
                                logger.warning(f"Error getting stats for pod {pod_id}: {str(e)}")
                                pod_stats[pod_id] = {
                                    'error': str(e),
                                    'status': 'unknown'
                                }
                    
                    # Update node health information
                    nodes[node_id].update({
                        'last_heartbeat': datetime.now(),
                        'status': 'healthy',
                        'health_metrics': {
                            'cpu_usage_percent': cpu_usage,
                            'memory_usage_percent': memory_percent,
                            'memory_usage_mb': memory_usage / (1024 * 1024),
                            'memory_limit_mb': memory_limit / (1024 * 1024),
                            'running_pods': len(nodes[node_id]['pods']),
                            'container_status': container.status,
                            'last_error': None,
                            'pod_stats': pod_stats
                        }
                    })

                    try:
                        # Calculate actual CPU percentage
                        cpu_count = nodes[node_id]['cpu_capacity']
                        cpu_allocated = sum(pods[pid]['cpu_required'] for pid in nodes[node_id]['pods'] if pid in pods)
                        cpu_usage_percent = (cpu_allocated / cpu_count * 100) if cpu_count > 0 else 0
                        
                        cpu_predictor.add_metric(
                            node_id=node_id,
                            cpu_percent=cpu_usage_percent,
                            memory_percent=memory_percent,
                            pod_count=len(nodes[node_id]['pods']),
                            total_cpu_capacity=nodes[node_id]['cpu_capacity']
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add metric to predictor: {e}")

                except Exception as e:
                    # Update node with error information
                    if node_id in nodes:
                        nodes[node_id].update({
                            'last_heartbeat': datetime.now(),
                            'status': 'unhealthy',
                            'health_metrics': {
                                'last_error': str(e),
                                'error_time': datetime.now().isoformat()
                            }
                        })
                    logger.error(f"Error updating health metrics for node {node_id}: {str(e)}")
            time.sleep(5)  # Send heartbeat every 5 seconds

    @staticmethod
    def check_health():
        while True:
            current_time = datetime.now()
            for node_id, node_info in list(nodes.items()):  # Use list() to avoid modification during iteration
                try:
                    # Check for missed heartbeats
                    heartbeat_age = (current_time - node_info['last_heartbeat']).seconds
                    
                    # Get health metrics
                    health_metrics = node_info.get('health_metrics', {})
                    memory_percent = health_metrics.get('memory_usage_percent', 0)
                    running_pods = health_metrics.get('running_pods', 0)
                    container_status = health_metrics.get('container_status', 'unknown')
                    
                    # Define health conditions
                    conditions = {
                        'heartbeat': heartbeat_age <= 15,  # Less than 3 missed heartbeats
                        'memory': memory_percent < 90,     # Memory usage below 90%
                        'container': container_status == 'running',
                        'pods': running_pods <= node_info.get('cpu_capacity', 0) * 2  # Basic pod density check
                    }
                    
                    # Update node status based on conditions
                    if all(conditions.values()):
                        if node_info['status'] != 'healthy':
                            logger.info(f"Node {node_id} recovered and marked as healthy")
                            node_info['status'] = 'healthy'

                            email_alerter.node_failure_alert(node_id)

                    else:
                        if node_info['status'] == 'healthy':
                            logger.warning(f"Node {node_id} marked as unhealthy - Failed conditions: {[k for k,v in conditions.items() if not v]}")
                            node_info['status'] = 'unhealthy'

                            email_alerter.node_recovery_alert(node_id)

                            PodScheduler.reschedule_pods(node_id)
                    
                    # Update detailed health status
                    node_info['health_status'] = {
                        'conditions': conditions,
                        'last_check': current_time.isoformat(),
                        'details': {
                            'heartbeat_age_seconds': heartbeat_age,
                            'memory_usage_percent': memory_percent,
                            'running_pods': running_pods,
                            'container_status': container_status
                        }
                    }
                    
                except Exception as e:
                    logger.error(f"Error checking health for node {node_id}: {str(e)}")
                    if node_info['status'] == 'healthy':
                        node_info['status'] = 'unhealthy'
                        PodScheduler.reschedule_pods(node_id)
            
            time.sleep(20)  # Check every 5 seconds

# API Endpoints
@app.route('/nodes', methods=['POST'])
def add_node():
    logger.info("Received request to add node")
    data = request.get_json()
    if not data:
        logger.error("No JSON data received")
        return jsonify({'error': 'No data provided'}), 400
    
    cpu_capacity = data.get('cpu_capacity')
    if not cpu_capacity:
        logger.error("No CPU capacity specified")
        return jsonify({'error': 'CPU capacity is required'}), 400
    
    # Add CPU capacity validation
    try:
        cpu_capacity = int(cpu_capacity)
        if cpu_capacity <= 0:
            logger.error(f"Invalid CPU capacity: {cpu_capacity} (must be positive)")
            return jsonify({'error': 'CPU capacity must be positive'}), 400
        if cpu_capacity > MAX_NODE_CPU:
            logger.error(f"CPU capacity too high: {cpu_capacity} (maximum is {MAX_NODE_CPU})")
            return jsonify({'error': f'Maximum CPU capacity per node is {MAX_NODE_CPU} cores'}), 400
    except ValueError:
        logger.error(f"Invalid CPU capacity: {cpu_capacity} (not a number)")
        return jsonify({'error': 'CPU capacity must be a number'}), 400
    
    node_id = NodeManager.add_node(cpu_capacity)
    if isinstance(node_id, dict):
        return jsonify(node_id), 400
    return jsonify({'node_id': node_id, 'message': 'Node added successfully'})

@app.route('/nodes/<node_id>', methods=['DELETE'])
def remove_node(node_id):
    logger.info(f"Received request to remove node: {node_id}")
    result = NodeManager.remove_node(node_id)
    if 'error' in result:
        return jsonify(result), 404
    return jsonify(result)

@app.route('/pods', methods=['POST'])
def create_pod():
    logger.info("Received request to create pod")
    data = request.get_json()
    if not data:
        logger.error("No JSON data received")
        return jsonify({'error': 'No data provided'}), 400
    
    cpu_required = data.get('cpu_required')
    if not cpu_required:
        logger.error("No CPU requirement specified")
        return jsonify({'error': 'CPU requirement is required'}), 400
    
    # Get optional image parameter
    image = data.get('image', 'nginx:latest')
    
    # Add CPU requirement validation
    try:
        cpu_required = int(cpu_required)
        if cpu_required <= 0:
            logger.error(f"Invalid CPU requirement: {cpu_required} (must be positive)")
            return jsonify({'error': 'CPU requirement must be positive'}), 400
        if cpu_required > MAX_POD_CPU:
            logger.error(f"CPU requirement too high: {cpu_required} (maximum is {MAX_POD_CPU})")
            return jsonify({'error': f'Maximum CPU requirement per pod is {MAX_POD_CPU} cores'}), 400
    except ValueError:
        logger.error(f"Invalid CPU requirement: {cpu_required} (not a number)")
        return jsonify({'error': 'CPU requirement must be a number'}), 400
    
    pod_id = PodScheduler.schedule_pod(cpu_required, image)
    if isinstance(pod_id, dict):
        return jsonify(pod_id), 400
    
    # Get the created pod info
    pod_info = pods[pod_id]
    return jsonify({
        'pod_id': pod_id, 
        'message': 'Pod scheduled successfully',
        'node_id': pod_info['node_id'],
        'image': pod_info['image'],
        'access_url': f"http://localhost:{pod_info['host_port']}"
    })

@app.route('/cluster/status', methods=['GET'])
def get_cluster_status():
    logger.info("Received request for cluster status")
    status = {
        'nodes': {
            node_id: {
                'cpu_capacity': info['cpu_capacity'],
                'cpu_available': info['cpu_available'],
                'status': info['status'],
                'health_metrics': info.get('health_metrics', {}),
                'health_status': info.get('health_status', {}),
                'pods': [
                    {
                        'id': pod_id,
                        'cpu_required': pods[pod_id]['cpu_required'] if pod_id in pods else 0,
                        'status': pods[pod_id]['status'] if pod_id in pods else 'unknown',
                        'metrics': info.get('health_metrics', {}).get('pod_stats', {}).get(pod_id, {})
                    }
                    for pod_id in info['pods']
                ],
                'last_heartbeat': info['last_heartbeat'].isoformat()
            }
            for node_id, info in nodes.items()
        }
    }
    return jsonify(status)


@app.route('/cluster/predictions', methods=['GET'])
def get_predictions():
    """Get CPU predictions for all nodes"""
    logger.info("Received request for CPU predictions")
    predictions = cpu_predictor.get_all_predictions()
    return jsonify({
        'predictions': predictions,
        'prediction_interval_seconds': cpu_predictor.prediction_interval
    })

@app.route('/nodes/<node_id>/prediction', methods=['GET'])
def get_node_prediction(node_id):
    """Get CPU prediction for specific node"""
    prediction = cpu_predictor.get_prediction(node_id)
    if prediction is None:
        return jsonify({'error': 'No prediction available'}), 404
    return jsonify(prediction)


@app.route('/predictions/export', methods=['GET'])
def export_predictions():
    """Export predictions to CSV file"""
    logger.info("Received request to export predictions")
    node_id = request.args.get('node_id')
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'predictions_{node_id if node_id else "all"}_{timestamp}.csv'
    filepath = os.path.join('/tmp', filename)
    
    # Export to CSV
    result = cpu_predictor.export_to_csv(node_id, filepath)
    
    if result is None:
        return jsonify({'error': 'No data available for export'}), 404
    
    try:
        # Send file
        from flask import send_file
        return send_file(
            filepath,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        return jsonify({'error': 'Failed to send file'}), 500


@app.route('/monitoring/stats', methods=['GET'])
def get_monitoring_stats():
    """Get comprehensive monitoring statistics for data and model freshness"""
    logger.info("Received request for monitoring stats")
    stats = cpu_predictor.get_monitoring_stats()
    return jsonify(stats)




@app.route('/autoscaler/enable', methods=['POST'])
def enable_autoscaler():
    """Enable auto-scaling"""
    logger.info("Enabling auto-scaler")
    if autoscaler:
        autoscaler.enable()
        return jsonify({'message': 'Auto-scaling enabled', 'status': 'enabled'})
    return jsonify({'error': 'Auto-scaler not initialized'}), 500

@app.route('/autoscaler/disable', methods=['POST'])
def disable_autoscaler():
    """Disable auto-scaling"""
    logger.info("Disabling auto-scaler")
    if autoscaler:
        autoscaler.disable()
        return jsonify({'message': 'Auto-scaling disabled', 'status': 'disabled'})
    return jsonify({'error': 'Auto-scaler not initialized'}), 500

@app.route('/autoscaler/status', methods=['GET'])
def get_autoscaler_status():
    """Get auto-scaler status and metrics"""
    if not autoscaler:
        return jsonify({'error': 'Auto-scaler not initialized'}), 500
    
    status = autoscaler.get_status()
    return jsonify(status)

@app.route('/autoscaler/config', methods=['GET', 'POST'])
def autoscaler_config():
    """Get or update auto-scaler configuration"""
    if not autoscaler:
        return jsonify({'error': 'Auto-scaler not initialized'}), 500
    
    if request.method == 'POST':
        config = request.get_json()
        autoscaler.update_config(config)
        return jsonify({'message': 'Configuration updated', 'config': autoscaler.get_config()})
    
    return jsonify(autoscaler.get_config())

@app.route('/autoscaler/history', methods=['GET'])
def get_autoscaler_history():
    """Get auto-scaling history"""
    if not autoscaler:
        return jsonify({'error': 'Auto-scaler not initialized'}), 500
    
    limit = request.args.get('limit', 50, type=int)
    history = autoscaler.get_history(limit)
    return jsonify({'history': history, 'total': len(history)})



@app.route('/cluster/config/save', methods=['POST'])
def save_cluster_config():
    """Save current cluster configuration"""
    logger.info("Saving cluster configuration")
    filepath = 'cluster_config.json'
    success = config_manager.save_config(filepath)
    
    if success:
        return jsonify({'message': 'Configuration saved', 'filepath': filepath})
    return jsonify({'error': 'Failed to save configuration'}), 500

@app.route('/cluster/config/load', methods=['POST'])
def load_cluster_config():
    """Load cluster configuration (returns config for review)"""
    logger.info("Loading cluster configuration")
    filepath = 'cluster_config.json'
    config = config_manager.load_config(filepath)
    
    if config:
        return jsonify({
            'message': 'Configuration loaded',
            'config': config,
            'note': 'This is a preview. Use /cluster/config/apply to apply it.'
        })
    return jsonify({'error': 'Failed to load configuration'}), 500

@app.route('/cluster/config/export', methods=['GET'])
def export_cluster_config():
    """Export current configuration as JSON download"""
    logger.info("Exporting cluster configuration")
    config = config_manager.export_config()
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(config, temp_file, indent=2)
    temp_file.close()
    
    return send_file(
        temp_file.name,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'cluster_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )

# ==================== LOGS EXPORT ENDPOINTS ====================

@app.route('/logs/export', methods=['GET'])
def export_logs():
    """Export system logs"""
    format_type = request.args.get('format', 'txt')  # txt or json
    logger.info(f"Exporting logs in {format_type} format")
    
    # Read logs from the logging system
    # In production, you'd read from actual log file
    logs = []
    try:
        with open('orchestrator.log', 'r') as f:
            logs = f.readlines()
    except FileNotFoundError:
        # Generate sample logs if file doesn't exist
        logs = [
            f"{datetime.now().isoformat()} - INFO - Sample log entry\n"
        ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == 'json':
        filepath = f'logs_{timestamp}.json'
        log_exporter.export_json(logs, filepath)
        mimetype = 'application/json'
    else:
        filepath = f'logs_{timestamp}.txt'
        log_exporter.export_txt(logs, filepath)
        mimetype = 'text/plain'
    
    return send_file(
        filepath,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filepath
    )

# ==================== EMAIL ALERTS ENDPOINTS ====================

@app.route('/alerts/enable', methods=['POST'])
def enable_alerts():
    """Enable email alerts"""
    logger.info("Enabling email alerts")
    email_alerter.enable()
    return jsonify({'message': 'Email alerts enabled', 'status': 'enabled'})

@app.route('/alerts/disable', methods=['POST'])
def disable_alerts():
    """Disable email alerts"""
    logger.info("Disabling email alerts")
    email_alerter.disable()
    return jsonify({'message': 'Email alerts disabled', 'status': 'disabled'})

@app.route('/alerts/config', methods=['GET', 'POST'])
def alerts_config():
    """Get or update email alert configuration"""
    if request.method == 'POST':
        config = request.get_json()
        email_alerter.update_config(config)
        return jsonify({'message': 'Alert configuration updated'})
    
    return jsonify({
        'enabled': email_alerter.enabled,
        'config': email_alerter.config
    })

@app.route('/alerts/test', methods=['POST'])
def test_alert():
    """Send a test alert"""
    logger.info("Sending test alert")
    success = email_alerter.send_alert(
        'Test Alert',
        'This is a test alert from CuraNet',
        'INFO'
    )
    return jsonify({'message': 'Test alert sent', 'success': success})

@app.route('/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history"""
    limit = request.args.get('limit', 50, type=int)
    history = email_alerter.get_alert_history(limit)
    return jsonify({'history': history, 'total': len(history)})


@app.route('/alerts/simulate-failure', methods=['POST'])
def simulate_node_failure():
    """Simulate a node failure and trigger alert"""
    data = request.get_json()
    node_id = data.get('node_id')
    
    if not node_id or node_id not in nodes:
        return jsonify({'error': 'Invalid node ID'}), 400
    
    logger.info(f"Simulating failure for node {node_id}")
    
    # Mark node as unhealthy
    nodes[node_id]['status'] = 'unhealthy'
    
    # Send alert
    email_alerter.node_failure_alert(node_id)
    
    # Trigger rescheduling
    from api_server import PodScheduler
    PodScheduler.reschedule_pods(node_id)
    
    return jsonify({
        'message': f'Node {node_id} marked as failed',
        'alert_sent': True
    })

    
if __name__ == '__main__':
    logger.info("Starting API server...")
    
    # Configure logging to file
    file_handler = logging.FileHandler('orchestrator.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))
    logging.getLogger().addHandler(file_handler)
    
    # Start health monitoring thread
    threading.Thread(target=HealthMonitor.check_health, daemon=True).start()
    logger.info("Health monitoring thread started")
    
    # Start ML predictor
    predictor_manager = PredictorManager(cpu_predictor, nodes, pods)
    predictor_manager.start()
    logger.info("ML predictor started")
    
    # Initialize and start auto-scaler
    autoscaler = AutoScaler(nodes, pods, cpu_predictor, NodeManager, config={
        'scale_up_threshold': 75,
        'scale_down_threshold': 30,
        'min_nodes': 1,
        'max_nodes': 10,
        'scale_up_cpu': 4,
        'cooldown_seconds': 60
    })
    autoscaler.start()
    logger.info("Auto-scaler initialized (disabled by default)")
    
    logger.info("=" * 50)
    logger.info("🚀 CuraNet API Server Ready")
    logger.info("=" * 50)
    logger.info("API Endpoints:")
    logger.info("  - Cluster: http://localhost:5001/cluster/status")
    logger.info("  - Auto-Scaling: http://localhost:5001/autoscaler/status")
    logger.info("  - Predictions: http://localhost:5001/cluster/predictions")
    logger.info("  - Monitoring: http://localhost:5001/monitoring/stats")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=True)