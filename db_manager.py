import logging
import json
from datetime import datetime, timedelta

from database import (
    get_db_session, 
    CloudProvider, 
    HealthCheck, 
    FailoverEvent, 
    PerformanceMetric, 
    BackupSync, 
    CostRecord, 
    RecoveryMetric,
    init_db
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('db_manager')

class DatabaseManager:
    """Manager class for database operations"""
    
    def __init__(self):
        """Initialize the database manager"""
        # Ensure database tables are created
        try:
            init_db()
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
    
    def get_provider_by_name(self, provider_name):
        """Get a cloud provider by name"""
        session = get_db_session()
        try:
            provider = session.query(CloudProvider).filter_by(name=provider_name).first()
            return provider
        except Exception as e:
            logger.error(f"Error getting provider by name: {str(e)}")
            return None
        finally:
            session.close()
    
    def record_health_check(self, provider_name, status, response_time=None, error_message=None, status_code=None):
        """Record a health check result"""
        session = get_db_session()
        try:
            # Get provider
            provider = self.get_provider_by_name(provider_name)
            if not provider:
                logger.warning(f"Provider {provider_name} not found in database")
                return False
            
            # Create health check record
            health_check = HealthCheck(
                provider_id=provider.id,
                status=status,
                response_time=response_time,
                error_message=error_message,
                status_code=status_code,
                checked_at=datetime.now()
            )
            
            session.add(health_check)
            session.commit()
            logger.debug(f"Health check recorded for {provider_name}: {status}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording health check: {str(e)}")
            return False
        
        finally:
            session.close()
    
    def record_failover_event(self, from_provider, to_provider, reason=None, is_manual=False, triggered_by=None, details=None):
        """Record a failover event"""
        session = get_db_session()
        try:
            # Create failover event record
            failover_event = FailoverEvent(
                from_provider=from_provider,
                to_provider=to_provider,
                reason=reason,
                is_manual=is_manual,
                triggered_by=triggered_by,
                details=json.dumps(details) if details else None,
                occurred_at=datetime.now()
            )
            
            session.add(failover_event)
            session.commit()
            logger.info(f"Failover event recorded: {from_provider} → {to_provider}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording failover event: {str(e)}")
            return False
        
        finally:
            session.close()
    
    def record_performance_metrics(self, provider_name, metrics):
        """Record performance metrics"""
        session = get_db_session()
        try:
            # Get provider
            provider = self.get_provider_by_name(provider_name)
            if not provider:
                logger.warning(f"Provider {provider_name} not found in database")
                return False
            
            # Create performance metrics record
            perf_metrics = PerformanceMetric(
                provider_id=provider.id,
                cpu_utilization=metrics.get('cpu_utilization', 0),
                memory_utilization=metrics.get('memory_utilization', 0),
                disk_iops=metrics.get('disk_iops', 0),
                network_throughput=metrics.get('network_throughput', 0),
                request_success_rate=metrics.get('request_success_rate', 0),
                average_response_time=metrics.get('average_response_time', 0),
                recorded_at=datetime.now()
            )
            
            session.add(perf_metrics)
            session.commit()
            logger.debug(f"Performance metrics recorded for {provider_name}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording performance metrics: {str(e)}")
            return False
        
        finally:
            session.close()
    
    def record_backup_sync(self, source_provider, target_provider, files_synced, total_files, success=True, error_message=None, sync_duration=0):
        """Record a backup sync event"""
        session = get_db_session()
        try:
            # Create backup sync record
            backup_sync = BackupSync(
                source_provider=source_provider,
                target_provider=target_provider,
                files_synced=files_synced,
                total_files=total_files,
                success=success,
                error_message=error_message,
                sync_duration=sync_duration,
                completed_at=datetime.now()
            )
            
            session.add(backup_sync)
            session.commit()
            logger.debug(f"Backup sync recorded: {source_provider} → {target_provider}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording backup sync: {str(e)}")
            return False
        
        finally:
            session.close()
    
    def record_cost(self, provider, compute_cost, storage_cost, transfer_cost, record_date=None):
        """Record a cost entry"""
        session = get_db_session()
        try:
            # Calculate total cost
            total_cost = compute_cost + storage_cost + transfer_cost
            
            # Use current date if not provided
            if not record_date:
                record_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Create cost record
            cost_record = CostRecord(
                provider=provider,
                compute_cost=compute_cost,
                storage_cost=storage_cost,
                transfer_cost=transfer_cost,
                total_cost=total_cost,
                record_date=record_date
            )
            
            session.add(cost_record)
            session.commit()
            logger.debug(f"Cost record added for {provider}: ${total_cost:.2f}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording cost: {str(e)}")
            return False
        
        finally:
            session.close()
    
    def get_health_status(self):
        """Get the latest health status for all providers"""
        session = get_db_session()
        try:
            # Get all providers
            providers = session.query(CloudProvider).all()
            result = {}
            
            for provider in providers:
                # Get latest health check for this provider
                latest_check = session.query(HealthCheck) \
                    .filter_by(provider_id=provider.id) \
                    .order_by(HealthCheck.checked_at.desc()) \
                    .first()
                
                if latest_check:
                    result[provider.name] = {
                        "status": latest_check.status,
                        "last_checked": latest_check.checked_at.isoformat(),
                        "response_time": latest_check.response_time
                    }
                    
                    # Add error details if available
                    if not latest_check.status:
                        if latest_check.error_message:
                            result[provider.name]["error"] = latest_check.error_message
                        if latest_check.status_code:
                            result[provider.name]["status_code"] = latest_check.status_code
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting health status: {str(e)}")
            return {}
        
        finally:
            session.close()
    
    def get_recent_failover_events(self, limit=10):
        """Get recent failover events"""
        session = get_db_session()
        try:
            # Get recent failover events
            events = session.query(FailoverEvent) \
                .order_by(FailoverEvent.occurred_at.desc()) \
                .limit(limit) \
                .all()
            
            result = []
            for event in events:
                event_data = {
                    "id": event.id,
                    "from_provider": event.from_provider,
                    "to_provider": event.to_provider,
                    "reason": event.reason,
                    "is_manual": event.is_manual,
                    "triggered_by": event.triggered_by,
                    "occurred_at": event.occurred_at.isoformat()
                }
                
                # Parse details JSON if available
                if event.details:
                    try:
                        event_data["details"] = json.loads(event.details)
                    except:
                        event_data["details"] = event.details
                
                result.append(event_data)
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting failover events: {str(e)}")
            return []
        
        finally:
            session.close()
    
    def get_performance_data(self):
        """Get the latest performance data for all providers"""
        session = get_db_session()
        try:
            # Get all providers
            providers = session.query(CloudProvider).all()
            result = {}
            
            for provider in providers:
                # Get latest performance metrics for this provider
                latest_metrics = session.query(PerformanceMetric) \
                    .filter_by(provider_id=provider.id) \
                    .order_by(PerformanceMetric.recorded_at.desc()) \
                    .first()
                
                if latest_metrics:
                    result[provider.name] = {
                        "cpu_utilization": latest_metrics.cpu_utilization,
                        "memory_utilization": latest_metrics.memory_utilization,
                        "disk_iops": latest_metrics.disk_iops,
                        "network_throughput": latest_metrics.network_throughput,
                        "request_success_rate": latest_metrics.request_success_rate,
                        "average_response_time": latest_metrics.average_response_time,
                        "timestamp": latest_metrics.recorded_at.isoformat()
                    }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting performance data: {str(e)}")
            return {}
        
        finally:
            session.close()
    
    def get_provider_availability(self, provider_name, hours=24):
        """Get availability percentage for a provider over a time period"""
        session = get_db_session()
        try:
            # Get provider
            provider = self.get_provider_by_name(provider_name)
            if not provider:
                logger.warning(f"Provider {provider_name} not found in database")
                return 0
            
            # Calculate time period
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Count total checks and successful checks
            total_checks = session.query(HealthCheck) \
                .filter(
                    HealthCheck.provider_id == provider.id,
                    HealthCheck.checked_at >= start_time,
                    HealthCheck.checked_at <= end_time
                ) \
                .count()
            
            successful_checks = session.query(HealthCheck) \
                .filter(
                    HealthCheck.provider_id == provider.id,
                    HealthCheck.checked_at >= start_time,
                    HealthCheck.checked_at <= end_time,
                    HealthCheck.status == True
                ) \
                .count()
            
            # Calculate availability percentage
            if total_checks > 0:
                availability = (successful_checks / total_checks) * 100
            else:
                availability = 0
            
            return availability
        
        except Exception as e:
            logger.error(f"Error calculating availability: {str(e)}")
            return 0
        
        finally:
            session.close()
    
    def get_cost_history(self, provider=None, days=30):
        """Get cost history for a provider or all providers"""
        session = get_db_session()
        try:
            # Calculate time period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query cost records
            query = session.query(CostRecord) \
                .filter(CostRecord.record_date >= start_date) \
                .order_by(CostRecord.record_date)
            
            # Filter by provider if specified
            if provider:
                query = query.filter(CostRecord.provider == provider)
            
            records = query.all()
            
            # Organize data by provider
            result = {}
            for record in records:
                if record.provider not in result:
                    result[record.provider] = []
                
                result[record.provider].append({
                    "timestamp": record.record_date.isoformat(),
                    "compute_cost": record.compute_cost,
                    "storage_cost": record.storage_cost,
                    "transfer_cost": record.transfer_cost,
                    "total_cost": record.total_cost
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting cost history: {str(e)}")
            return {}
        
        finally:
            session.close()
    
    def get_recovery_metrics(self):
        """Get all recovery metrics"""
        session = get_db_session()
        try:
            metrics = session.query(RecoveryMetric).all()
            result = {}
            
            for metric in metrics:
                result[metric.scenario] = {
                    "Downtime": metric.downtime,
                    "RTO": metric.rto,
                    "RPO": metric.rpo,
                    "Failover Time": metric.failover_time,
                    "Cost": metric.cost,
                    "Data Loss Probability": metric.data_loss_probability,
                    "Reliability Score": metric.reliability_score
                }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting recovery metrics: {str(e)}")
            return {}
        
        finally:
            session.close()
    
    def update_recovery_metric(self, scenario, metric_name, value):
        """Update a specific recovery metric"""
        session = get_db_session()
        try:
            # Find the metric
            metric = session.query(RecoveryMetric).filter_by(scenario=scenario).first()
            if not metric:
                logger.warning(f"Recovery metric for scenario '{scenario}' not found")
                return False
            
            # Update the specified metric
            if hasattr(metric, metric_name.lower()):
                setattr(metric, metric_name.lower(), value)
                session.commit()
                logger.info(f"Updated {metric_name} for {scenario} to {value}")
                return True
            else:
                logger.warning(f"Invalid metric name: {metric_name}")
                return False
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating recovery metric: {str(e)}")
            return False
        
        finally:
            session.close()

# Singleton instance
db_manager = DatabaseManager()

# Main execution when run directly
if __name__ == "__main__":
    # Test the database manager
    print("Testing database manager...")
    
    # Test getting providers
    provider = db_manager.get_provider_by_name("aws")
    if provider:
        print(f"Found provider: {provider.display_name}")
    
    # Test recording health check
    db_manager.record_health_check("aws", True, 0.125)
    
    # Test getting health status
    health_status = db_manager.get_health_status()
    print(f"Health status: {health_status}")