import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime

from health_check import get_current_health_status
from failover_manager import get_active_provider
from advanced_failover import advanced_failover_manager
from performance_monitor import get_performance_data
from db_manager import db_manager

# Color schemes for providers
PROVIDER_COLORS = {
    "aws": "#FF9900",      # AWS Orange
    "azure": "#0078D4",    # Azure Blue
    "gcp": "#4285F4"       # Google Blue
}

def render_disaster_recovery_dashboard():
    """Render the advanced disaster recovery dashboard page"""
    st.title("Disaster Recovery Management")
    st.markdown("### Advanced Failover Decision Engine and Disaster Simulation")
    
    # Get current status
    health_status = get_current_health_status()
    active_provider = get_active_provider()
    
    # Left column: Status and Controls
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Current Active Provider
        st.subheader("Active Cloud Provider")
        active_provider_style = f"""
        <div style="background-color:{PROVIDER_COLORS.get(active_provider, '#333333')}; 
                    padding:10px; 
                    border-radius:5px; 
                    color:white; 
                    font-size:24px; 
                    text-align:center;
                    margin-bottom:20px;">
            {active_provider.upper()}
        </div>
        """
        st.markdown(active_provider_style, unsafe_allow_html=True)
        
        # Provider Status Indicators
        st.subheader("Provider Health Status")
        
        # Display health status for each provider
        for provider in ["aws", "azure", "gcp"]:
            status = health_status.get(provider, {}).get("status", False)
            provider_color = PROVIDER_COLORS.get(provider, "#333333")
            
            # Create color-coded indicator
            status_indicator = f"""
            <div style="display:flex; align-items:center; margin-bottom:10px;">
                <div style="background-color:{provider_color}; width:10px; height:20px; margin-right:10px;"></div>
                <div style="flex-grow:1;">{provider.upper()}</div>
                <div style="background-color:{'green' if status else 'red'}; 
                            color:white; 
                            padding:2px 10px; 
                            border-radius:10px; 
                            text-align:center;
                            min-width:80px;">
                    {'HEALTHY' if status else 'UNHEALTHY'}
                </div>
            </div>
            """
            st.markdown(status_indicator, unsafe_allow_html=True)
        
        # Failover Controls
        st.subheader("Failover Controls")
        
        # Manual Failover
        manual_target = st.selectbox(
            "Select provider for manual failover:",
            ["aws", "azure", "gcp"],
            index=["aws", "azure", "gcp"].index(active_provider) if active_provider in ["aws", "azure", "gcp"] else 0
        )
        
        failover_reason = st.text_input("Failover reason:", "Manual failover initiated by operator")
        
        if st.button("Execute Manual Failover"):
            if manual_target == active_provider:
                st.warning(f"{manual_target.upper()} is already the active provider.")
            else:
                # Perform manual failover using advanced logic
                with st.spinner(f"Failing over to {manual_target.upper()}..."):
                    success = advanced_failover_manager.manual_failover(manual_target, failover_reason)
                    
                    if success:
                        st.success(f"Successfully failed over from {active_provider.upper()} to {manual_target.upper()}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failover failed. See logs for details.")
        
        # Disaster Simulation
        st.subheader("Disaster Simulation")
        
        st.markdown("Simulate disaster scenarios to test failover capabilities:")
        
        disaster_type = st.radio(
            "Disaster Type:",
            ["Provider Failure", "Performance Degradation", "Network Outage", "Random Scenario"]
        )
        
        if st.button("Simulate Disaster"):
            scenario_map = {
                "Provider Failure": "provider_failure",
                "Performance Degradation": "performance_degradation",
                "Network Outage": "network_outage",
                "Random Scenario": "random"
            }
            
            scenario = scenario_map[disaster_type]
            
            with st.spinner(f"Simulating {disaster_type.lower()}..."):
                result = advanced_failover_manager.simulate_disaster_scenario(scenario)
                
                if result:
                    st.success(f"Disaster scenario triggered automatic failover")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.info("Disaster scenario did not trigger automatic failover. System maintained stability.")
    
    # Right column: Provider Scoring and Metrics
    with col2:
        # Provider Scores
        st.subheader("Provider Scoring Analysis")
        
        # Calculate scores for all providers
        scores = {}
        for provider in ["aws", "azure", "gcp"]:
            scores[provider] = advanced_failover_manager.calculate_provider_score(provider, health_status)
        
        # Create a bar chart of provider scores
        score_df = pd.DataFrame({
            "Provider": list(scores.keys()),
            "Score": list(scores.values())
        })
        
        fig = px.bar(
            score_df,
            x="Provider",
            y="Score",
            color="Provider",
            color_discrete_map=PROVIDER_COLORS,
            title="Provider Scores (Higher is Better)",
            labels={"Provider": "Cloud Provider", "Score": "Decision Score"}
        )
        
        fig.update_layout(
            xaxis_title="Cloud Provider",
            yaxis_title="Decision Score",
            yaxis_range=[0, 100],
            xaxis=dict(tickvals=["aws", "azure", "gcp"], ticktext=["AWS", "AZURE", "GCP"])
        )
        
        # Add a threshold line for minimum acceptable score
        fig.add_shape(
            type="line",
            x0=-0.5,
            x1=2.5,
            y0=50,
            y1=50,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Score Component Breakdown
        st.subheader("Score Component Breakdown")
        
        # Get performance data
        performance_data = get_performance_data()
        
        # Create a table of scoring factors
        factor_data = []
        
        for provider in ["aws", "azure", "gcp"]:
            # Health Status
            is_healthy = provider in health_status and health_status[provider].get('status', False)
            health_score = 50 if is_healthy else 0
            
            # Recent history score calculation (simplified)
            history = advanced_failover_manager.health_history.get(provider, [])
            if history:
                recent_health_ratio = sum(1 for status in history if status.get('healthy', False)) / len(history)
                history_score = 20 * recent_health_ratio * advanced_failover_manager.provider_weights[provider]['reliability']
            else:
                history_score = 0
            
            # Performance score calculation (simplified)
            if provider in performance_data:
                perf = performance_data[provider]
                response_time = perf.get('average_response_time', 0.5)
                response_score = max(0, 10 - (response_time * 10))
                success_rate = perf.get('request_success_rate', 95) / 100
                success_score = success_rate * 10
                perf_score = (response_score + success_score) * advanced_failover_manager.provider_weights[provider]['performance']
            else:
                perf_score = 0
            
            # Cost score approximation
            cost_score = scores[provider] - (health_score + history_score + perf_score)
            
            factor_data.append({
                "Provider": provider.upper(),
                "Health Status": round(health_score, 1),
                "Reliability History": round(history_score, 1),
                "Performance": round(perf_score, 1),
                "Cost Efficiency": round(cost_score, 1),
                "Total Score": round(scores[provider], 1)
            })
        
        # Convert to DataFrame and display
        factor_df = pd.DataFrame(factor_data)
        st.dataframe(factor_df, use_container_width=True)
    
    # Failover History Section
    st.header("Failover Event History")
    
    # Get recent failover events
    recent_events = advanced_failover_manager.get_recent_failover_events(limit=10)
    
    if recent_events:
        # Convert to DataFrame
        event_data = []
        
        for event in recent_events:
            event_data.append({
                "Time": datetime.fromisoformat(event["occurred_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "From": event["from_provider"].upper(),
                "To": event["to_provider"].upper(),
                "Reason": event["reason"] if "reason" in event else "Not specified",
                "Type": "Manual" if event.get("is_manual", False) else "Automatic"
            })
        
        events_df = pd.DataFrame(event_data)
        st.dataframe(events_df, use_container_width=True)
    else:
        st.info("No failover events have occurred yet.")
    
    # Timeline visualization of failover events
    st.subheader("Failover Events Timeline")
    
    try:
        from advanced_graphs import create_failover_timeline_chart
        
        st.plotly_chart(create_failover_timeline_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying failover timeline: {str(e)}")
    
    # Disaster Recovery Metrics
    st.header("Disaster Recovery Metrics")
    
    # Get recovery metrics
    recovery_metrics = db_manager.get_recovery_metrics()
    
    if recovery_metrics:
        # Convert to DataFrame
        metrics_df = pd.DataFrame.from_dict(recovery_metrics, orient='index')
        metrics_df.reset_index(inplace=True)
        metrics_df.rename(columns={'index': 'Scenario'}, inplace=True)
        
        # Format columns
        if 'RPO' in metrics_df.columns:
            metrics_df['RPO'] = metrics_df['RPO'].apply(lambda x: f"{x} min")
        
        if 'Cost' in metrics_df.columns:
            metrics_df['Cost'] = metrics_df['Cost'].apply(lambda x: f"${x}")
        
        for col in ['Downtime', 'RTO', 'Failover Time']:
            if col in metrics_df.columns:
                metrics_df[col] = metrics_df[col].apply(lambda x: f"{x} s")
        
        st.dataframe(metrics_df, use_container_width=True)
        
        # Comparison chart
        st.subheader("Recovery Time Objectives (RTO) Comparison")
        
        try:
            from advanced_graphs import create_rpo_rto_analysis_chart
            
            st.plotly_chart(create_rpo_rto_analysis_chart(), use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying RPO/RTO analysis: {str(e)}")
    else:
        st.info("No recovery metrics available.")