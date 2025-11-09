import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_distribution_pie_chart(performance_df):
    """Creates a Pie Chart showing stock distribution by Current Value."""
    if performance_df.empty:
        fig = go.Figure().add_annotation(
            x=0.5, y=0.5, text="No Data Available for Distribution Chart",
            showarrow=False, font={'size': 16}
        )
        fig.update_layout(height=400)
        return fig
        
    distribution_data = performance_df.groupby('Symbol')['Current Value'].sum().reset_index()
    
    fig = px.pie(
        distribution_data, 
        values='Current Value', 
        names='Symbol', 
        title='Portfolio Distribution by Current Market Value',
        hole=0.3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(t=50, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def create_growth_line_chart(cumulative_returns_df, benchmark_df):
    """Creates a Line Graph showing cumulative portfolio growth vs. a benchmark."""
    if cumulative_returns_df.empty and benchmark_df.empty:
        fig = go.Figure().add_annotation(
            x=0.5, y=0.5, text="No Historical Data Available for Comparison Chart",
            showarrow=False, font={'size': 16}
        )
        fig.update_layout(height=400)
        return fig

    fig = go.Figure()
    
    if not cumulative_returns_df.empty:
        fig.add_trace(go.Scatter(
            x=cumulative_returns_df['Date'], 
            y=cumulative_returns_df['Cumulative_Growth'],
            mode='lines', 
            name='My Portfolio',
            line=dict(width=3, color='#4CAF50')
        ))

    if not benchmark_df.empty:
        fig.add_trace(go.Scatter(
            x=benchmark_df['Date'], 
            y=benchmark_df['Benchmark_Growth'],
            mode='lines', 
            name='S&P 500 (^GSPC)',
            line=dict(width=2, color='#007BFF', dash='dash')
        ))

    fig.update_layout(
        title='Portfolio Growth vs. S&P 500 (Growth Factor)',
        xaxis_title="Date",
        yaxis_title="Growth Factor (Starting Value = 1.0)",
        hovermode="x unified"
    )
    return fig

def create_prediction_line_chart(historical_df, prediction_df):
    """Creates a line chart combining historical data and the forecast."""
    if historical_df.empty:
        fig = go.Figure().add_annotation(x=0.5, y=0.5, text="Insufficient Data for Prediction", showarrow=False)
        fig.update_layout(height=400)
        return fig

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=historical_df['Date'], y=historical_df['Cumulative_Growth'],
        mode='lines', name='Historical Growth',
        line=dict(color='#007BFF', width=2)
    ))

    prediction_trace_df = pd.concat([historical_df.tail(1), prediction_df])
    
    fig.add_trace(go.Scatter(
        x=prediction_trace_df['Date'], y=prediction_trace_df['Cumulative_Growth'],
        mode='lines', name='30-Day Forecast',
        line=dict(color='#FF4B4B', width=2, dash='dot')
    ))

    fig.update_layout(
        title='Portfolio Growth & 30-Day Forecast (Linear Regression)',
        xaxis_title="Date",
        yaxis_title="Growth Factor",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    return fig

def create_sector_distribution_chart(performance_df, value_type='Current Value'):
    """
    Creates a Pie Chart showing sector distribution based on a specified value type.
    """
    if performance_df.empty or 'Sector' not in performance_df.columns:
        fig = go.Figure().add_annotation(
            x=0.5, y=0.5, text="Sector data not available.",
            showarrow=False, font={'size': 16}
        )
        fig.update_layout(height=400)
        return fig
    
    # Group by Sector and sum the selected value type
    sector_data = performance_df.groupby('Sector')[value_type].sum().reset_index()
    
    title_text = f"Sector Distribution by {value_type}"
    
    fig = px.pie(
        sector_data, 
        values=value_type, 
        names='Sector', 
        title=title_text,
        hole=0.4 # Slightly larger hole
    )
    
    fig.update_traces(textposition='inside', textinfo='percent')
    fig.update_layout(
        margin=dict(t=50, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig