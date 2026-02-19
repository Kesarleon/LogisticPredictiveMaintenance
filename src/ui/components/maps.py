import pydeck as pdk
import streamlit as st
import pandas as pd
import numpy as np

def _get_risk_color(prob):
    """Returns color based on probability."""
    if prob > 0.7: return [255, 0, 0, 200]    # Red
    if prob > 0.4: return [255, 165, 0, 200]  # Orange
    return [0, 255, 0, 200]                   # Green

def _get_location_color(loc_type):
    """Returns color based on location type."""
    if loc_type == 'Taller': return [255, 0, 255, 200] # Magenta
    return [0, 255, 255, 200]                         # Cyan

def render_fleet_map(df_units: pd.DataFrame, df_locations: pd.DataFrame):
    """
    Renders a map showing current fleet distribution and fixed locations.
    """
    # Prepare Unit Data
    # Ensure we have lat/lon. If merged, they might be there.
    if 'lat' not in df_units.columns or 'lon' not in df_units.columns:
        st.warning("No location data available for units.")
        return

    df_units = df_units.copy()
    df_units['color'] = df_units['probabilidad_falla'].apply(_get_risk_color)

    # Prepare Location Data
    df_locations = df_locations.copy()
    df_locations['color'] = df_locations['type'].apply(_get_location_color)
    df_locations['size'] = df_locations['type'].apply(lambda x: 20000 if x == 'Taller' else 10000)

    # Unit Layer
    layer_units = pdk.Layer(
        "ScatterplotLayer",
        data=df_units,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius=15000,
        pickable=True,
        auto_highlight=True,
    )

    # Location Layer
    layer_locations = pdk.Layer(
        "ScatterplotLayer",
        data=df_locations,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="size", # Scaled differently?
        pickable=True,
        stroked=True,
        filled=True,
        line_width_min_pixels=2,
    )

    # Tooltip
    tooltip = {
        "html": "<b>Unidad:</b> {unit_id} <br/> <b>Riesgo:</b> {probabilidad_falla}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    view_state = pdk.ViewState(
        latitude=23.6345,
        longitude=-102.5528,
        zoom=4,
        pitch=0,
    )

    r = pdk.Deck(
        layers=[layer_locations, layer_units],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
    )

    st.pydeck_chart(r)

def render_route_map(df_routes: pd.DataFrame, df_locations: pd.DataFrame):
    """
    Renders the optimization map showing routes from units to destinations.
    Expects df_routes to have: current_lon, current_lat, dest_lon, dest_lat.
    """
    # Similar to original map_view.py logic

    # ... (Reuse logic from previous thought but adapted) ...
    # Units
    df_routes = df_routes.copy()
    if 'risk_prob' in df_routes.columns:
        df_routes['color'] = df_routes['risk_prob'].apply(_get_risk_color)
    else:
        # Fallback if column names differ
        df_routes['color'] = df_routes['probabilidad_falla'].apply(_get_risk_color)

    # Locations
    df_locations = df_locations.copy()
    df_locations['color'] = df_locations['type'].apply(_get_location_color)
    df_locations['size'] = df_locations['type'].apply(lambda x: 200 if x == 'Taller' else 100) # Radius scale for visual

    # Layers
    layer_units = pdk.Layer(
        "ScatterplotLayer",
        data=df_routes,
        get_position=["current_lon", "current_lat"],
        get_fill_color="color",
        get_radius=15000,
        pickable=True,
        auto_highlight=True,
    )

    layer_locations = pdk.Layer(
        "ScatterplotLayer",
        data=df_locations,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="size * 100",
        pickable=True,
        stroked=True,
        filled=True,
        line_width_min_pixels=2,
    )

    layer_routes = pdk.Layer(
        "ArcLayer",
        data=df_routes,
        get_source_position=["current_lon", "current_lat"],
        get_target_position=["dest_lon", "dest_lat"],
        get_source_color=[0, 255, 0, 100],
        get_target_color=[255, 0, 0, 100],
        get_width=3,
        pickable=True,
    )

    tooltip = {
        "html": "<b>Unidad:</b> {unit_id} <br/> <b>Destino:</b> {dest_name}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

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
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
    )

    st.pydeck_chart(r)
