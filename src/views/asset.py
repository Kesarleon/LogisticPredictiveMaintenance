import streamlit as st
import pandas as pd
import numpy as np
from src.ui.components.kpi import render_kpi_grid
from src.ui.components.charts import plot_historical_trend, plot_sensor_readings
from src.data.loader import load_historical_data

def render_asset_diagnostics(df_current: pd.DataFrame):
    """
    Renders the detailed view for a single asset.
    """
    st.header("Diagnóstico Detallado de Activos")

    # Unit Selector
    col_sel, col_info = st.columns([1, 3])

    with col_sel:
        # Sort units by risk so high risk are at top
        sorted_units = df_current.sort_values(by='probabilidad_falla', ascending=False)['unit_id'].tolist()
        selected_unit = st.selectbox("Seleccionar Unidad", sorted_units)

    # Get Unit Data
    unit_row = df_current[df_current['unit_id'] == selected_unit].iloc[0]

    # High Level Unit KPIs
    with col_info:
        kpis = [
            {
                "label": "Probabilidad Falla Actual",
                "value": f"{unit_row['probabilidad_falla']:.1%}",
                "delta": "vs Promedio Flota",
                "delta_color": "inverse" if unit_row['probabilidad_falla'] > df_current['probabilidad_falla'].mean() else "normal"
            },
            {
                "label": "Costo Esperado Falla",
                "value": f"${unit_row['Costo_Falla_Total']:,.0f}",
                "help": "Impacto financiero si falla hoy"
            },
            {
                "label": "Horas Motor",
                "value": f"{unit_row['horas_motor']:,.0f} hrs",
                "delta": "Acumulado"
            },
            {
                "label": "Estado Actual",
                "value": unit_row['Accion_Sugerida'],
                "delta_color": "off"
            }
        ]
        render_kpi_grid(kpis)

    st.markdown("---")

    # Historical Analysis
    # We need the full history for charts
    df_history = load_historical_data()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Tendencia de Riesgo Predictivo")
        fig_trend = plot_historical_trend(df_history, selected_unit)
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("Monitoreo de Sensores Críticos")
        fig_sensors = plot_sensor_readings(df_history, selected_unit)
        st.plotly_chart(fig_sensors, use_container_width=True)

    # Technical Specs / Maintenance Log Placeholder
    with st.expander("📋 Ficha Técnica y Bitácora de Mantenimiento", expanded=False):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown(f"""
            - **ID Unidad:** {unit_row['unit_id']}
            - **Modelo:** Kenworth T680 (Simulado)
            - **Año:** 2019
            - **Motor:** Cummins X15
            """)
        with col_t2:
            st.markdown(f"""
            - **Último Mantenimiento:** {(pd.to_datetime('today') - pd.Timedelta(days=np.random.randint(10, 60))).strftime('%Y-%m-%d')}
            - **Próximo Servicio:** {(pd.to_datetime('today') + pd.Timedelta(days=np.random.randint(5, 30))).strftime('%Y-%m-%d')}
            - **Odómetro:** {unit_row['kilometraje']:,.0f} km
            """)
