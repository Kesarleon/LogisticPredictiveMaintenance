import streamlit as st
import pandas as pd
from src.data.generator import generate_historical_data, get_locations_data, assign_unit_locations

@st.cache_data
def load_historical_data():
    """
    Loads historical data for the fleet. Cached for performance.
    """
    return generate_historical_data()

def get_current_snapshot(df_history: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the dataframe corresponding to the most recent date in the history.
    """
    current_date = df_history['fecha'].max()
    return df_history[df_history['fecha'] == current_date].copy()

@st.cache_data
def load_fixed_locations():
    """
    Returns the dataframe of fixed locations (Stations, Workshops).
    """
    return get_locations_data()

def get_unit_locations(df_current_units: pd.DataFrame):
    """
    Returns the location of units. Uses session state to prevent
    jumping on reruns.
    """
    if 'unit_locations' not in st.session_state:
        st.session_state['unit_locations'] = assign_unit_locations(df_current_units)

    return st.session_state['unit_locations']

def clear_cache():
    """
    Clears data cache if needed.
    """
    st.cache_data.clear()
    if 'unit_locations' in st.session_state:
        del st.session_state['unit_locations']
