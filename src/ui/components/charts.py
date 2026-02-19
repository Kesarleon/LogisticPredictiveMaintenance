import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def plot_risk_scatter(df: pd.DataFrame):
    """
    Scatter plot: Probability vs Cost of Failure, sized by Potential Savings.
    """
    fig = px.scatter(
        df,
        x="probabilidad_falla",
        y="Costo_Falla_Total",
        size="Ahorro_Potencial",
        color="Nivel_Riesgo",
        color_discrete_map={"Alto": "red", "Medio": "orange", "Bajo": "green"},
        hover_data=["unit_id", "Accion_Sugerida", "CEI", "CEM"],
        labels={"probabilidad_falla": "Probabilidad de Falla", "Costo_Falla_Total": "Costo Total de Falla ($)"},
        title="Unidades por Riesgo y Costo"
    )
    fig.update_layout(template="plotly_white")
    return fig

def plot_risk_distribution(df: pd.DataFrame):
    """
    Donut chart of risk distribution.
    """
    risk_counts = df['Nivel_Riesgo'].value_counts()
    fig = px.pie(
        names=risk_counts.index,
        values=risk_counts.values,
        color=risk_counts.index,
        color_discrete_map={"Alto": "red", "Medio": "orange", "Bajo": "green"},
        hole=0.4,
        title="Distribución de Riesgo"
    )
    fig.update_layout(template="plotly_white")
    return fig

def plot_historical_trend(df_history: pd.DataFrame, unit_id: str):
    """
    Line chart of failure probability over time for a specific unit.
    """
    unit_data = df_history[df_history['unit_id'] == unit_id].sort_values(by='fecha')

    fig = px.line(
        unit_data,
        x='fecha',
        y='probabilidad_falla',
        title=f"Evolución de Probabilidad de Falla - {unit_id}",
        markers=True
    )

    # Add High Risk Threshold
    fig.add_hline(
        y=0.7,
        line_dash="dash",
        line_color="red",
        annotation_text="Límite Riesgo Alto"
    )
    fig.update_layout(template="plotly_white")
    return fig

def plot_sensor_readings(df_history: pd.DataFrame, unit_id: str):
    """
    Line chart of sensor readings over time for a specific unit.
    """
    unit_data = df_history[df_history['unit_id'] == unit_id].sort_values(by='fecha')

    fig = px.line(
        unit_data,
        x='fecha',
        y=['temperatura_motor', 'vibracion_rms'],
        title=f"Sensores Críticos - {unit_id}",
        labels={'value': 'Valor', 'variable': 'Sensor'}
    )
    fig.update_layout(template="plotly_white")
    return fig
