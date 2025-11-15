import requests
import json
import sys
import time
import multiprocessing
from datetime import datetime
import os

# Update BASE_URL to use the IP address where the server is running (127.0.0.1)
BASE_URL = 'http://127.0.0.1:5001'

def check_server():
    try:
        response = requests.get(f'{BASE_URL}/cluster/status')
        return True
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the API server.")
        print("Please make sure the API server is running (python api_server.py)")
        print(f"Trying to connect to: {BASE_URL}")
        return False
    except Exception as e:
        print(f"Error checking server: {str(e)}")
        return False

def print_help():
    # Get system CPU count
    system_cpu = multiprocessing.cpu_count()
    max_node_cpu = min(8, system_cpu)
    max_pod_cpu = min(6, system_cpu)
    
    print(f"""
CuraNet CLI
----------------------------
System Information:
- Available CPU cores: {system_cpu}
- Maximum node CPU capacity: {max_node_cpu} cores
- Maximum pod CPU requirement: {max_pod_cpu} cores
- Total CPU capacity across all nodes cannot exceed {system_cpu} cores

CLUSTER MANAGEMENT:
  add-node <cpu_capacity>           - Add a new node with specified CPU capacity
  remove-node <node_id>             - Remove a node by ID
  create-pod <cpu_required> [image] - Create a pod (max {max_pod_cpu} cores)
  status                            - Show cluster status
  
PREDICTIONS & MONITORING:
  predictions                       - Get CPU predictions for all nodes
  node-prediction <node_id>         - Get prediction for specific node
  export-predictions [node_id]      - Export predictions to CSV
  monitoring-stats                  - Get monitoring statistics
  
AUTO-SCALING:
  autoscaler-enable                 - Enable auto-scaling
  autoscaler-disable                - Disable auto-scaling
  autoscaler-status                 - Get auto-scaler status
  autoscaler-config                 - View auto-scaler configuration
  autoscaler-config-set <json>      - Update auto-scaler configuration
  autoscaler-history [limit]        - View auto-scaling history
  
CONFIGURATION MANAGEMENT:
  config-save                       - Save current cluster configuration
  config-load                       - Load cluster configuration
  config-export                     - Export configuration to JSON file
  
LOGS & ALERTS:
  logs-export [format]              - Export logs (format: txt or json)
  alerts-enable                     - Enable email alerts
  alerts-disable                    - Disable email alerts
  alerts-config                     - View alert configuration
  alerts-config-set <json>          - Update alert configuration
  alerts-test                       - Send test alert
  alerts-history [limit]            - View alert history
  simulate-failure <node_id>        - Simulate node failure
  
GENERAL:
  help                              - Show this help message
  exit                              - Exit the program

Available Container Images:
- nginx:latest (default), httpd:latest, python:3.9-slim, redis:latest, mysql:5.7
    """)

def format_response(response):
    """Pretty print JSON response"""
    try:
        return json.dumps(response.json(), indent=2)
    except:
        return str(response.text)

def handle_request(method, endpoint, data=None, params=None):
    """Generic request handler with error handling"""
    try:
        url = f'{BASE_URL}{endpoint}'
        if method == 'GET':
            response = requests.get(url, params=params)
        elif method == 'POST':
            response = requests.post(url, json=data)
        elif method == 'DELETE':
            response = requests.delete(url)
        else:
            print(f"Unsupported HTTP method: {method}")
            return
        
        print(format_response(response))
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the API server. Is it running?")
    except Exception as e:
        print(f"Error: {str(e)}")

# ==================== CLUSTER MANAGEMENT ====================

def add_node(cpu_capacity):
    handle_request('POST', '/nodes', {'cpu_capacity': int(cpu_capacity)})

def remove_node(node_id):
    handle_request('DELETE', f'/nodes/{node_id}')

def create_pod(args):
    try:
        cpu_required = int(args[0])
        image = args[1] if len(args) > 1 else 'nginx:latest'
        handle_request('POST', '/pods', {
            'cpu_required': cpu_required,
            'image': image
        })
    except ValueError:
        print("Error: CPU requirement must be a number")
    except Exception as e:
        print(f"Error: {str(e)}")

def show_status():
    handle_request('GET', '/cluster/status')

# ==================== PREDICTIONS & MONITORING ====================

def get_predictions():
    """Get CPU predictions for all nodes"""
    handle_request('GET', '/cluster/predictions')

def get_node_prediction(node_id):
    """Get CPU prediction for specific node"""
    handle_request('GET', f'/nodes/{node_id}/prediction')

def export_predictions(node_id=None):
    """Export predictions to CSV file"""
    try:
        params = {'node_id': node_id} if node_id else {}
        url = f'{BASE_URL}/predictions/export'
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            # Save file locally
            filename = f'predictions_{node_id if node_id else "all"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ Predictions exported to: {filename}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error exporting predictions: {str(e)}")

def get_monitoring_stats():
    """Get comprehensive monitoring statistics"""
    handle_request('GET', '/monitoring/stats')

# ==================== AUTO-SCALING ====================

def autoscaler_enable():
    """Enable auto-scaling"""
    handle_request('POST', '/autoscaler/enable')

def autoscaler_disable():
    """Disable auto-scaling"""
    handle_request('POST', '/autoscaler/disable')

def autoscaler_status():
    """Get auto-scaler status"""
    handle_request('GET', '/autoscaler/status')

def autoscaler_config():
    """Get auto-scaler configuration"""
    handle_request('GET', '/autoscaler/config')

def autoscaler_config_set(config_json):
    """Update auto-scaler configuration"""
    try:
        config = json.loads(config_json)
        handle_request('POST', '/autoscaler/config', config)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")

def autoscaler_history(limit=50):
    """Get auto-scaling history"""
    handle_request('GET', '/autoscaler/history', params={'limit': limit})

# ==================== CONFIGURATION MANAGEMENT ====================

def config_save():
    """Save current cluster configuration"""
    handle_request('POST', '/cluster/config/save')

def config_load():
    """Load cluster configuration"""
    handle_request('POST', '/cluster/config/load')

def config_export():
    """Export configuration to JSON file"""
    try:
        url = f'{BASE_URL}/cluster/config/export'
        response = requests.get(url)
        
        if response.status_code == 200:
            filename = f'cluster_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ Configuration exported to: {filename}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error exporting configuration: {str(e)}")

# ==================== LOGS & ALERTS ====================

def logs_export(format_type='txt'):
    """Export system logs"""
    try:
        url = f'{BASE_URL}/logs/export'
        response = requests.get(url, params={'format': format_type})
        
        if response.status_code == 200:
            filename = f'logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{format_type}'
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ Logs exported to: {filename}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error exporting logs: {str(e)}")

def alerts_enable():
    """Enable email alerts"""
    handle_request('POST', '/alerts/enable')

def alerts_disable():
    """Disable email alerts"""
    handle_request('POST', '/alerts/disable')

def alerts_config():
    """Get alert configuration"""
    handle_request('GET', '/alerts/config')

def alerts_config_set(config_json):
    """Update alert configuration"""
    try:
        config = json.loads(config_json)
        handle_request('POST', '/alerts/config', config)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")

def alerts_test():
    """Send test alert"""
    handle_request('POST', '/alerts/test')

def alerts_history(limit=50):
    """Get alert history"""
    handle_request('GET', '/alerts/history', params={'limit': limit})

def simulate_failure(node_id):
    """Simulate node failure"""
    handle_request('POST', '/alerts/simulate-failure', {'node_id': node_id})

# ==================== INTERACTIVE MODE ====================

def interactive_mode():
    """Enhanced interactive mode with all features"""
    print("CuraNet CLI - Interactive Mode")
    print_help()
    
    # Wait for server to be ready
    print("\nWaiting for API server to be ready...")
    for _ in range(5):
        if check_server():
            print("✓ Connected to API server")
            break
        time.sleep(1)
    else:
        print("✗ Could not connect to API server")
        return
    
    while True:
        try:
            command = input("\n🔧 cluster> ").strip().split()
            if not command:
                continue
                
            cmd = command[0].lower()
            
            # General commands
            if cmd == 'exit':
                print("Goodbye!")
                sys.exit(0)
            elif cmd == 'help':
                print_help()
            
            # Cluster management
            elif cmd == 'status':
                show_status()
            elif cmd == 'add-node' and len(command) == 2:
                add_node(command[1])
            elif cmd == 'remove-node' and len(command) == 2:
                remove_node(command[1])
            elif cmd == 'create-pod' and len(command) >= 2:
                create_pod(command[1:])
            
            # Predictions & Monitoring
            elif cmd == 'predictions':
                get_predictions()
            elif cmd == 'node-prediction' and len(command) == 2:
                get_node_prediction(command[1])
            elif cmd == 'export-predictions':
                node_id = command[1] if len(command) > 1 else None
                export_predictions(node_id)
            elif cmd == 'monitoring-stats':
                get_monitoring_stats()
            
            # Auto-scaling
            elif cmd == 'autoscaler-enable':
                autoscaler_enable()
            elif cmd == 'autoscaler-disable':
                autoscaler_disable()
            elif cmd == 'autoscaler-status':
                autoscaler_status()
            elif cmd == 'autoscaler-config':
                autoscaler_config()
            elif cmd == 'autoscaler-config-set' and len(command) >= 2:
                autoscaler_config_set(' '.join(command[1:]))
            elif cmd == 'autoscaler-history':
                limit = int(command[1]) if len(command) > 1 else 50
                autoscaler_history(limit)
            
            # Configuration management
            elif cmd == 'config-save':
                config_save()
            elif cmd == 'config-load':
                config_load()
            elif cmd == 'config-export':
                config_export()
            
            # Logs & Alerts
            elif cmd == 'logs-export':
                format_type = command[1] if len(command) > 1 else 'txt'
                logs_export(format_type)
            elif cmd == 'alerts-enable':
                alerts_enable()
            elif cmd == 'alerts-disable':
                alerts_disable()
            elif cmd == 'alerts-config':
                alerts_config()
            elif cmd == 'alerts-config-set' and len(command) >= 2:
                alerts_config_set(' '.join(command[1:]))
            elif cmd == 'alerts-test':
                alerts_test()
            elif cmd == 'alerts-history':
                limit = int(command[1]) if len(command) > 1 else 50
                alerts_history(limit)
            elif cmd == 'simulate-failure' and len(command) == 2:
                simulate_failure(command[1])
            
            else:
                print("Invalid command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {str(e)}")

# ==================== COMMAND LINE MODE ====================

def command_line_mode():
    """Execute single command from command line arguments"""
    if len(sys.argv) < 2:
        interactive_mode()
        return
    
    cmd = sys.argv[1].lower()
    args = sys.argv[2:]
    
    # Map commands to functions
    commands = {
        'status': show_status,
        'predictions': get_predictions,
        'monitoring-stats': get_monitoring_stats,
        'autoscaler-enable': autoscaler_enable,
        'autoscaler-disable': autoscaler_disable,
        'autoscaler-status': autoscaler_status,
        'autoscaler-config': autoscaler_config,
        'autoscaler-history': lambda: autoscaler_history(int(args[0]) if args else 50),
        'config-save': config_save,
        'config-load': config_load,
        'config-export': config_export,
        'alerts-enable': alerts_enable,
        'alerts-disable': alerts_disable,
        'alerts-config': alerts_config,
        'alerts-test': alerts_test,
        'alerts-history': lambda: alerts_history(int(args[0]) if args else 50),
    }
    
    # Commands with arguments
    if cmd == 'add-node' and len(args) == 1:
        add_node(args[0])
    elif cmd == 'remove-node' and len(args) == 1:
        remove_node(args[0])
    elif cmd == 'create-pod' and len(args) >= 1:
        create_pod(args)
    elif cmd == 'node-prediction' and len(args) == 1:
        get_node_prediction(args[0])
    elif cmd == 'export-predictions':
        export_predictions(args[0] if args else None)
    elif cmd == 'autoscaler-config-set' and len(args) >= 1:
        autoscaler_config_set(' '.join(args))
    elif cmd == 'logs-export':
        logs_export(args[0] if args else 'txt')
    elif cmd == 'alerts-config-set' and len(args) >= 1:
        alerts_config_set(' '.join(args))
    elif cmd == 'simulate-failure' and len(args) == 1:
        simulate_failure(args[0])
    elif cmd in commands:
        commands[cmd]()
    elif cmd == 'help':
        print_help()
    else:
        print(f"Unknown command: {cmd}")
        print("Type 'help' for available commands")

def main():
    """Main entry point"""
    if not check_server():
        print("\nPlease start the API server first:")
        print("  python api_server.py")
        sys.exit(1)
    
    # Check if running in command line or interactive mode
    if len(sys.argv) > 1:
        command_line_mode()
    else:
        interactive_mode()

if __name__ == '__main__':
    main()