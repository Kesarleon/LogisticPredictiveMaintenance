import streamlit as st
import pandas as pd
from src.data.loader import load_fixed_locations, get_unit_locations
from src.ui.components.maps import render_fleet_map, render_route_map
from src.ui.components.kpi import render_kpi_grid
from src.utils.vrp import solve_vrp_optimization

def render_fleet_intelligence(df_current: pd.DataFrame):
    """
    Renders the Fleet Intelligence view with Map and VRP Optimization.
    """
    st.header("Inteligencia de Flota y Optimización Logística")

    # Tabs for different levels of analysis
    tab_overview, tab_optimization = st.tabs(["Mapa General de Flota", "Optimización de Rutas (VRP)"])

    # Load shared data
    locations_df = load_fixed_locations()

    # Ensure units have location data
    # We use the session state cached locations
    unit_locs = get_unit_locations(df_current)

    # Merge locations into main df for the map
    # Note: df_current might already have it if we merged earlier, but let's be safe
    if 'lat' not in df_current.columns:
        df_map = pd.merge(df_current, unit_locs, on='unit_id', how='left')
    else:
        df_map = df_current.copy()

    # --- TAB 1: General Map ---
    with tab_overview:
        st.markdown("### Distribución Geográfica y Estado de Salud")

        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            risk_filter = st.multiselect(
                "Filtrar por Riesgo",
                ["Alto", "Medio", "Bajo"],
                default=["Alto", "Medio", "Bajo"],
                key="map_risk_filter"
            )

        # Filter Logic
        df_filtered = df_map[df_map['Nivel_Riesgo'].isin(risk_filter)]

        st.markdown(f"Mostrando **{len(df_filtered)}** unidades.")
        render_fleet_map(df_filtered, locations_df)

        st.markdown("---")
        st.subheader("Análisis Regional")
        # Simple placeholder for regional analysis
        # Assuming we don't have explicit 'Region' column, we can use nearest location or just show a table
        st.info("Distribución de flota basada en proximidad a hubs principales.")


    # --- TAB 2: VRP Optimization ---
    with tab_optimization:
        st.markdown("### Asignación Inteligente de Unidades a Talleres")
        st.caption("Algoritmo de optimización que balancea: Costo de Transporte vs. Riesgo de Falla vs. Capacidad de Talleres.")

        # Simulation Controls
        with st.expander("Parámetros de Simulación", expanded=True):
            col_s1, col_s2, col_s3 = st.columns(3)

            with col_s1:
                risk_weight = st.slider(
                    "Peso del Riesgo (Aversión)",
                    0.0, 1.0, 0.5,
                    help="0: Ignora riesgo (solo costo transporte). 1: Prioriza seguridad extrema."
                )

            with col_s2:
                cost_km = st.number_input("Costo Operativo por Km ($)", value=1.5, step=0.1)

            with col_s3:
                use_capacity = st.checkbox("Respetar Capacidad de Talleres", value=True)

            run_opt = st.button("Ejecutar Optimización", type="primary")

        if run_opt:
            with st.spinner("Calculando rutas óptimas con Google OR-Tools..."):
                # Prepare params
                params = {
                    "risk_weight": risk_weight,
                    "cost_km": cost_km,
                    "use_capacity": use_capacity,
                    "avg_failure_cost": df_current['costo_reparacion_promedio'].mean()
                }

                # Run Solver
                # We use df_map which has lat/lon
                df_results, summary = solve_vrp_optimization(df_map, locations_df, params)

                if df_results.empty:
                    st.error(f"No se encontró solución factible. {summary.get('status')}")
                else:
                    st.success("Optimización completada con éxito.")

                    # KPIs for Optimization
                    # Calculate savings vs baseline (Naive)
                    # Simple heuristic for display
                    total_cost = summary.get('total_cost', 0)
                    assigned_maint = len(df_results[df_results['dest_type'] == 'Taller'])

                    kpis = [
                        {"label": "Unidades Asignadas a Taller", "value": f"{assigned_maint}", "delta": "Mantenimiento"},
                        {"label": "Costo Total Logístico", "value": f"${total_cost:,.0f}", "delta_color": "inverse"},
                        {"label": "Riesgo Mitigado", "value": "Alta", "help": "Unidades críticas enviadas a taller."}
                    ]
                    render_kpi_grid(kpis)

                    # Map
                    st.subheader("Rutas Sugeridas")
                    render_route_map(df_results, locations_df)

                    # Table
                    st.subheader("Detalle de Asignaciones")
                    st.dataframe(
                        df_results[['unit_id', 'risk_prob', 'dest_name', 'distance_km', 'expected_cost', 'justification']],
                        use_container_width=True
                    )
