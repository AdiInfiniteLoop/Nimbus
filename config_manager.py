from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import logging
from datetime import datetime
import smtplib
from typing import Dict, Optional
import docker

logger = logging.getLogger(__name__)

class ClusterConfigManager:
    """Manage cluster configuration save/load"""
    
    def __init__(self, nodes: Dict, pods: Dict, client: docker.DockerClient):
        self.nodes = nodes
        self.pods = pods
        self.client = client
    
    def save_config(self, filepath: str = 'cluster_config.json') -> bool:
        """Save current cluster state to file"""
        try:
            config = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'nodes': {},
                'pods': {}
            }
            
            # Save node configurations
            for node_id, node_info in self.nodes.items():
                config['nodes'][node_id] = {
                    'cpu_capacity': node_info['cpu_capacity'],
                    'cpu_available': node_info['cpu_available'],
                    'status': node_info['status'],
                    'pods': node_info['pods'].copy()
                }
            
            # Save pod configurations
            for pod_id, pod_info in self.pods.items():
                config['pods'][pod_id] = {
                    'node_id': pod_info['node_id'],
                    'cpu_required': pod_info['cpu_required'],
                    'image': pod_info.get('image', 'nginx:latest'),
                    'status': pod_info['status']
                }
            
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Cluster config saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def load_config(self, filepath: str = 'cluster_config.json') -> Dict:
        """Load cluster configuration from file"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Cluster config loaded from {filepath} (saved: {config['timestamp']})")
            return config
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None
    
    def export_config(self) -> Dict:
        """Export current configuration as dictionary"""
        config = {
            'timestamp': datetime.now().isoformat(),
            'nodes_count': len(self.nodes),
            'pods_count': len(self.pods),
            'nodes': {
                node_id: {
                    'cpu_capacity': info['cpu_capacity'],
                    'cpu_available': info['cpu_available'],
                    'status': info['status'],
                    'pods_count': len(info['pods'])
                }
                for node_id, info in self.nodes.items()
            },
            'pods': {
                pod_id: {
                    'node_id': info['node_id'],
                    'cpu_required': info['cpu_required'],
                    'image': info.get('image', 'nginx:latest')
                }
                for pod_id, info in self.pods.items()
            }
        }
        return config


class LogExporter:
    """Export system logs in various formats"""
    
    def __init__(self):
        self.logs = []
    
    def capture_logs(self, log_file: str = None) -> list:
        """Capture logs from logging system"""
        # This would typically read from the log file
        # For now, we'll provide a mechanism to store logs
        return self.logs
    
    def export_txt(self, logs: list, filepath: str = 'system_logs.txt') -> bool:
        """Export logs as plain text"""
        try:
            with open(filepath, 'w') as f:
                f.write(f"=== Cluster Orchestrator System Logs ===\n")
                f.write(f"Exported: {datetime.now().isoformat()}\n")
                f.write(f"Total Entries: {len(logs)}\n")
                f.write("=" * 50 + "\n\n")
                
                for log in logs:
                    f.write(f"{log}\n")
            
            logger.info(f"Logs exported to TXT: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export logs as TXT: {e}")
            return False
    
    def export_json(self, logs: list, filepath: str = 'system_logs.json') -> bool:
        """Export logs as JSON"""
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_logs': len(logs),
                'logs': logs
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Logs exported to JSON: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export logs as JSON: {e}")
            return False


class EmailAlerter:
    """Send email alerts for cluster events"""
    
    def __init__(self, enabled: bool = False, config: Dict = None):
        self.enabled = enabled
        self.config = config or {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',
            'sender_password': '',
            'recipient_emails': []
        }
        self.alert_history = []
    
    def enable(self):
        """Enable email alerts"""
        self.enabled = True
        logger.info("Email alerts ENABLED")
    
    def disable(self):
        """Disable email alerts"""
        self.enabled = False
        logger.info("Email alerts DISABLED")
    
    def update_config(self, config: Dict):
        """Update email configuration"""
        self.config.update(config)
        logger.info("Email alert config updated")

    def _send_real_email(self, subject: str, message: str) -> bool:
        """Send email using Gmail SMTP with real delivery."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config["sender_email"]
            msg["To"] = ", ".join(self.config["recipient_emails"])
            msg["Subject"] = subject

            msg.attach(MIMEText(message, "plain"))

            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                server.starttls()
                server.login(self.config["sender_email"], self.config["sender_password"])
                server.send_message(msg)

            logger.info(f"📧 REAL EMAIL SENT: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send real email: {e}")
            return False

    def send_alert(self, subject: str, message: str, severity: str = 'INFO') -> bool:
        """Send an email alert"""
        if not self.enabled:
            logger.debug(f"Email alert (disabled): {subject}")
            return False
        
        # Record alert
        alert = {
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'message': message,
            'severity': severity,
            'sent': False
        }
        
        
        # Attempt real email
        if self.config.get('sender_email') and \
        self.config.get('sender_password') and \
        self.config.get('recipient_emails'):

            sent = self._send_real_email(subject, message)
            alert['sent'] = sent
        else:
            logger.warning("Email alert not sent: Missing configuration")

    
    def node_failure_alert(self, node_id: str):
        """Send alert for node failure"""
        subject = f"🚨 Node Failure: {node_id[:12]}"
        message = f"""
Node Failure Detected

Node ID: {node_id}
Time: {datetime.now().isoformat()}
Status: UNHEALTHY

Action Required: Check node status and investigate cause.
Pods on this node will be automatically rescheduled.
        """
        self.send_alert(subject, message.strip(), 'CRITICAL')
    
    def node_recovery_alert(self, node_id: str):
        """Send alert for node recovery"""
        subject = f"✅ Node Recovered: {node_id[:12]}"
        message = f"""
Node Recovery Detected

Node ID: {node_id}
Time: {datetime.now().isoformat()}
Status: HEALTHY

The node has recovered and is now accepting workloads.
        """
        self.send_alert(subject, message.strip(), 'INFO')
    
    def autoscale_alert(self, action: str, node_id: str, reason: str):
        """Send alert for auto-scaling events"""
        subject = f"⚡ Auto-Scale {action.upper()}: {node_id[:12]}"
        message = f"""
Auto-Scaling Event

Action: {action.upper()}
Node ID: {node_id}
Time: {datetime.now().isoformat()}
Reason: {reason}

The cluster has automatically adjusted capacity based on predicted load.
        """
        self.send_alert(subject, message.strip(), 'INFO')
    
    def high_load_alert(self, cpu_percent: float):
        """Send alert for high cluster load"""
        subject = f"⚠️ High Cluster Load: {cpu_percent:.1f}%"
        message = f"""
High Load Warning

Current CPU Usage: {cpu_percent:.1f}%
Time: {datetime.now().isoformat()}
Threshold: 80%

Consider scaling up or optimizing workloads.
        """
        self.send_alert(subject, message.strip(), 'WARNING')
    
    def get_alert_history(self, limit: int = 50) -> list:
        """Get recent alert history"""
        return self.alert_history[-limit:]
    
    def clear_history(self):
        """Clear alert history"""
        self.alert_history = []
        logger.info("Alert history cleared")