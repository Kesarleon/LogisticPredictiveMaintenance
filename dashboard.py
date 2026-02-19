import streamlit as st
import pandas as pd
from src.ui.styles import apply_custom_styles
from src.data.loader import load_historical_data, get_current_snapshot
from src.data.financials import enrich_data_with_financials
from src.views.summary import render_executive_summary
from src.views.fleet import render_fleet_intelligence
from src.views.asset import render_asset_diagnostics
from src.views.risk import render_risk_view

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Dashboard Ejecutivo - Mantenimiento Predictivo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Apply Styles ---
apply_custom_styles()

# --- 3. Data Loading & Logic Layer ---
@st.cache_data
def load_and_process_data(preventive_cost, downtime_cost):
    # Load raw history
    df_hist = load_historical_data()
    # Get current snapshot
    df_curr = get_current_snapshot(df_hist)
    # Apply Financial Logic
    df_enriched = enrich_data_with_financials(df_curr, preventive_cost, downtime_cost)
    return df_hist, df_enriched

# --- 4. Sidebar Controls ---
st.sidebar.title("Configuración Financiera")
st.sidebar.caption("Parámetros para cálculo de ROI y CEI vs CEM")

costo_preventivo = st.sidebar.number_input(
    "Costo Mantenimiento Preventivo ($)",
    min_value=0.0,
    value=5000.0,
    step=500.0,
    help="Costo promedio de realizar un mantenimiento preventivo estándar."
)

costo_paro = st.sidebar.number_input(
    "Costo Paro Programado ($)",
    min_value=0.0,
    value=2000.0,
    step=500.0,
    help="Costo operativo/lucro cesante por detener la unidad."
)

# Load Data
df_history, df_current = load_and_process_data(costo_preventivo, costo_paro)

st.sidebar.markdown("---")

# Navigation
st.sidebar.title("Navegación")
selection = st.sidebar.radio(
    "Ir a:",
    [
        "Resumen Ejecutivo",
        "Inteligencia de Flota",
        "Diagnóstico de Activos",
        "Motor de Riesgo Logístico"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    f"""
    **Estado del Sistema:**
    - Unidades Monitoreadas: {len(df_current)}
    - Fecha Corte: {df_history['fecha'].max().strftime('%Y-%m-%d')}
    """
)

# --- 5. Main Content Routing ---

if selection == "Resumen Ejecutivo":
    render_executive_summary(df_current)

elif selection == "Inteligencia de Flota":
    render_fleet_intelligence(df_current)

elif selection == "Diagnóstico de Activos":
    render_asset_diagnostics(df_current)

elif selection == "Motor de Riesgo Logístico":
    render_risk_view(df_current)

# --- Footer ---
st.markdown("""
<div style='text-align: center; color: grey; padding: 20px; font-size: 0.8em;'>
    <p>Plataforma de Mantenimiento Predictivo v2.0 | Modular & Scalable Architecture</p>
</div>
""", unsafe_allow_html=True)
