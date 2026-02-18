import streamlit as st
import pandas as pd
from functions.vrp_solver import solve_vrp_optimization
from components.kpi_cards import render_kpi_cards
from components.map_view import render_map_view
from data_generator import get_locations_data, assign_unit_locations

def render_optimization_tab(df_current):
    st.header("Optimización Inteligente de Unidades (VRP con Riesgo)")
    st.markdown("""
    Modelo avanzado de asignación de rutas considerando riesgo predictivo, costos logísticos y capacidad de talleres.
    """)

    # 1. Sidebar Controls (Simulation Panel)
    st.sidebar.markdown("### ⚙️ Panel de Simulación (VRP)")

    risk_weight = st.sidebar.slider(
        "Peso del Riesgo (Aversión)",
        0.0, 1.0, 0.5,
        help="0: Ignora riesgo (solo costo transporte). 1: Prioriza seguridad (minimiza probabilidad de falla)."
    )

    cost_km = st.sidebar.number_input("Costo por Km ($)", value=1.5, step=0.1)

    use_capacity = st.sidebar.checkbox(
        "Restricción de Capacidad",
        value=True,
        help="Si está activo, los talleres y estaciones tienen un límite máximo de unidades."
    )

    if st.sidebar.button("🔄 Reoptimizar Modelo", type="primary"):
        st.cache_data.clear()

    # 2. Prepare Data
    locations_df = get_locations_data()

    # Ensure unit locations are present
    if 'lat' not in df_current.columns:
        # If df_current comes from main dashboard without 'lat', we merge or regenerate
        # But dashboard.py passes df_current which might not have lat/lon if not joined yet.
        # Let's generate/retrieve locations
        unit_locs = assign_unit_locations(df_current)
        # Merge if not already merged
        df_model = pd.merge(df_current, unit_locs, on='unit_id', how='left')
        # If simulate moving, we might need to handle lat_x, lat_y
        if 'lat_x' in df_model.columns:
            df_model['lat'] = df_model['lat_y'].fillna(df_model['lat_x'])
            df_model['lon'] = df_model['lon_y'].fillna(df_model['lon_x'])
    else:
        df_model = df_current.copy()

    # 3. Solve VRP
    params = {
        "risk_weight": risk_weight,
        "cost_km": cost_km,
        "use_capacity": use_capacity,
        "avg_failure_cost": 50000 # Default
    }

    with st.spinner("Ejecutando Solver de Optimización (Google OR-Tools)..."):
        df_results, summary = solve_vrp_optimization(df_model, locations_df, params)

    if df_results.empty:
        st.error(f"No se encontró solución óptima. {summary.get('status')}")
        return

    # 4. KPIs
    render_kpi_cards(df_results, df_model)

    st.markdown("---")

    # 5. Map
    col_map, col_details = st.columns([2, 1])

    with col_map:
        st.subheader("Mapa de Rutas Óptimas")
        render_map_view(df_results, locations_df)

    with col_details:
        st.subheader("Distribución de Destinos")
        dest_counts = df_results['dest_type'].value_counts()
        st.bar_chart(dest_counts)

        st.info(f"""
        **Costo Total Optimizado:** ${summary['total_cost']:,.2f}

        El modelo ha asignado {len(df_results)} unidades respetando las capacidades de {len(locations_df)} ubicaciones.
        """)

    # 6. Detailed Table
    st.subheader("Tabla de Decisiones Óptimas")

    table_cols = [
        'unit_id', 'risk_level', 'risk_prob',
        'dest_name', 'dest_type', 'distance_km',
        'expected_cost', 'justification'
    ]

    df_table = df_results[table_cols].sort_values(by='risk_prob', ascending=False)

    # Formatting
    df_table['risk_prob'] = df_table['risk_prob'].map('{:.1%}'.format)
    df_table['distance_km'] = df_table['distance_km'].map('{:.1f} km'.format)
    df_table['expected_cost'] = df_table['expected_cost'].map('${:,.2f}'.format)

    def highlight_risk(s):
        color = ''
        if s['dest_type'] == 'Taller':
            color = '#ffcccc' # Red tint for maintenance
        elif s['risk_level'] == 'Alto' and s['dest_type'] != 'Taller':
            color = '#ffffcc' # Yellow warning (High risk but operating)
        return [f'background-color: {color}' for v in s]

    st.dataframe(
        df_table.style.apply(highlight_risk, axis=1),
        use_container_width=True,
        hide_index=True
    )

    # 7. Extras / Explanations
    with st.expander("ℹ️ Detalles Técnicos y Escalabilidad"):
        st.markdown("""
        ### Arquitectura del Modelo VRP
        Este módulo utiliza **Google OR-Tools** (Solver MIP SCIP) para resolver un problema de asignación con costos generalizados.

        **Función Objetivo:** Minimizar $Z = \sum (C_{transporte} + C_{riesgo} - I_{operativo})$

        **Restricciones:**
        1. Cada unidad debe ir a un solo destino.
        2. La suma de unidades en un destino $j$ no puede exceder $Capacidad_j$.

        ### Escalabilidad SaaS
        - **Microservicio:** El solver (`vrp_solver.py`) puede desacoplarse en una API (FastAPI/Flask) que reciba JSON y devuelva la asignación.
        - **Cola de Tareas:** Para flotas > 1000 unidades, usar Celery/Redis para procesar la optimización en background.
        - **Geo-Sharding:** Dividir el problema por regiones geográficas si la flota es nacional/global.
        """)
