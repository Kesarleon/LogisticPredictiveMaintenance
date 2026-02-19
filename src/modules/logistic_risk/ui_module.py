import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from .risk_engine import LogisticRiskEngine

def render_logistic_risk_engine():
    """
    Renders the Logistic Risk Engine module in Streamlit.
    """
    st.header("Motor Predictivo de Riesgo Logístico")
    st.markdown("Gestión inteligente de rutas basada en modelado probabilístico.")

    # Initialize engine in session state to persist data/weights
    if 'logistic_engine' not in st.session_state:
        st.session_state['logistic_engine'] = LogisticRiskEngine()
        st.session_state['logistic_engine'].generate_simulated_data()

    engine = st.session_state['logistic_engine']

    # --- Control Panel ---
    st.subheader("Configuración de Escenario")

    col_ctrl_1, col_ctrl_2, col_ctrl_3 = st.columns([1, 1, 2])

    with col_ctrl_1:
        # Route Selector
        # Ensure data is generated
        if not engine.current_data:
            engine.generate_simulated_data()

        route_options = list(engine.current_data.keys())
        selected_route = st.selectbox("📍 Seleccionar Ruta", route_options, index=0)

    with col_ctrl_2:
        # Hour Selector
        selected_hour = st.slider("🕒 Hora de Salida", 0, 23, 8)

    with col_ctrl_3:
        # Weight Configuration
        with st.expander("⚖️ Calibración de Pesos (Modelo Matemático)"):
            c1, c2 = st.columns(2)
            with c1:
                w_traffic = st.slider("Tráfico", 0.0, 1.0, 0.4, 0.1)
                w_accident = st.slider("Accidentabilidad", 0.0, 1.0, 0.3, 0.1)
            with c2:
                w_reten = st.slider("Seguridad (Retenes)", 0.0, 1.0, 0.1, 0.1)
                w_climate = st.slider("Clima", 0.0, 1.0, 0.2, 0.1)

            if st.button("Aplicar Pesos"):
                engine.set_weights(w_traffic, w_accident, w_reten, w_climate)
                st.success("Modelo Recalibrado")

    st.markdown("---")

    # --- KPIs & Analysis ---

    # Run calculation for current selection
    risk_data = engine.aggregate_route_risk(selected_route, selected_hour)

    # KPI Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric("Risk Score Global", f"{risk_data['avg_risk']:.1%}", help="Promedio ponderado de riesgo en toda la ruta")

    risk_color = "normal"
    if risk_data['risk_level'] == "Alto": risk_color = "inverse"
    kpi2.metric("Nivel de Riesgo", risk_data['risk_level'], delta_color=risk_color)

    kpi3.metric("Velocidad Est.", f"{risk_data['estimated_speed_kmh']:.0f} km/h", delta="-5 km/h" if risk_data['estimated_speed_kmh'] < 60 else None)

    kpi4.metric("Índice Compuesto", f"{risk_data['composite_risk_index']:.2f}", help="Indice sintético (60% promedio, 40% pico máximo)")

    # --- Charts Row 1 ---

    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Análisis Temporal (24h)")
        # Calculate 24h curve
        # This is fast enough to do on the fly
        analysis_res = engine.find_optimal_departure(selected_route)
        df_analysis = analysis_res['analysis']
        best_hour = analysis_res['best_hour']

        fig_curve = px.line(df_analysis, x='hour', y=['composite_risk_index', 'avg_risk'],
                           title=f"Perfil de Riesgo Diario - {selected_route}",
                           labels={'value': 'Indice Riesgo', 'variable': 'Métrica'},
                           markers=True,
                           color_discrete_sequence=['#FF4B4B', '#1F77B4'])

        # Highlight selected hour
        fig_curve.add_vline(x=selected_hour, line_dash="dash", line_color="orange", annotation_text="Selección")
        # Highlight best hour
        fig_curve.add_vline(x=best_hour, line_dash="dot", line_color="green", annotation_text="Óptimo")

        # Add a rect for high risk?
        # fig_curve.add_hrect(y0=0.6, y1=1.0, line_width=0, fillcolor="red", opacity=0.1)

        st.plotly_chart(fig_curve, use_container_width=True)

        if st.button("✨ Simular Mejor Ventana Operativa"):
             st.success(f"La ventana óptima de salida es a las **{best_hour}:00** horas. Reducción de riesgo estimada: **{(1 - (analysis_res['min_risk_index']/risk_data['composite_risk_index'])):.1%}** respecto a la hora actual.")

    with c2:
        st.subheader("Distribución de Riesgo")
        df_details = risk_data['details']

        fig_hist = px.histogram(df_details, x="risk_score", nbins=15,
                               title="Histograma de Segmentos",
                               labels={'risk_score': 'Score de Riesgo'},
                               color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- Charts Row 2 ---

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Mapa de Calor: Intensidad de Riesgo")
        st.caption("Visualización de riesgo por hora (Eje X) y segmento de ruta (Eje Y). Zonas amarillas/rojas indican peligro.")

        # Generate heatmap data (subsampled for performance if needed, but 200x24 is small)
        # We need a matrix.
        # Let's create a list of dicts
        heatmap_rows = []
        for h in range(24):
            # We can reuse the loop or optimize later
            res = engine.aggregate_route_risk(selected_route, h)
            # res['details'] has 'segment_id' and 'risk_score'
            # We want to extract just that.
            subset = res['details'][['segment_id', 'risk_score']].copy()
            subset['hour'] = h
            heatmap_rows.append(subset)

        df_heatmap = pd.concat(heatmap_rows)

        fig_heat = px.density_heatmap(
            df_heatmap,
            x="hour",
            y="segment_id",
            z="risk_score",
            histfunc="avg",
            nbinsx=24,
            nbinsy=50,
            color_continuous_scale="RdYlGn_r", # Red-Yellow-Green reversed (Red is high risk)
            title="Heatmap Tèrmico de Riesgo"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with c4:
        st.subheader("Comparativa Estratégica")

        comp_data = []
        for r in route_options:
            res = engine.aggregate_route_risk(r, selected_hour)
            comp_data.append({
                'Ruta': r,
                'Riesgo Global': res['avg_risk'],
                'Pico Riesgo': res['max_segment_risk'],
            })

        df_comp = pd.DataFrame(comp_data)

        # Melt for grouped bar chart
        df_comp_melt = df_comp.melt(id_vars='Ruta', var_name='Métrica', value_name='Valor')

        fig_comp = px.bar(df_comp_melt, x='Ruta', y='Valor', color='Métrica', barmode='group',
                          title=f"Comparación entre Rutas ({selected_hour}:00)",
                          text_auto='.2f')
        st.plotly_chart(fig_comp, use_container_width=True)

    # --- Map Section ---
    st.markdown("---")
    st.subheader("Mapa de Riesgo por Segmento")

    col_map_1, col_map_2 = st.columns([1, 3])

    with col_map_1:
        st.markdown("**Configuración del Mapa**")
        map_risk_factor = st.radio(
            "Factor de Riesgo a Visualizar",
            options=["Riesgo Total", "Tráfico", "Accidentabilidad", "Retenes", "Clima"],
            index=0
        )

        factor_map = {
            "Riesgo Total": "risk_score",
            "Tráfico": "traffic_risk",
            "Accidentabilidad": "accident_risk",
            "Retenes": "reten_risk",
            "Clima": "climate_risk"
        }

        selected_factor_col = factor_map[map_risk_factor]

        st.caption("Los segmentos se colorean de Verde (Bajo) a Rojo (Alto) según la intensidad del factor seleccionado.")

    with col_map_2:
        import pydeck as pdk

        # Prepare data for PyDeck
        # risk_data['details'] has start_lat, start_lon, end_lat, end_lon
        df_map = risk_data['details'].copy()

        # Color function
        # We need a list of [r, g, b] for each row
        def get_color(val):
            # Normalize 0-1 just in case
            val = max(0, min(1, val))
            # Green to Red interpolation
            # Low risk (0): Green (0, 255, 0)
            # High risk (1): Red (255, 0, 0)
            return [int(val * 255), int((1 - val) * 255), 0]

        df_map['color'] = df_map[selected_factor_col].apply(get_color)

        # Create PathLayer data
        # PathLayer expects a path field: [[lon, lat], [lon, lat]]
        df_map['path'] = df_map.apply(lambda row: [[row['start_lon'], row['start_lat']], [row['end_lon'], row['end_lat']]], axis=1)

        # Center the map
        initial_view_state = pdk.ViewState(
            latitude=df_map['start_lat'].mean(),
            longitude=df_map['start_lon'].mean(),
            zoom=10,
            pitch=0,
        )

        layer = pdk.Layer(
            "PathLayer",
            df_map,
            pickable=True,
            get_color="color",
            width_scale=20,
            width_min_pixels=2,
            get_path="path",
            get_width=5
        )

        st.pydeck_chart(pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            initial_view_state=initial_view_state,
            layers=[layer],
            tooltip={"text": "Segmento: {segment_id}\nValor: {" + selected_factor_col + "}"}
        ))


    # --- Footer / Professional Touch ---
    with st.expander("ℹ️ Detalles Técnicos y Supuestos del Modelo"):
        st.markdown("""
        **Metodología:**
        El motor de riesgo utiliza una arquitectura hexagonal ligera. Los cálculos se basan en una suma ponderada de factores normalizados:
        - **Tráfico:** Densidad vehicular estimada por hora.
        - **Accidentabilidad:** Histórico de siniestros y condiciones de visibilidad.
        - **Seguridad:** Presencia de retenes y zonas de conflicto.
        - **Clima:** Vulnerabilidad del tramo a condiciones adversas.

        **Escalabilidad:**
        Este módulo está preparado para integrarse con APIs de tráfico en tiempo real (Google Maps/Waze) y modelos de ML (XGBoost) para predicción de incidentes.
        """)
