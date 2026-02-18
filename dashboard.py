import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from data_generator import generate_historical_data, get_locations_data, assign_unit_locations

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
</style>
""", unsafe_allow_html=True)

# Data Loading
@st.cache_data
def load_data():
    df_hist = generate_historical_data()
    return df_hist

df_history = load_data()
current_date = df_history['fecha'].max()
df_current = df_history[df_history['fecha'] == current_date].copy()

# Load Geospatial Data
locations_df = get_locations_data()
# We need to cache or fix the unit locations so they don't jump on every interaction
if 'unit_locations' not in st.session_state:
    st.session_state['unit_locations'] = assign_unit_locations(df_current)

unit_locations_df = st.session_state['unit_locations']

# Sidebar Settings
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

st.title("Dashboard Ejecutivo de Mantenimiento Predictivo")
st.markdown(f"**Fecha de corte:** {current_date.strftime('%Y-%m-%d')}")

# Create Tabs
tab1, tab2 = st.tabs(["Visión General", "Logística y Ruteo"])

# --- TAB 1: General Dashboard ---
with tab1:
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
    st.subheader("Ranking de Prioridad y Acciones Recomendadas")

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

    st.markdown("""
    **Definiciones:**
    - **CEI (Costo Esperado de Inacción):** Probabilidad de Falla × Costo Total Estimado de la Falla. Representa el riesgo financiero de no intervenir.
    - **CEM (Costo Estimado de Mantenimiento):** Suma del costo de mantenimiento preventivo y el costo de paro programado.
    """)

    st.markdown("---")

    # Row 4: Historical Analysis (Drill Down)
    st.subheader("Tendencia Histórica")

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
        fig_sensors = px.line(
            unit_hist,
            x='fecha',
            y=['temperatura_motor', 'vibracion_rms'],
            title=f"Sensores Críticos - {selected_unit}",
            labels={'value': 'Valor', 'variable': 'Sensor'}
        )
        st.plotly_chart(fig_sensors, use_container_width=True)


# --- TAB 2: Logistics & Routing ---
with tab2:
    st.header("Planificación de Rutas y Gestión de Talleres")
    st.markdown("Visualización de la flota y asignación óptima a Talleres (Riesgo Alto) o Estaciones de Carga (Operación Normal).")

    # Merge Location Data with Risk Data
    # unit_locations_df has [unit_id, lat, lon]
    # df_current has [unit_id, Nivel_Riesgo, probabilidad_falla, etc.]

    df_map = pd.merge(unit_locations_df, df_current[['unit_id', 'Nivel_Riesgo', 'probabilidad_falla', 'Accion_Sugerida']], on='unit_id')

    # Haversine Distance Helper
    def haversine_np(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
        c = 2 * np.arcsin(np.sqrt(a))
        km = 6367 * c
        return km

    # Calculate Optimal Destination
    results = []

    # Separate locations by type
    workshops = locations_df[locations_df['type'] == 'Taller']
    stations = locations_df[locations_df['type'] == 'Estación']

    for index, row in df_map.iterrows():
        u_lat = row['lat']
        u_lon = row['lon']
        risk = row['Nivel_Riesgo']

        # Determine target list based on risk
        if risk == 'Alto':
            targets = workshops
            target_type_str = "Taller (Reparación Urgente)"
        else:
            targets = stations
            target_type_str = "Estación (Carga/Descarga)"

        # Calculate distances to all relevant targets
        # We use numpy broadcasting for efficiency if lists were huge, but iteration is fine here
        distances = []
        for _, t_row in targets.iterrows():
            dist = haversine_np(u_lon, u_lat, t_row['lon'], t_row['lat'])
            distances.append((t_row['name'], t_row['lat'], t_row['lon'], dist))

        # Find min distance
        best_target = min(distances, key=lambda x: x[3])

        results.append({
            "unit_id": row['unit_id'],
            "lat_origin": u_lat,
            "lon_origin": u_lon,
            "risk": risk,
            "target_name": best_target[0],
            "lat_dest": best_target[1],
            "lon_dest": best_target[2],
            "distance_km": best_target[3],
            "action_type": target_type_str
        })

    df_routes = pd.DataFrame(results)

    # --- MAP VISUALIZATION ---

    # We will use graph_objects to layer scatter plots and lines
    fig_map = go.Figure()

    # 1. Plot Stations and Workshops
    fig_map.add_trace(go.Scattermapbox(
        lat=locations_df['lat'],
        lon=locations_df['lon'],
        mode='markers+text',
        marker=go.scattermapbox.Marker(
            size=15,
            color=['red' if t == 'Taller' else 'blue' for t in locations_df['type']],
            opacity=0.8
        ),
        text=locations_df['name'],
        textposition="bottom center",
        name="Puntos de Interés"
    ))

    # 2. Plot Units
    # Color by risk
    colors = {"Alto": "red", "Medio": "orange", "Bajo": "green"}
    for risk_cat in ["Alto", "Medio", "Bajo"]:
        subset = df_routes[df_routes['risk'] == risk_cat]
        if not subset.empty:
            fig_map.add_trace(go.Scattermapbox(
                lat=subset['lat_origin'],
                lon=subset['lon_origin'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=10,
                    color=colors[risk_cat]
                ),
                text=subset['unit_id'],
                name=f"Unidades - {risk_cat}"
            ))

    # 3. Draw Lines for High Risk Units (Priority Routing)
    high_risk_routes = df_routes[df_routes['risk'] == 'Alto']
    for index, row in high_risk_routes.iterrows():
        fig_map.add_trace(go.Scattermapbox(
            mode="lines",
            lon=[row['lon_origin'], row['lon_dest']],
            lat=[row['lat_origin'], row['lat_dest']],
            line=dict(width=2, color='red'),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Map Layout
    fig_map.update_layout(
        mapbox_style="open-street-map", # Free, no token needed
        mapbox=dict(
            center=dict(lat=23.6345, lon=-102.5528), # Center of Mexico
            zoom=4
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    st.plotly_chart(fig_map, use_container_width=True)

    # --- ROUTING TABLE ---
    st.subheader("Detalle de Asignaciones de Ruta")

    # Filter controls
    show_all = st.checkbox("Mostrar todas las unidades (Desmarcar para ver solo críticas)", value=True)

    table_view = df_routes.copy()
    if not show_all:
        table_view = table_view[table_view['risk'] == 'Alto']

    table_view = table_view[['unit_id', 'risk', 'target_name', 'action_type', 'distance_km']]
    table_view = table_view.sort_values(by=['risk', 'distance_km'], ascending=[True, True]) # Alto sorts before Bajo usually? No, Alto is 'Alto'.
    # Let's sort manually
    risk_order = {'Alto': 0, 'Medio': 1, 'Bajo': 2}
    table_view['risk_sort'] = table_view['risk'].map(risk_order)
    table_view = table_view.sort_values(by=['risk_sort', 'distance_km']).drop('risk_sort', axis=1)

    # Formatting
    table_view['distance_km'] = table_view['distance_km'].map('{:.1f} km'.format)
    table_view.columns = ['Unidad', 'Nivel Riesgo', 'Destino Asignado', 'Tipo de Acción', 'Distancia']

    def highlight_high_risk(s):
        return ['background-color: #ffcccc' if s['Nivel Riesgo'] == 'Alto' else '' for v in s]

    st.dataframe(
        table_view.style.apply(highlight_high_risk, axis=1),
        use_container_width=True,
        hide_index=True
    )

# Footer
st.markdown("""
<div style='text-align: center; color: grey; padding: 20px;'>
    <p>Dashboard generado por Sistema de Mantenimiento Predictivo v1.0</p>
</div>
""", unsafe_allow_html=True)
