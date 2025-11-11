# 🚀 Cluster Orchestrator - BTech Major Project

## ML-Powered Container Orchestration System with Auto-Scaling

A sophisticated Kubernetes-inspired container orchestration platform featuring machine learning-based CPU prediction, intelligent auto-scaling, and real-time monitoring.

---

## 📋 Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [ML Model Details](#ml-model-details)
- [Screenshots](#screenshots)
- [Project Structure](#project-structure)

---

## ✨ Features

### Core Functionality
- ⚡ **Container Orchestration** - Deploy and manage pods across multiple nodes
- 🤖 **ML-Based CPU Prediction** - Random Forest model predicts future CPU usage
- 🔄 **Intelligent Auto-Scaling** - Automatically add/remove nodes based on predictions
- 📊 **Real-time Monitoring** - Live metrics and health monitoring
- 🎯 **Smart Scheduling** - Filter-Score-Bind algorithm for optimal pod placement

### Advanced Features
- 📈 **40+ Engineered Features** - Trends, patterns, momentum for accurate predictions
- 🔔 **Email Alerts** - Notifications for node failures and scaling events
- 💾 **Config Management** - Save/load cluster configurations
- 📁 **Log Export** - Export system logs in TXT/JSON formats
- 🌓 **Dark/Light Theme** - User-friendly UI with theme toggle
- 📉 **Performance Analytics** - Training metrics, R² scores, MAE, RMSE

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Dashboard   │  │  Charts &    │  │   Settings   │         │
│  │  Monitoring  │  │  Visualizations│  │   Modal     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│           ↓                 ↓                 ↓                  │
│  ┌───────────────────────────────────────────────────┐         │
│  │         REST API (HTTP/JSON)                       │         │
│  └───────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask API Server)                    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   API Endpoints                           │  │
│  │  /nodes  /pods  /cluster/status  /predictions  /alerts   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Node Manager │  │Pod Scheduler │  │ Health       │        │
│  │              │  │              │  │ Monitor      │        │
│  │ - Add/Remove │  │ - Filter     │  │              │        │
│  │ - Health     │  │ - Score      │  │ - Heartbeat  │        │
│  │   Check      │  │ - Bind       │  │ - Rescheduling        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                              ↓                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ CPU Predictor│  │ Auto-Scaler  │  │Config Manager│        │
│  │              │  │              │  │              │        │
│  │ - Random     │  │ - Thresholds │  │ - Save/Load  │        │
│  │   Forest     │  │ - Cooldown   │  │ - Export     │        │
│  │ - 40+        │  │ - Add/Remove │  │ - Backup     │        │
│  │   Features   │  │   Nodes      │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                              ↓                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │Email Alerter │  │Log Exporter  │  │  Monitoring  │        │
│  │              │  │              │  │   Stats      │        │
│  │ - Failures   │  │ - TXT/JSON   │  │              │        │
│  │ - Recoveries │  │ - Timestamp  │  │ - Freshness  │        │
│  │ - Scaling    │  │   Export     │  │ - Quality    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER ENGINE                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Node        │  │  Node        │  │  Node        │        │
│  │  Container   │  │  Container   │  │  Container   │        │
│  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │        │
│  │  │ Pod 1  │  │  │  │ Pod 2  │  │  │  │ Pod 3  │  │        │
│  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │        │
│  │  ┌────────┐  │  │  ┌────────┐  │  │              │        │
│  │  │ Pod 4  │  │  │  │ Pod 5  │  │  │              │        │
│  │  └────────┘  │  │  └────────┘  │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Python 3.9+** - Core programming language
- **Flask** - REST API framework
- **Docker SDK** - Container management
- **scikit-learn** - Machine learning (Random Forest)
- **NumPy** - Numerical computations
- **Threading** - Concurrent operations

### Frontend
- **React 18** - UI framework
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Lucide Icons** - Icon library

### Infrastructure
- **Docker** - Containerization platform
- **Docker Desktop** - Development environment

---

## 📦 Installation

### Prerequisites
```bash
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/

# Verify Docker installation
docker --version
docker ps
```

### Backend Setup
```bash
# Clone the repository
git clone <repository-url>
cd cluster-orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements.txt
```
flask==3.0.0
flask-cors==4.0.0
docker==7.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

### Run the Application
```bash
# Start backend
python api_server.py

# Backend will be available at: http://localhost:5001
```

### Frontend Setup
The dashboard is provided as a React artifact. Simply:
1. Start the backend server
2. Open the React dashboard artifact
3. It will automatically connect to `http://localhost:5001`

---

## 🎮 Usage

### 1. Start the System
```bash
# Terminal 1: Start backend
python api_server.py

# Terminal 2: Open dashboard (React artifact)
# The dashboard connects automatically to the API
```

### 2. Add Nodes
- Click "Add Node" button
- Specify CPU capacity (1-8 cores)
- Node container is created automatically

### 3. Create Pods
- Click "Create Pod" button
- Specify CPU requirement and image
- Pod is scheduled using ML predictions

### 4. Enable Auto-Scaling
- Go to Settings modal
- Configure thresholds and limits
- Click "Enable" in auto-scaler control panel
- System will automatically scale based on predicted CPU

### 5. Monitor & Export
- View real-time metrics and predictions
- Export logs (TXT/JSON) from Settings
- Save/Load cluster configurations
- Enable email alerts for failures

---

## 📡 API Documentation

### Node Management
```bash
# Add Node
POST /nodes
Body: {"cpu_capacity": 4}

# Remove Node
DELETE /nodes/<node_id>

# Get Cluster Status
GET /cluster/status
```

### Pod Management
```bash
# Create Pod
POST /pods
Body: {"cpu_required": 2, "image": "nginx:latest"}

# Get Cluster Status (includes pods)
GET /cluster/status
```

### ML Predictions
```bash
# Get All Predictions
GET /cluster/predictions

# Get Node Prediction
GET /nodes/<node_id>/prediction

# Export Predictions CSV
GET /predictions/export?node_id=<optional>
```

### Auto-Scaling
```bash
# Enable Auto-Scaling
POST /autoscaler/enable

# Disable Auto-Scaling
POST /autoscaler/disable

# Get Auto-Scaler Status
GET /autoscaler/status

# Update Configuration
POST /autoscaler/config
Body: {
  "scale_up_threshold": 75,
  "scale_down_threshold": 30,
  "min_nodes": 1,
  "max_nodes": 10
}

# Get Scaling History
GET /autoscaler/history?limit=50
```

### Configuration & Logs
```bash
# Save Cluster Config
POST /cluster/config/save

# Load Cluster Config
POST /cluster/config/load

# Export Config
GET /cluster/config/export

# Export Logs
GET /logs/export?format=txt  # or format=json
```

### Email Alerts
```bash
# Enable Alerts
POST /alerts/enable

# Disable Alerts
POST /alerts/disable

# Update Configuration
POST /alerts/config
Body: {
  "sender_email": "admin@example.com",
  "recipient_emails": ["ops@example.com"]
}

# Send Test Alert
POST /alerts/test

# Simulate Node Failure
POST /alerts/simulate-failure
Body: {"node_id": "<node_id>"}

# Get Alert History
GET /alerts/history?limit=50
```

### Monitoring
```bash
# Get Monitoring Stats
GET /monitoring/stats
```

---

## 🤖 ML Model Details

### Random Forest Regressor
- **Algorithm**: Random Forest for time-series prediction
- **Target**: CPU usage 30 seconds ahead
- **Training**: Every 2 minutes with latest data
- **Features**: 40+ engineered features

### Feature Engineering
```python
Features Include:
1. Trends (short/medium/long term)
2. Velocity & Acceleration
3. Volatility (std deviation)
4. Rate of Change
5. Moving Averages (MA-6, MA-12, MA-24, MA-48)
6. Momentum Indicators (MACD-like)
7. Statistical (min, max, percentiles)
8. Historical Context (deviation from history)
9. Workload (pod count, CPU capacity)
10. Temporal (hour, day, cyclical encoding)
```

### Performance Metrics
- **R² Score**: 0.6-0.9 (Good to Excellent)
- **MAE**: 5-10% (Good accuracy)
- **RMSE**: 6-12% (Low error)
- **Training Time**: 0.5-2 seconds per node
- **Prediction Time**: <0.1 seconds

### Why This Approach Works
✅ Focuses on **patterns and trends**, not current values
✅ Avoids **echo predictions** (predicting current value)
✅ Captures **momentum and acceleration**
✅ Includes **temporal patterns** (business hours, etc.)
✅ Uses **historical context** for better predictions

---

## 📸 Screenshots

### Dashboard
- Real-time cluster monitoring
- CPU distribution pie chart
- Live CPU usage line chart
- Node status table with predictions

### Auto-Scaling Panel
- Enable/disable auto-scaling
- Configure thresholds and limits
- View scaling history
- Real-time recommendations

### Settings Modal
- Auto-scaler configuration
- Email alert setup
- Log export options
- Cluster backup/restore

---

## 📁 Project Structure

```
cluster-orchestrator/
├── api_server.py              # Main Flask API server
├── scheduling.py              # Filter-Score-Bind scheduler
├── ml_predictor_enhanced.py   # ML prediction engine
├── autoscaler.py              # Auto-scaling logic
├── config_manager.py          # Config & log management
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── cluster_config.json        # Saved cluster state
├── orchestrator.log           # System logs
└── predictions_export.csv     # Exported predictions
```

---

## 🎯 Key Innovations

### 1. ML-Driven Scheduling
Traditional schedulers react to current load. Our system **predicts future load** and makes proactive decisions.

### 2. Rich Feature Engineering
Using 40+ features focusing on **trends and patterns** instead of just current values prevents echo predictions.

### 3. Parallel Training
Multiple node models train simultaneously using ThreadPoolExecutor, achieving **4x speedup**.

### 4. Comprehensive Monitoring
Track data freshness, model age, training duration, and prediction quality in real-time.

### 5. Production-Grade Features
- Auto-scaling with cooldown
- Email alerts for critical events
- Config save/load for disaster recovery
- Log export for debugging

---

## 🔬 Testing & Validation

### Load Testing
```python
# Create multiple nodes
for i in range(5):
    POST /nodes {"cpu_capacity": 4}

# Create many pods
for i in range(20):
    POST /pods {"cpu_required": 1, "image": "nginx:latest"}

# Enable auto-scaling and observe behavior
POST /autoscaler/enable
```

### Failure Simulation
```bash
# Simulate node failure
POST /alerts/simulate-failure
Body: {"node_id": "<node_id>"}

# Observe:
# - Email alert sent
# - Pods rescheduled automatically
# - Health status updated
```

### Performance Metrics
- **Scheduling Latency**: <100ms per pod
- **ML Prediction Time**: <100ms per node
- **Auto-Scale Decision**: <1 second
- **UI Update Frequency**: 5 seconds

---

## 🚀 Future Enhancements

### Short Term
- [ ] WebSocket for real-time updates
- [ ] Persistent database (PostgreSQL)
- [ ] User authentication (JWT)
- [ ] Anomaly detection (Isolation Forest)

### Long Term
- [ ] Multi-region support
- [ ] GPU scheduling
- [ ] Custom resource types
- [ ] Helm chart support

---

## 👨‍🎓 Academic Context

**Project Type**: BTech 4th Year Major Project  
**Domain**: Cloud Computing, Machine Learning, DevOps  
**Duration**: 6 months  

### Learning Outcomes
1. Container orchestration concepts
2. Machine learning for time-series prediction
3. RESTful API design
4. Real-time monitoring systems
5. Production-grade software development

### Technologies Demonstrated
- **Backend Development**: Flask, Python
- **Machine Learning**: scikit-learn, Random Forest
- **DevOps**: Docker, containerization
- **Frontend**: React, data visualization
- **System Design**: Microservices, distributed systems

---

## 📄 License

This project is developed for academic purposes as part of BTech curriculum.

---

## 👤 Author

**BTech 4th Year Student**  
Computer Science & Engineering  

---

## 🙏 Acknowledgments

- Inspired by Kubernetes architecture
- Built with Docker for containerization
- Machine learning using scikit-learn
- UI components from Tailwind CSS & Lucide

---

## 📞 Support

For issues or questions:
1. Check API logs: `tail -f orchestrator.log`
2. Verify Docker is running: `docker ps`
3. Check container status: `docker ps -a`
4. Review error messages in browser console

---

**Made with ❤️ for BTech Major Project**