import streamlit as st

def render_kpi_grid(metrics):
    """
    Renders a row of KPI metrics.

    Args:
        metrics (list of dict): Each dict should have keys:
            - label (str)
            - value (str or number)
            - delta (str or number, optional)
            - delta_color (str, optional: "normal", "inverse", "off")
            - help (str, optional)
    """
    cols = st.columns(len(metrics))

    for col, metric in zip(cols, metrics):
        col.metric(
            label=metric.get("label"),
            value=metric.get("value"),
            delta=metric.get("delta"),
            delta_color=metric.get("delta_color", "normal"),
            help=metric.get("help")
        )
