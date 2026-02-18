import pydeck as pdk
import streamlit as st
import pandas as pd

def render_map_view(df_results, locations_df):
    """
    Renders a Pydeck map with units, locations, and route lines.
    """

    # 1. Colors
    # Units: Green (Low Risk), Yellow (Med), Red (High)
    def get_color(prob):
        if prob > 0.7: return [255, 0, 0, 200]
        if prob > 0.4: return [255, 165, 0, 200]
        return [0, 255, 0, 200]

    df_results['color'] = df_results['risk_prob'].apply(get_color)

    # Locations: Blue (Station), Purple (Workshop)
    def get_loc_color(t):
        if t == 'Taller': return [128, 0, 128, 200]
        return [0, 0, 255, 200]

    locations_df['color'] = locations_df['type'].apply(get_loc_color)
    locations_df['size'] = locations_df['type'].apply(lambda x: 200 if x == 'Taller' else 100)

    # 2. Layers

    # Unit Layer
    layer_units = pdk.Layer(
        "ScatterplotLayer",
        data=df_results,
        get_position=["current_lon", "current_lat"],
        get_fill_color="color",
        get_radius=15000, # meters
        pickable=True,
        auto_highlight=True,
    )

    # Location Layer
    layer_locations = pdk.Layer(
        "ScatterplotLayer",
        data=locations_df,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="size * 100",
        pickable=True,
        stroked=True,
        filled=True,
        line_width_min_pixels=2,
    )

    # Route Layer (Arcs)
    # Using ArcLayer or LineLayer. ArcLayer looks cooler for routes.
    layer_routes = pdk.Layer(
        "ArcLayer",
        data=df_results,
        get_source_position=["current_lon", "current_lat"],
        get_target_position=["dest_lon", "dest_lat"],
        get_source_color=[0, 255, 0, 100],
        get_target_color=[255, 0, 0, 100],
        get_width=3,
        pickable=True,
    )

    # 3. Tooltip
    tooltip = {
        "html": "<b>Unidad:</b> {unit_id} <br/> <b>Riesgo:</b> {risk_prob} <br/> <b>Destino:</b> {dest_name}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    # 4. View State
    view_state = pdk.ViewState(
        latitude=23.6345,
        longitude=-102.5528,
        zoom=4,
        pitch=0,
    )

    r = pdk.Deck(
        layers=[layer_routes, layer_locations, layer_units],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v9"
    )

    st.pydeck_chart(r)

    # Legend (Text based for simplicity)
    st.markdown("""
    <div style='display: flex; gap: 10px; font-size: 0.8em; color: gray;'>
        <span>🔴 Unidad Riesgo Alto</span>
        <span>🟠 Unidad Riesgo Medio</span>
        <span>🟢 Unidad Riesgo Bajo</span>
        <span>🟣 Taller</span>
        <span>🔵 Estación</span>
    </div>
    """, unsafe_allow_html=True)
