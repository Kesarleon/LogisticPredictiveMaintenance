import streamlit as st

def render_kpi_cards(df_results, df_units):
    """
    Renders the KPI cards for the optimization results.
    """
    total_units = len(df_units)
    total_to_workshop = len(df_results[df_results['dest_type'] == 'Taller'])

    # Savings (Simulated comparison)
    # Baseline: Assume naive nearest location without optimization
    # Here we simulate savings as "Risk Mitigation" - e.g., if we sent High Risk units to Stations, they fail.
    # Cost = (Sum of Expected Costs in Optimized Plan) vs (Naive Plan Cost)
    # For now, let's use a simple heuristic for display:
    # "Ahorro Esperado Hoy" = Cost of prevented failures (High Risk * Fail Cost) - Maintenance Cost

    high_risk_units = df_results[(df_results['risk_prob'] > 0.7) & (df_results['dest_type'] == 'Taller')]
    prevented_failures = len(high_risk_units)
    avg_fail_cost = 50000 # Configurable?
    avg_maint_cost = 5000

    savings = prevented_failures * (avg_fail_cost - avg_maint_cost)

    # Weighted Risk
    weighted_risk = (df_units['probabilidad_falla'].mean() * 100)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Unidades Activas", f"{total_units}", delta=f"{total_units - total_to_workshop} en Operación")
    col2.metric("Enviadas a Taller", f"{total_to_workshop}", delta_color="inverse")
    col3.metric("Ahorro Esperado (Hoy)", f"${savings:,.0f}", delta="vs No Optimizado")
    col4.metric("Riesgo Promedio Flota", f"{weighted_risk:.1f}%", delta_color="inverse")
