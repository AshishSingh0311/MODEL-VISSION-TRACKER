import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from metrics_table import get_metrics_dataframe

def create_performance_bar_chart():
    """Create a bar chart of performance metrics"""
    df = get_metrics_dataframe()
    
    # Melt the DataFrame to get it into a format suitable for plotting
    melted_df = pd.melt(
        df, 
        id_vars=['Scenario'], 
        value_vars=['Downtime', 'RTO', 'RPO', 'Failover Time'],
        var_name='Metric', 
        value_name='Seconds'
    )
    
    # Create the bar chart
    fig = px.bar(
        melted_df, 
        x='Scenario', 
        y='Seconds', 
        color='Metric',
        title='Performance Metrics by Failure Scenario',
        barmode='group',
        height=500
    )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title='Failure Scenario',
        yaxis_title='Time (seconds)',
        legend_title='Metric',
        font=dict(size=12),
        xaxis=dict(tickangle=-45)
    )
    
    return fig

def create_cost_bar_chart():
    """Create a bar chart of cost metrics"""
    df = get_metrics_dataframe()
    
    # Create the bar chart
    fig = px.bar(
        df, 
        x='Scenario', 
        y='Cost',
        title='Cost by Failure Scenario',
        height=400,
        color='Scenario'
    )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title='Failure Scenario',
        yaxis_title='Cost (USD)',
        font=dict(size=12),
        xaxis=dict(tickangle=-45),
        showlegend=False
    )
    
    # Add dollar signs to y-axis labels
    fig.update_yaxes(tickprefix='$')
    
    return fig

def create_rto_rpo_scatter():
    """Create a scatter plot of RTO vs RPO"""
    df = get_metrics_dataframe()
    
    # Create the scatter plot
    fig = px.scatter(
        df, 
        x='RTO', 
        y='RPO',
        text='Scenario',
        size='Cost',
        color='Scenario',
        title='RTO vs RPO by Failure Scenario',
        height=500
    )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title='Recovery Time Objective (seconds)',
        yaxis_title='Recovery Point Objective (minutes)',
        font=dict(size=12)
    )
    
    # Add text labels with hover info
    fig.update_traces(
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>RTO: %{x} seconds<br>RPO: %{y} minutes<br>Cost: $%{marker.size}<extra></extra>'
    )
    
    return fig

def create_downtime_comparison_chart():
    """Create a horizontal bar chart comparing downtime across scenarios"""
    df = get_metrics_dataframe()
    
    # Sort by downtime
    df = df.sort_values('Downtime', ascending=True)
    
    # Create the horizontal bar chart
    fig = px.bar(
        df, 
        y='Scenario', 
        x='Downtime',
        orientation='h',
        title='Downtime Comparison Across Failure Scenarios',
        height=400,
        color='Downtime',
        color_continuous_scale='Viridis'
    )
    
    # Update layout for better readability
    fig.update_layout(
        yaxis_title='Failure Scenario',
        xaxis_title='Downtime (seconds)',
        font=dict(size=12)
    )
    
    return fig

def create_metrics_radar_chart():
    """Create a radar chart of all metrics for each scenario"""
    df = get_metrics_dataframe()
    
    # Get unique scenarios
    scenarios = df['Scenario'].unique()
    
    # Define metrics for radar chart
    metrics = ['Downtime', 'RTO', 'RPO', 'Failover Time', 'Cost']
    
    # Create radar chart
    fig = go.Figure()
    
    for scenario in scenarios:
        scenario_data = df[df['Scenario'] == scenario]
        
        # Normalize data for radar chart (0-1 scale)
        values = []
        for metric in metrics:
            metric_max = df[metric].max()
            metric_min = df[metric].min()
            normalized = (scenario_data[metric].values[0] - metric_min) / (metric_max - metric_min) if metric_max > metric_min else 0
            values.append(normalized)
        
        # Add a new trace for each scenario
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
            fill='toself',
            name=scenario
        ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title='Normalized Metrics Comparison (Radar Chart)',
        height=500
    )
    
    return fig
