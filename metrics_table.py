import json
import os
import pandas as pd
from datetime import datetime

from config import INITIAL_METRICS, METRICS_FILE

def load_metrics():
    """Load metrics from file or initialize with defaults"""
    try:
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create directory for metrics file if it doesn't exist
            os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
            
            # Initialize with default metrics
            with open(METRICS_FILE, 'w') as f:
                json.dump(INITIAL_METRICS, f)
            
            return INITIAL_METRICS
    except Exception as e:
        print(f"Error loading metrics: {str(e)}")
        return INITIAL_METRICS

def save_metrics(metrics):
    """Save metrics to file"""
    try:
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f)
        return True
    except Exception as e:
        print(f"Error saving metrics: {str(e)}")
        return False

def get_metrics_dataframe():
    """Get metrics as a pandas DataFrame"""
    metrics = load_metrics()
    
    # Convert metrics to DataFrame
    df = pd.DataFrame.from_dict(metrics, orient='index')
    
    # Add scenario as a column
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Scenario'}, inplace=True)
    
    return df

def update_metric(scenario, metric, value):
    """Update a specific metric value"""
    metrics = load_metrics()
    
    if scenario in metrics and metric in metrics[scenario]:
        metrics[scenario][metric] = value
        save_metrics(metrics)
        return True
    
    return False

def add_metric_event(scenario, metrics_data):
    """Add a new metric event with timestamp"""
    try:
        # Load existing metrics
        all_metrics = load_metrics()
        
        # Create new event with timestamp
        event = {
            **metrics_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add or update the scenario
        all_metrics[scenario] = event
        
        # Save updated metrics
        save_metrics(all_metrics)
        
        return True
    except Exception as e:
        print(f"Error adding metric event: {str(e)}")
        return False

def get_formatted_metrics_table():
    """Get a formatted metrics table suitable for display"""
    df = get_metrics_dataframe()
    
    # Format numeric columns
    for col in df.columns:
        if col != 'Scenario' and col != 'timestamp':
            if df[col].dtype in ['int64', 'float64']:
                if col == 'Cost':
                    df[col] = df[col].apply(lambda x: f"${x}")
                elif col == 'RPO':
                    df[col] = df[col].apply(lambda x: f"{x} min")
                else:
                    df[col] = df[col].apply(lambda x: f"{x} s")
    
    return df
