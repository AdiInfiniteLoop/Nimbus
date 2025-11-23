from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Node(Base):
    __tablename__ = 'nodes'
    
    id = Column(String(36), primary_key=True)
    container_id = Column(String(64), unique=True, nullable=False)
    cpu_capacity = Column(Integer, nullable=False)
    cpu_available = Column(Integer, nullable=False)
    status = Column(String(20), default='healthy')
    last_heartbeat = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    pods = relationship('Pod', back_populates='node', cascade='all, delete-orphan')
    metrics = relationship('NodeMetric', back_populates='node', cascade='all, delete-orphan')
    predictions = relationship('CPUPrediction', back_populates='node', cascade='all, delete-orphan')
    events = relationship('Event', back_populates='node', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'container_id': self.container_id,
            'cpu_capacity': self.cpu_capacity,
            'cpu_available': self.cpu_available,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'pod_count': len(self.pods)
        }


class Pod(Base):
    __tablename__ = 'pods'
    
    id = Column(String(36), primary_key=True)
    node_id = Column(String(36), ForeignKey('nodes.id'), nullable=True)
    container_id = Column(String(64), unique=True, nullable=False)
    image = Column(String(255), nullable=False)
    cpu_required = Column(Integer, nullable=False)
    host_port = Column(Integer, nullable=True)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    scheduled_at = Column(DateTime, nullable=True)
    
    # Relationships
    node = relationship('Node', back_populates='pods')
    metrics = relationship('PodMetric', back_populates='pod', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'node_id': self.node_id,
            'container_id': self.container_id,
            'image': self.image,
            'cpu_required': self.cpu_required,
            'host_port': self.host_port,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None
        }


class NodeMetric(Base):
    __tablename__ = 'node_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(36), ForeignKey('nodes.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    cpu_usage_percent = Column(Float, nullable=False)
    memory_usage_percent = Column(Float, nullable=False)
    memory_usage_mb = Column(Float, nullable=False)
    memory_limit_mb = Column(Float, nullable=False)
    running_pods = Column(Integer, default=0)
    container_status = Column(String(20))
    
    # Relationships
    node = relationship('Node', back_populates='metrics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_percent': self.memory_usage_percent,
            'memory_usage_mb': self.memory_usage_mb,
            'running_pods': self.running_pods
        }


class PodMetric(Base):
    __tablename__ = 'pod_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pod_id = Column(String(36), ForeignKey('pods.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    cpu_usage = Column(Float, nullable=False)
    memory_usage_mb = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    status = Column(String(20))
    
    # Relationships
    pod = relationship('Pod', back_populates='metrics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'pod_id': self.pod_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_usage': self.cpu_usage,
            'memory_usage_mb': self.memory_usage_mb,
            'memory_percent': self.memory_percent,
            'status': self.status
        }


class CPUPrediction(Base):
    __tablename__ = 'cpu_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(36), ForeignKey('nodes.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    current_cpu = Column(Float, nullable=False)
    predicted_cpu = Column(Float, nullable=False)
    prediction_interval = Column(Integer, default=30)
    model_score = Column(Float, nullable=True)
    
    # Relationships
    node = relationship('Node', back_populates='predictions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'current_cpu': self.current_cpu,
            'predicted_cpu': self.predicted_cpu,
            'prediction_interval': self.prediction_interval,
            'model_score': self.model_score
        }


class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default='info')  # info, warning, error
    node_id = Column(String(36), ForeignKey('nodes.id'), nullable=True)
    pod_id = Column(String(36), nullable=True)
    message = Column(Text, nullable=False)
    event_metadata = Column(JSON, nullable=True)
    
    # Relationships
    node = relationship('Node', back_populates='events')
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'severity': self.severity,
            'node_id': self.node_id,
            'pod_id': self.pod_id,
            'message': self.message,
            'event_metadata': self.event_metadata
        }


class SchedulingDecision(Base):
    __tablename__ = 'scheduling_decisions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pod_id = Column(String(36), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    selected_node_id = Column(String(36), nullable=True)
    success = Column(Boolean, default=False)
    filter_phase_result = Column(JSON, nullable=True)
    score_phase_result = Column(JSON, nullable=True)
    bind_phase_result = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'pod_id': self.pod_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'selected_node_id': self.selected_node_id,
            'success': self.success,
            'filter_phase_result': self.filter_phase_result,
            'score_phase_result': self.score_phase_result,
            'failure_reason': self.failure_reason
        }


class DatabaseService:
    """Manages database connections and operations"""
    
    def __init__(self, db_url='sqlite:///orchestrator.db'):
        self.engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized: {db_url}")
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def close_session(self):
        """Close the scoped session"""
        self.Session.remove()
    
    def cleanup_old_metrics(self, hours=24):
        """Remove metrics older than specified hours"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            deleted_node_metrics = session.query(NodeMetric).filter(
                NodeMetric.timestamp < cutoff
            ).delete()
            
            deleted_pod_metrics = session.query(PodMetric).filter(
                PodMetric.timestamp < cutoff
            ).delete()
            
            deleted_predictions = session.query(CPUPrediction).filter(
                CPUPrediction.timestamp < cutoff
            ).delete()
            
            session.commit()
            logger.info(
                f"Cleaned up old metrics: "
                f"Node={deleted_node_metrics}, "
                f"Pod={deleted_pod_metrics}, "
                f"Predictions={deleted_predictions}"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up metrics: {e}")
        finally:
            session.close()