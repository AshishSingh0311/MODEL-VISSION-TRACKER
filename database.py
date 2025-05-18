import os
import logging
import json
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('database')

# Get database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    DATABASE_URL = "sqlite:///multi_cloud_dr.db"  # Fallback to SQLite
    logger.warning(f"Using fallback SQLite database: {DATABASE_URL}")

# Create engine and session
try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    Base = declarative_base()
    logger.info("Database connection established")
except Exception as e:
    logger.error(f"Error connecting to database: {str(e)}")
    raise

# Define models
class CloudProvider(Base):
    """Model for cloud provider information"""
    __tablename__ = 'cloud_providers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # aws, azure, gcp
    display_name = Column(String(100))  # AWS, Azure, GCP
    region = Column(String(50))
    priority = Column(Integer)
    base_latency = Column(Float)
    base_reliability = Column(Float)
    cost_per_hour = Column(Float)
    storage_cost_gb = Column(Float)
    data_transfer_cost_gb = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    health_checks = relationship("HealthCheck", back_populates="provider")
    performance_metrics = relationship("PerformanceMetric", back_populates="provider")
    
    def __repr__(self):
        return f"<CloudProvider(name='{self.name}')>"

class HealthCheck(Base):
    """Model for health check results"""
    __tablename__ = 'health_checks'
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey('cloud_providers.id'))
    status = Column(Boolean, default=True)
    response_time = Column(Float, nullable=True)
    error_message = Column(String(255), nullable=True)
    status_code = Column(Integer, nullable=True)
    checked_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    provider = relationship("CloudProvider", back_populates="health_checks")
    
    def __repr__(self):
        return f"<HealthCheck(provider='{self.provider.name if self.provider else None}', status={self.status})>"

class FailoverEvent(Base):
    """Model for failover events"""
    __tablename__ = 'failover_events'
    
    id = Column(Integer, primary_key=True)
    from_provider = Column(String(50), nullable=False)
    to_provider = Column(String(50), nullable=False)
    reason = Column(String(255))
    is_manual = Column(Boolean, default=False)
    triggered_by = Column(String(100), nullable=True)  # User or system
    details = Column(Text, nullable=True)  # JSON string with additional details
    occurred_at = Column(DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f"<FailoverEvent(from='{self.from_provider}', to='{self.to_provider}')>"

class PerformanceMetric(Base):
    """Model for performance metrics"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey('cloud_providers.id'))
    cpu_utilization = Column(Float)
    memory_utilization = Column(Float)
    disk_iops = Column(Integer)
    network_throughput = Column(Float)
    request_success_rate = Column(Float)
    average_response_time = Column(Float)
    recorded_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    provider = relationship("CloudProvider", back_populates="performance_metrics")
    
    def __repr__(self):
        return f"<PerformanceMetric(provider='{self.provider.name if self.provider else None}')>"

class BackupSync(Base):
    """Model for backup sync events"""
    __tablename__ = 'backup_syncs'
    
    id = Column(Integer, primary_key=True)
    source_provider = Column(String(50), nullable=False)
    target_provider = Column(String(50), nullable=False)
    files_synced = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(String(255), nullable=True)
    sync_duration = Column(Float)  # in seconds
    completed_at = Column(DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f"<BackupSync(source='{self.source_provider}', target='{self.target_provider}')>"

class CostRecord(Base):
    """Model for cost records"""
    __tablename__ = 'cost_records'
    
    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False)
    compute_cost = Column(Float, default=0.0)
    storage_cost = Column(Float, default=0.0)
    transfer_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    record_date = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<CostRecord(provider='{self.provider}', total_cost={self.total_cost})>"

class RecoveryMetric(Base):
    """Model for recovery metrics from scenarios"""
    __tablename__ = 'recovery_metrics'
    
    id = Column(Integer, primary_key=True)
    scenario = Column(String(100), nullable=False)
    downtime = Column(Float)  # seconds
    rto = Column(Float)  # seconds
    rpo = Column(Float)  # minutes
    failover_time = Column(Float)  # seconds
    cost = Column(Float)  # dollars
    data_loss_probability = Column(Float)
    reliability_score = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<RecoveryMetric(scenario='{self.scenario}')>"

# Create all tables
def init_db():
    """Initialize the database tables"""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        # Initialize with default data
        init_default_data()
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

# Helper function to initialize default data
def init_default_data():
    """Initialize database with default data"""
    session = Session()
    
    try:
        # Check if we already have cloud providers
        if session.query(CloudProvider).count() == 0:
            # Add default cloud providers
            providers = [
                CloudProvider(
                    name="aws",
                    display_name="Amazon Web Services",
                    region="us-east-1",
                    priority=1,
                    base_latency=25.0,
                    base_reliability=0.998,
                    cost_per_hour=0.75,
                    storage_cost_gb=0.023,
                    data_transfer_cost_gb=0.09
                ),
                CloudProvider(
                    name="azure",
                    display_name="Microsoft Azure",
                    region="eastus",
                    priority=2,
                    base_latency=30.0,
                    base_reliability=0.996,
                    cost_per_hour=0.80,
                    storage_cost_gb=0.018,
                    data_transfer_cost_gb=0.08
                ),
                CloudProvider(
                    name="gcp",
                    display_name="Google Cloud Platform",
                    region="us-central1",
                    priority=3,
                    base_latency=28.0,
                    base_reliability=0.997,
                    cost_per_hour=0.72,
                    storage_cost_gb=0.020,
                    data_transfer_cost_gb=0.11
                )
            ]
            
            session.add_all(providers)
            session.commit()
            logger.info("Default cloud providers added to database")
        
        # Check if we already have recovery metrics
        if session.query(RecoveryMetric).count() == 0:
            # Add default recovery metrics from the research paper
            metrics = [
                RecoveryMetric(
                    scenario="AWS Instance Failure",
                    downtime=120.0,
                    rto=45.0,
                    rpo=5.0,
                    failover_time=30.0,
                    cost=20.0,
                    data_loss_probability=0.01,
                    reliability_score=0.95
                ),
                RecoveryMetric(
                    scenario="Azure Storage Failure",
                    downtime=150.0,
                    rto=60.0,
                    rpo=6.0,
                    failover_time=35.0,
                    cost=25.0,
                    data_loss_probability=0.02,
                    reliability_score=0.93
                ),
                RecoveryMetric(
                    scenario="GCP Network Disruption",
                    downtime=180.0,
                    rto=90.0,
                    rpo=7.0,
                    failover_time=50.0,
                    cost=30.0,
                    data_loss_probability=0.03,
                    reliability_score=0.90
                ),
                RecoveryMetric(
                    scenario="Cross-Cloud Failover",
                    downtime=90.0,
                    rto=40.0,
                    rpo=4.0,
                    failover_time=25.0,
                    cost=22.0,
                    data_loss_probability=0.005,
                    reliability_score=0.97
                ),
                RecoveryMetric(
                    scenario="Multi-Cloud Outage",
                    downtime=110.0,
                    rto=50.0,
                    rpo=5.0,
                    failover_time=40.0,
                    cost=28.0,
                    data_loss_probability=0.015,
                    reliability_score=0.96
                )
            ]
            
            session.add_all(metrics)
            session.commit()
            logger.info("Default recovery metrics added to database")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error initializing default data: {str(e)}")
    finally:
        session.close()

# Function to get a database session
def get_db_session():
    """Get a database session"""
    return Session()

# Main execution when run directly
if __name__ == "__main__":
    init_db()