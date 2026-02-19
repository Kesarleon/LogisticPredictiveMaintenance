import streamlit as st
import pandas as pd
from src.ui.components.kpi import render_kpi_grid
from src.ui.components.charts import plot_risk_scatter, plot_risk_distribution

def render_executive_summary(df_current: pd.DataFrame):
    """
    Renders the high-level Executive Summary view.
    Focus: Financial Impact, Risk Overview, ROI.
    """
    st.header("Resumen Ejecutivo y Financiero")
    st.markdown("---")

    # 1. Financial KPIs
    total_savings = df_current['Ahorro_Potencial'].sum()
    units_high_risk = len(df_current[df_current['Nivel_Riesgo'] == "Alto"])
    total_cei = df_current['CEI'].sum()

    # ROI Logic (Simulated project cost)
    project_cost = 500000
    roi_percent = (total_savings / (df_current[df_current['Ahorro_Potencial'] > 0]['CEM'].sum()) * 100) if total_savings > 0 else 0
    months_to_breakeven = project_cost / total_savings if total_savings > 0 else 999

    metrics = [
        {
            "label": "Unidades en Riesgo Alto",
            "value": f"{units_high_risk}",
            "delta": None,
            "delta_color": "inverse",
            "help": "Total de unidades con probabilidad de falla > 70%"
        },
        {
            "label": "Ahorro Potencial Total",
            "value": f"${total_savings:,.2f}",
            "delta": "Mensual Est.",
            "delta_color": "normal",
            "help": "Suma de (CEI - CEM) para intervenciones justificadas"
        },
        {
            "label": "Costo Esperado Inacción (Riesgo)",
            "value": f"${total_cei:,.2f}",
            "delta_color": "inverse",
            "help": "Riesgo financiero total si no se realiza ninguna acción"
        },
        {
            "label": "Retorno Inversión (Payback)",
            "value": f"{months_to_breakeven:.1f} Meses",
            "help": f"Basado en costo proyecto ${project_cost:,.0f}"
        }
    ]

    render_kpi_grid(metrics)
    st.markdown("---")

    # 2. Strategic Charts
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Matriz de Riesgo: Probabilidad vs Impacto Financiero")
        # Filter for active units or relevant ones if needed
        fig_scatter = plot_risk_scatter(df_current)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c2:
        st.subheader("Distribución de Riesgo")
        fig_pie = plot_risk_distribution(df_current)
        st.plotly_chart(fig_pie, use_container_width=True)

    # 3. Actionable Insights (Priority Table)
    st.subheader("Ranking de Prioridad y Acciones Recomendadas")
    st.markdown("Listado de las unidades que requieren atención inmediata basado en el retorno económico de la intervención.")

    display_cols = [
        'unit_id', 'Nivel_Riesgo', 'probabilidad_falla',
        'Costo_Falla_Total', 'CEI', 'CEM',
        'Ahorro_Potencial', 'Accion_Sugerida'
    ]

    # Sort by Savings (Impact) then Probability
    df_display = df_current.sort_values(by=['Ahorro_Potencial', 'probabilidad_falla'], ascending=[False, False]).head(10)
    df_display = df_display[display_cols]

    # Format for display
    # Create a display copy to not mess up types if reused
    df_fmt = df_display.copy()
    df_fmt['probabilidad_falla'] = df_fmt['probabilidad_falla'].map('{:.1%}'.format)
    for col in ['Costo_Falla_Total', 'CEI', 'CEM', 'Ahorro_Potencial']:
        df_fmt[col] = df_fmt[col].map('${:,.2f}'.format)

    st.dataframe(
        df_fmt,
        use_container_width=True,
        hide_index=True
    )
