import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_generator import generate_historical_data

# Configuration
st.set_page_config(
    page_title="Dashboard Ejecutivo - Mantenimiento Predictivo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Corporate Look
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    h1, h2, h3 {
        color: #0e1117;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Data Loading
@st.cache_data
def load_data():
    return generate_historical_data()

df_history = load_data()
current_date = df_history['fecha'].max()
df_current = df_history[df_history['fecha'] == current_date].copy()

# Sidebar Settings
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1541/1541425.png", width=100) # Generic Icon
st.sidebar.title("Configuración Financiera")
st.sidebar.markdown("---")

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

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros")
risk_filter = st.sidebar.multiselect(
    "Nivel de Riesgo",
    options=["Alto", "Medio", "Bajo"],
    default=["Alto", "Medio", "Bajo"]
)

# Financial Calculations
CEM = costo_preventivo + costo_paro

# CEI: Costo Esperado de Inacción = Probabilidad * Costo Falla (Reparación)
# Note: In real life, Cost of Failure includes lost income + repair + collateral damage.
# Here we use simulated 'costo_reparacion_promedio' as base, maybe multiplier for 'Total Failure Cost'.
# Let's assume Costo Falla = Costo Reparación + (Ingreso Diario * Days Lost (simulated 3 days))
df_current['Costo_Falla_Total'] = df_current['costo_reparacion_promedio'] + (df_current['ingreso_diario_promedio'] * 3)

df_current['CEI'] = df_current['probabilidad_falla'] * df_current['Costo_Falla_Total']
df_current['CEM'] = CEM

# Recommendation Logic
def get_recommendation(row):
    if row['CEI'] > row['CEM']:
        return "Programar Mantenimiento"
    elif row['probabilidad_falla'] > 0.4:
        return "Monitorear"
    else:
        return "Operar Normal"

df_current['Accion_Sugerida'] = df_current.apply(get_recommendation, axis=1)

# Savings Logic
# Ahorro = CEI - CEM (only if Intervention is justified and cheaper than risk)
# If CEI > CEM, we act. Our cost is CEM. If we did nothing, expected cost was CEI. Saving = CEI - CEM.
df_current['Ahorro_Potencial'] = df_current.apply(lambda x: (x['CEI'] - x['CEM']) if x['CEI'] > x['CEM'] else 0, axis=1)

# Risk Categories
def get_risk_level(prob):
    if prob > 0.7: return "Alto"
    if prob > 0.4: return "Medio"
    return "Bajo"

df_current['Nivel_Riesgo'] = df_current['probabilidad_falla'].apply(get_risk_level)

# Filter Data
df_filtered = df_current[df_current['Nivel_Riesgo'].isin(risk_filter)]

# --- Main Layout ---

st.title("📊 Dashboard Ejecutivo de Mantenimiento Predictivo")
st.markdown(f"**Fecha de corte:** {current_date.strftime('%Y-%m-%d')}")

# Top KPIs
col1, col2, col3, col4 = st.columns(4)

total_savings = df_current['Ahorro_Potencial'].sum()
units_high_risk = len(df_current[df_current['Nivel_Riesgo'] == "Alto"])
total_cei = df_current['CEI'].sum()
roi_percent = (total_savings / (df_current[df_current['Ahorro_Potencial'] > 0]['CEM'].sum()) * 100) if total_savings > 0 else 0

# Project ROI Simulation
project_cost = 500000 # Simulated implementation cost
months_to_breakeven = project_cost / total_savings if total_savings > 0 else 999

col1.metric("Unidades en Riesgo Alto", f"{units_high_risk}", delta=None, delta_color="inverse")
col2.metric("Ahorro Potencial Total", f"${total_savings:,.2f}", delta="Mensual Est.")
col3.metric("Costo Esperado Inacción (Riesgo)", f"${total_cei:,.2f}", delta_color="inverse")
col4.metric("Retorno Inversión (Payback)", f"{months_to_breakeven:.1f} Meses", help=f"Basado en costo proyecto ${project_cost:,.0f}")

st.markdown("---")

# Row 2: Charts
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Matriz de Riesgo: Probabilidad vs Impacto Financiero")
    fig_scatter = px.scatter(
        df_filtered,
        x="probabilidad_falla",
        y="Costo_Falla_Total",
        size="Ahorro_Potencial",
        color="Nivel_Riesgo",
        color_discrete_map={"Alto": "red", "Medio": "orange", "Bajo": "green"},
        hover_data=["unit_id", "Accion_Sugerida", "CEI", "CEM"],
        labels={"probabilidad_falla": "Probabilidad de Falla", "Costo_Falla_Total": "Costo Total de Falla ($)"},
        title="Unidades por Riesgo y Costo"
    )
    # Add Break-even line where CEI = CEM
    # CEI = Prob * Cost => CEM = Prob * Cost => Cost = CEM / Prob
    # Use a shape or line? A line is tricky because y = CEM/x is a curve.
    # Let's plot points.

    st.plotly_chart(fig_scatter, use_container_width=True)

with c2:
    st.subheader("Distribución de Riesgo")
    risk_counts = df_current['Nivel_Riesgo'].value_counts()
    fig_pie = px.pie(
        names=risk_counts.index,
        values=risk_counts.values,
        color=risk_counts.index,
        color_discrete_map={"Alto": "red", "Medio": "orange", "Bajo": "green"},
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Row 3: Detailed Action Table
st.subheader("📋 Ranking de Prioridad y Acciones Recomendadas")

# Prepare table for display
display_cols = [
    'unit_id', 'Nivel_Riesgo', 'probabilidad_falla',
    'Costo_Falla_Total', 'CEI', 'CEM',
    'Ahorro_Potencial', 'Accion_Sugerida'
]

df_display = df_filtered[display_cols].sort_values(by='probabilidad_falla', ascending=False)

# Format columns
df_display['probabilidad_falla'] = df_display['probabilidad_falla'].map('{:.1%}'.format)
for col in ['Costo_Falla_Total', 'CEI', 'CEM', 'Ahorro_Potencial']:
    df_display[col] = df_display[col].map('${:,.2f}'.format)

# Color styling function for dataframe
def risk_color(val):
    color = 'green'
    if val == 'Alto': color = 'red'
    elif val == 'Medio': color = 'orange'
    return f'color: {color}; font-weight: bold'

st.dataframe(
    df_display.style.map(risk_color, subset=['Nivel_Riesgo']),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# Row 4: Historical Analysis (Drill Down)
st.subheader("📈 Tendencia Histórica")

selected_unit = st.selectbox("Seleccionar Unidad para ver detalle:", df_history['unit_id'].unique())

unit_hist = df_history[df_history['unit_id'] == selected_unit].sort_values(by='fecha')

h1, h2 = st.columns(2)

with h1:
    fig_trend = px.line(
        unit_hist,
        x='fecha',
        y='probabilidad_falla',
        title=f"Evolución de Probabilidad de Falla - {selected_unit}",
        markers=True
    )
    fig_trend.add_hline(y=0.7, line_dash="dash", line_color="red", annotation_text="Límite Riesgo Alto")
    st.plotly_chart(fig_trend, use_container_width=True)

with h2:
    # ROI over time / Accumulated savings?
    # We can simulate that if they had followed recommendations, they would have saved X.
    # For now let's show sensor trends like Temperature vs Vibration
    fig_sensors = px.line(
        unit_hist,
        x='fecha',
        y=['temperatura_motor', 'vibracion_rms'],
        title=f"Sensores Críticos - {selected_unit}",
        labels={'value': 'Valor', 'variable': 'Sensor'}
    )
    st.plotly_chart(fig_sensors, use_container_width=True)

# Footer
st.markdown("""
<div style='text-align: center; color: grey; padding: 20px;'>
    <p>Dashboard generado por Sistema de Mantenimiento Predictivo v1.0</p>
</div>
""", unsafe_allow_html=True)
