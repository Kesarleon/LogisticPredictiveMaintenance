import streamlit as st
from src.modules.logistic_risk.ui_module import render_logistic_risk_engine

def render_risk_view(df_current=None):
    """
    Renders the Logistic Risk Engine view.
    Accepts df_current just for signature consistency, but the module handles its own data generation.
    """
    render_logistic_risk_engine()
