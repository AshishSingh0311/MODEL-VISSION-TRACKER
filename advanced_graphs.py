import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

from performance_monitor import (
    get_performance_data,
    get_availability_history,
    get_cost_history,
    get_network_latency,
    calculate_availability_percentage,
    get_total_cost_by_provider
)

# Color schemes for consistent visualizations
PROVIDER_COLORS = {
    "aws": "#FF9900",      # AWS Orange
    "azure": "#0078D4",    # Azure Blue
    "gcp": "#4285F4"       # Google Blue
}

def create_performance_comparison_chart():
    """Create a radar chart comparing performance metrics across providers"""
    # Get current performance data
    performance_data = get_performance_data()
    
    if not performance_data:
        return go.Figure().update_layout(title="No performance data available")
    
    # Prepare data for radar chart
    providers = list(performance_data.keys())
    
    # Define metrics to include in comparison (excluding timestamp)
    metrics = [
        "cpu_utilization", 
        "memory_utilization", 
        "disk_iops", 
        "network_throughput", 
        "request_success_rate"
    ]
    
    # Normalize the metrics values to a 0-1 scale for comparison
    normalized_data = {}
    for metric in metrics:
        values = [performance_data[provider][metric] for provider in providers if metric in performance_data[provider]]
        if not values:
            continue
            
        metric_min = min(values)
        metric_max = max(values)
        
        # Avoid division by zero
        range_value = metric_max - metric_min
        if range_value == 0:
            range_value = 1
            
        # Special treatment for request_success_rate (higher is better)
        if metric == "request_success_rate":
            normalized_data[metric] = {
                provider: (performance_data[provider][metric] - metric_min) / range_value 
                for provider in providers if metric in performance_data[provider]
            }
        else:
            # For other metrics, lower is better
            normalized_data[metric] = {
                provider: 1 - (performance_data[provider][metric] - metric_min) / range_value 
                for provider in providers if metric in performance_data[provider]
            }
    
    # Create radar chart
    fig = go.Figure()
    
    # Add traces for each provider
    for provider in providers:
        values = [normalized_data[metric][provider] for metric in metrics if metric in normalized_data and provider in normalized_data[metric]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
            fill='toself',
            name=provider.upper(),
            line_color=PROVIDER_COLORS.get(provider, "#333333")
        ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title="Cloud Provider Performance Comparison",
        height=500
    )
    
    return fig

def create_availability_timeline():
    """Create a timeline of provider availability over the past 24 hours"""
    # Get availability history
    availability_history = get_availability_history()
    
    if not availability_history:
        return go.Figure().update_layout(title="No availability history data")
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for each provider
    for provider, history in availability_history.items():
        if not history:
            continue
            
        # Convert timestamps to datetime
        timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in history]
        
        # Create status values (1 for up, 0 for down)
        status_values = [1 if entry["status"] else 0 for entry in history]
        
        # Add step line for each provider
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=status_values,
            mode='lines',
            name=provider.upper(),
            line=dict(
                color=PROVIDER_COLORS.get(provider, "#333333"),
                width=2,
                shape='hv'  # horizontal then vertical steps
            )
        ))
    
    # Update layout
    fig.update_layout(
        title="Cloud Provider Availability (Last 24 Hours)",
        xaxis_title="Time",
        yaxis=dict(
            title="Status",
            tickvals=[0, 1],
            ticktext=["Down", "Up"]
        ),
        height=400,
        hovermode="x unified"
    )
    
    return fig

def create_network_latency_chart():
    """Create a line chart of network latency over time"""
    # Get network latency data
    latency_data = get_network_latency()
    
    if not latency_data:
        return go.Figure().update_layout(title="No network latency data")
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for each provider
    for provider, data_points in latency_data.items():
        if not data_points:
            continue
            
        # Convert timestamps to datetime
        timestamps = [datetime.fromtimestamp(point["timestamp"]) for point in data_points]
        
        # Get latency values
        latency_values = [point["latency"] for point in data_points]
        
        # Add line for each provider
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=latency_values,
            mode='lines',
            name=provider.upper(),
            line=dict(
                color=PROVIDER_COLORS.get(provider, "#333333"),
                width=2
            )
        ))
    
    # Update layout
    fig.update_layout(
        title="Network Latency Over Time",
        xaxis_title="Time",
        yaxis_title="Latency (ms)",
        height=400,
        hovermode="x unified"
    )
    
    # Add threshold markers for good and degraded performance
    fig.add_shape(
        type="line",
        x0=min(timestamps),
        x1=max(timestamps),
        y0=50,
        y1=50,
        line=dict(
            color="green",
            width=1,
            dash="dash",
        )
    )
    
    fig.add_shape(
        type="line",
        x0=min(timestamps),
        x1=max(timestamps),
        y0=100,
        y1=100,
        line=dict(
            color="orange",
            width=1,
            dash="dash",
        )
    )
    
    # Add annotations for thresholds
    fig.add_annotation(
        x=max(timestamps),
        y=50,
        xanchor="right",
        text="Good",
        showarrow=False,
        font=dict(
            color="green"
        )
    )
    
    fig.add_annotation(
        x=max(timestamps),
        y=100,
        xanchor="right",
        text="Degraded",
        showarrow=False,
        font=dict(
            color="orange"
        )
    )
    
    return fig

def create_cost_breakdown_chart():
    """Create stacked bar chart showing cost breakdown by type for each provider"""
    # Get cost history
    cost_history = get_cost_history()
    
    if not cost_history:
        return go.Figure().update_layout(title="No cost data available")
    
    # Extract the latest cost entry for each provider
    latest_costs = {}
    for provider, history in cost_history.items():
        if history:
            latest_costs[provider] = history[-1]
    
    if not latest_costs:
        return go.Figure().update_layout(title="No cost data available")
    
    # Prepare data for stacked bar chart
    providers = list(latest_costs.keys())
    compute_costs = [latest_costs[provider].get("compute_cost", 0) for provider in providers]
    storage_costs = [latest_costs[provider].get("storage_cost", 0) for provider in providers]
    transfer_costs = [latest_costs[provider].get("transfer_cost", 0) for provider in providers]
    
    # Create stacked bar chart
    fig = go.Figure(data=[
        go.Bar(
            name="Compute",
            x=providers,
            y=compute_costs,
            marker_color="#1f77b4"
        ),
        go.Bar(
            name="Storage",
            x=providers,
            y=storage_costs,
            marker_color="#ff7f0e"
        ),
        go.Bar(
            name="Data Transfer",
            x=providers,
            y=transfer_costs,
            marker_color="#2ca02c"
        )
    ])
    
    # Change the bar mode to stacked
    fig.update_layout(
        barmode='stack',
        title="Cost Breakdown by Provider (Latest Day)",
        xaxis_title="Provider",
        yaxis_title="Cost (USD)",
        height=400
    )
    
    # Format x-axis labels to uppercase
    fig.update_xaxes(ticktext=[p.upper() for p in providers], tickvals=providers)
    
    # Add dollar signs to y-axis values
    fig.update_yaxes(tickprefix="$")
    
    return fig

def create_cost_trend_chart():
    """Create a line chart showing cost trends over time for each provider"""
    # Get cost history
    cost_history = get_cost_history()
    
    if not cost_history:
        return go.Figure().update_layout(title="No cost trend data available")
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for each provider
    for provider, history in cost_history.items():
        if not history:
            continue
            
        # Convert timestamps to datetime
        timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in history]
        
        # Get total cost values
        cost_values = [entry.get("total_cost", 0) for entry in history]
        
        # Add line for each provider
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=cost_values,
            mode='lines+markers',
            name=provider.upper(),
            line=dict(
                color=PROVIDER_COLORS.get(provider, "#333333"),
                width=2
            )
        ))
    
    # Update layout
    fig.update_layout(
        title="Daily Cost Trend (Last 30 Days)",
        xaxis_title="Date",
        yaxis_title="Total Cost (USD)",
        height=400,
        hovermode="x unified"
    )
    
    # Add dollar signs to y-axis values
    fig.update_yaxes(tickprefix="$")
    
    return fig

def create_availability_sla_gauge(provider=None):
    """Create a gauge chart showing availability percentage against SLA targets"""
    # Get availability percentages
    availability_percentages = calculate_availability_percentage(provider)
    
    if not availability_percentages:
        return go.Figure().update_layout(title="No availability data")
    
    # Define SLA thresholds
    sla_thresholds = {
        "critical": 95.0,
        "warning": 99.0,
        "target": 99.9,
        "ideal": 100.0
    }
    
    # Create a subplot for each provider
    providers = list(availability_percentages.keys()) if provider is None else [provider]
    fig = make_subplots(
        rows=1, 
        cols=len(providers),
        specs=[[{"type": "indicator"} for _ in providers]],
        subplot_titles=[p.upper() for p in providers]
    )
    
    # Add gauge for each provider
    for i, prov in enumerate(providers):
        value = availability_percentages.get(prov, 0)
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=value,
                domain={'row': 0, 'column': i},
                title={'text': f"Availability"},
                number={'suffix': "%", 'valueformat': ".2f"},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickvals': [95, 99, 99.9, 100]},
                    'bar': {'color': PROVIDER_COLORS.get(prov, "#333333")},
                    'steps': [
                        {'range': [0, sla_thresholds["critical"]], 'color': "red"},
                        {'range': [sla_thresholds["critical"], sla_thresholds["warning"]], 'color': "orange"},
                        {'range': [sla_thresholds["warning"], sla_thresholds["target"]], 'color': "yellow"},
                        {'range': [sla_thresholds["target"], sla_thresholds["ideal"]], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': sla_thresholds["target"]
                    }
                }
            ),
            row=1, col=i+1
        )
    
    # Update layout
    fig.update_layout(
        title="Cloud Provider Availability vs. SLA",
        height=300 if len(providers) <= 2 else 400
    )
    
    return fig

def create_failover_timeline_chart():
    """Create a timeline visualization of failover events"""
    # This is a simulated function as we don't have access to the actual failover logs
    # In a real implementation, this would parse the failover log file
    
    # Simulate some failover events for demonstration
    events = [
        {"timestamp": datetime.now() - timedelta(days=7, hours=3), "from": "aws", "to": "azure", "reason": "Network Disruption"},
        {"timestamp": datetime.now() - timedelta(days=5, hours=8), "from": "azure", "to": "gcp", "reason": "Storage Failure"},
        {"timestamp": datetime.now() - timedelta(days=3, hours=1), "from": "gcp", "to": "aws", "reason": "Instance Failure"},
        {"timestamp": datetime.now() - timedelta(days=1, hours=12), "from": "aws", "to": "azure", "reason": "Manual Failover"}
    ]
    
    # Create figure
    fig = go.Figure()
    
    # Add events as scatter points
    timestamps = [event["timestamp"] for event in events]
    
    # Create color map for event types
    reasons = list(set(event["reason"] for event in events))
    color_map = {reason: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, reason in enumerate(reasons)}
    
    # Create hover text
    hover_texts = [
        f"From: {event['from'].upper()}<br>To: {event['to'].upper()}<br>Reason: {event['reason']}<br>Time: {event['timestamp'].strftime('%Y-%m-%d %H:%M')}"
        for event in events
    ]
    
    # Plot each event with its reason color
    for reason in reasons:
        reason_events = [i for i, event in enumerate(events) if event["reason"] == reason]
        
        if not reason_events:
            continue
            
        fig.add_trace(go.Scatter(
            x=[timestamps[i] for i in reason_events],
            y=[1 for _ in reason_events],  # All at same level
            mode='markers',
            marker=dict(
                size=15,
                color=color_map[reason]
            ),
            name=reason,
            text=[hover_texts[i] for i in reason_events],
            hoverinfo="text"
        ))
    
    # Add failover connections
    for i in range(len(events)):
        fig.add_shape(
            type="line",
            x0=timestamps[i],
            x1=timestamps[i-1] if i > 0 else timestamps[i] + timedelta(hours=24),
            y0=1,
            y1=1,
            line=dict(
                color="gray",
                width=1,
                dash="dot"
            )
        )
    
    # Update layout
    fig.update_layout(
        title="Failover Events Timeline",
        xaxis_title="Date",
        yaxis=dict(
            visible=False
        ),
        height=250,
        showlegend=True,
        hovermode="closest"
    )
    
    return fig

def create_reliability_comparison_chart():
    """Create a bar chart comparing reliability metrics across different failure scenarios"""
    # Get metrics dataframe (using the metrics_table module function)
    from metrics_table import get_metrics_dataframe
    df = get_metrics_dataframe()
    
    if 'Reliability Score' not in df.columns:
        return go.Figure().update_layout(title="No reliability score data available")
    
    # Create horizontal bar chart sorted by reliability score
    df_sorted = df.sort_values('Reliability Score', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=df_sorted['Reliability Score'],
        y=df_sorted['Scenario'],
        orientation='h',
        marker_color='cornflowerblue',
        text=df_sorted['Reliability Score'].apply(lambda x: f"{x:.2f}"),
        textposition='auto'
    ))
    
    # Update layout
    fig.update_layout(
        title="Reliability Score by Failure Scenario",
        xaxis_title="Reliability Score (0-1)",
        xaxis=dict(
            range=[0.8, 1]  # Adjusted range to better visualize differences
        ),
        height=350
    )
    
    return fig

def create_realtime_performance_gauges():
    """Create gauge charts for real-time performance metrics"""
    # Get current performance data
    performance_data = get_performance_data()
    
    if not performance_data:
        return go.Figure().update_layout(title="No performance data available")
    
    # Get active provider
    from failover_manager import get_active_provider
    active_provider = get_active_provider()
    
    # Check if active provider has performance data
    if active_provider not in performance_data:
        return go.Figure().update_layout(title=f"No performance data for active provider ({active_provider})")
    
    # Get performance metrics for active provider
    provider_metrics = performance_data[active_provider]
    
    # Create subplots for each gauge
    fig = make_subplots(
        rows=1, 
        cols=3,
        specs=[[{"type": "indicator"} for _ in range(3)]],
        subplot_titles=["CPU Utilization", "Memory Utilization", "Response Time"]
    )
    
    # Add CPU gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=provider_metrics.get("cpu_utilization", 0),
            domain={'row': 0, 'column': 0},
            title={'text': "CPU"},
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': PROVIDER_COLORS.get(active_provider, "#333333")},
                'steps': [
                    {'range': [0, 50], 'color': "lightgreen"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ),
        row=1, col=1
    )
    
    # Add Memory gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=provider_metrics.get("memory_utilization", 0),
            domain={'row': 0, 'column': 1},
            title={'text': "Memory"},
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': PROVIDER_COLORS.get(active_provider, "#333333")},
                'steps': [
                    {'range': [0, 60], 'color': "lightgreen"},
                    {'range': [60, 85], 'color': "yellow"},
                    {'range': [85, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ),
        row=1, col=2
    )
    
    # Add Response Time gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=provider_metrics.get("average_response_time", 0) * 1000,  # Convert to ms
            domain={'row': 0, 'column': 2},
            title={'text': "Response Time"},
            number={'suffix': "ms"},
            gauge={
                'axis': {'range': [0, 500]},
                'bar': {'color': PROVIDER_COLORS.get(active_provider, "#333333")},
                'steps': [
                    {'range': [0, 100], 'color': "lightgreen"},
                    {'range': [100, 200], 'color': "yellow"},
                    {'range': [200, 500], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 200
                }
            }
        ),
        row=1, col=3
    )
    
    # Update layout
    fig.update_layout(
        title=f"Real-Time Performance Metrics for {active_provider.upper()}",
        height=250
    )
    
    return fig

def create_rpo_rto_analysis_chart():
    """Create an advanced analysis of RPO and RTO with error probabilities"""
    # Get metrics dataframe (using the metrics_table module function)
    from metrics_table import get_metrics_dataframe
    df = get_metrics_dataframe()
    
    if not all(col in df.columns for col in ['RPO', 'RTO', 'Data Loss Probability']):
        return go.Figure().update_layout(title="Missing required metrics data")
    
    # Create bubble chart
    fig = px.scatter(
        df,
        x='RPO',
        y='RTO',
        size='Cost',
        color='Data Loss Probability',
        hover_name='Scenario',
        size_max=60,
        color_continuous_scale='Viridis',
        labels={
            'RPO': 'Recovery Point Objective (minutes)',
            'RTO': 'Recovery Time Objective (seconds)',
            'Cost': 'Cost (USD)',
            'Data Loss Probability': 'Data Loss Probability'
        }
    )
    
    # Update layout
    fig.update_layout(
        title="RPO/RTO Analysis with Data Loss Risk",
        height=500,
        xaxis=dict(title='Recovery Point Objective (minutes)'),
        yaxis=dict(title='Recovery Time Objective (seconds)'),
        coloraxis_colorbar=dict(title='Data Loss Probability')
    )
    
    # Add annotations for quadrants
    fig.add_annotation(
        x=df['RPO'].min(),
        y=df['RTO'].min(),
        xref="x",
        yref="y",
        text="Best Recovery",
        showarrow=True,
        font=dict(
            family="Arial",
            size=12,
            color="#000000"
        ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=-40,
        ay=40,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ffffff",
        opacity=0.8
    )
    
    fig.add_annotation(
        x=df['RPO'].max(),
        y=df['RTO'].max(),
        xref="x",
        yref="y",
        text="Worst Recovery",
        showarrow=True,
        font=dict(
            family="Arial",
            size=12,
            color="#000000"
        ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=40,
        ay=-40,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ffffff",
        opacity=0.8
    )
    
    return fig