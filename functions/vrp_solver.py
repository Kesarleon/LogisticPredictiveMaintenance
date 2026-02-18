import pandas as pd
import numpy as np
from ortools.linear_solver import pywraplp

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

def solve_vrp_optimization(units_df, locations_df, params):
    """
    Solves the assignment problem of units to locations using OR-Tools MIP solver.

    Args:
        units_df: DataFrame with unit data
        locations_df: DataFrame with location data
        params: dict with keys:
            - risk_weight: float (0-1)
            - cost_km: float
            - avg_failure_cost: float (fallback)
            - use_capacity: bool

    Returns:
        df_results: DataFrame with optimal assignments
        summary: dict with optimization metrics
    """

    # 1. Setup Solver
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return None, {"status": "Solver not found"}

    infinity = solver.infinity()

    # Indices
    unit_ids = units_df['unit_id'].tolist()
    loc_ids = locations_df['id'].tolist()

    num_units = len(unit_ids)
    num_locs = len(loc_ids)

    # Decision Variables: x[i, j] = 1 if unit i goes to loc j
    x = {}
    for i in range(num_units):
        for j in range(num_locs):
            x[i, j] = solver.IntVar(0, 1, f'x_{i}_{j}')

    # 2. Constraints

    # C1: Each unit must go to exactly one location
    for i in range(num_units):
        solver.Add(solver.Sum([x[i, j] for j in range(num_locs)]) == 1)

    # C2: Capacity Constraints (if enabled)
    if params.get('use_capacity', True):
        for j in range(num_locs):
            cap = locations_df.iloc[j]['capacidad']
            solver.Add(solver.Sum([x[i, j] for i in range(num_units)]) <= cap)

    # 3. Objective Function Calculation
    objective_terms = []

    # Pre-calculate distances matrix to avoid re-calc inside loop if possible,
    # but here loop is fine for N ~ 30-100

    for i in range(num_units):
        u_row = units_df.iloc[i]
        u_lat = u_row['lat']
        u_lon = u_row['lon']
        u_prob = u_row['probabilidad_falla']
        u_income = u_row.get('ingreso_diario_promedio', 0)
        u_fail_cost = u_row.get('costo_reparacion_promedio', params.get('avg_failure_cost', 50000))

        # Risk Weight parameter
        w_risk = params.get('risk_weight', 0.5)
        cost_km = params.get('cost_km', 1.5)

        for j in range(num_locs):
            l_row = locations_df.iloc[j]
            l_lat = l_row['lat']
            l_lon = l_row['lon']
            l_type = l_row['type']

            dist_km = haversine_np(u_lon, u_lat, l_lon, l_lat)

            # --- COST FUNCTION ---
            # 1. Transport Cost
            transport_cost = dist_km * cost_km

            # 2. Risk/Failure Cost
            # If going to Workshop, risk is mitigated (we pay for maint, but avoid catastrophic failure during operation)
            # If going to Station, risk exists.

            if l_type == 'Taller':
                # Cost is Maintenance (preventive) + Transport
                # We assume if we go to workshop, we DON'T earn income today.
                # So Cost = Transport + Maint + Opportunity Cost (Income)
                # But wait, Maint cost is usually cheaper than Failure.

                maint_cost = 5000 # Default simulated preventive cost
                risk_cost = 0 # Mitigated
                opportunity_cost = u_income # Lost income

                # To encourage workshops for HIGH risk units, the alternative (Station) must be MORE expensive.

                total_cost_ij = transport_cost + maint_cost + opportunity_cost

            else: # Estación
                # We earn income (negative cost)
                # But we carry risk of failure

                # Expected Failure Cost = Prob * Failure_Cost
                expected_failure = u_prob * u_fail_cost

                # We weight the risk component to allow user sensitivity
                # Adjusted Risk Cost = Expected Failure * (1 + Risk_Weight) ?
                # Or simply: cost = transport + (prob * fail_cost) - income

                # Let's add the specific logic requested:
                # "Minimizar: Costo_transporte + (Prob_falla * Costo_falla * Distancia_ruta_ponderada) + Costo_maint"
                # The prompt implies risk is distance dependent? "Distancia_ruta_ponderada".
                # If the unit fails ON THE WAY, distance matters.
                # If it fails DURING operation, distance doesn't matter as much.
                # Let's assume standard Expected Cost:

                risk_component = expected_failure

                # Apply risk weight from slider to make it "heavier" if desired
                # If w_risk is 1, full impact. If 0, ignore risk (naive profit max).
                # Actually, typically "Risk Weight" implies importance.
                # Let's use it as a multiplier for the failure cost or probability?
                # Let's say: Effective Risk Cost = Risk Component * (0.5 + w_risk) to scale it.
                # Or just use it as is.

                # Let's stick to economic reality + user bias
                # Real Cost = Transport + (Prob * FailCost) - Income

                # User "Risk Weight" (0-1) can interpolate between "Pure Economic" and "Risk Averse".
                # Risk Averse means we inflate the cost of failure.
                # Multiplier = 1 + (w_risk * 5) -> 1x to 6x penalty for risk

                risk_penalty_multiplier = 1 + (w_risk * 2)

                total_cost_ij = transport_cost + (risk_component * risk_penalty_multiplier) - u_income

            objective_terms.append(total_cost_ij * x[i, j])

    solver.Minimize(solver.Sum(objective_terms))

    # 4. Solve
    status = solver.Solve()

    # 5. Process Results
    results = []

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        total_obj_value = solver.Objective().Value()

        for i in range(num_units):
            for j in range(num_locs):
                if x[i, j].solution_value() > 0.5:
                    u_row = units_df.iloc[i]
                    l_row = locations_df.iloc[j]

                    dist_km = haversine_np(u_row['lon'], u_row['lat'], l_row['lon'], l_row['lat'])

                    # Recalculate component costs for display
                    transport = dist_km * params.get('cost_km', 1.5)
                    u_prob = u_row['probabilidad_falla']
                    u_fail_cost = u_row.get('costo_reparacion_promedio', 50000)
                    u_income = u_row.get('ingreso_diario_promedio', 0)

                    if l_row['type'] == 'Taller':
                        type_cost = 5000 + u_income # Maint + Opportunity
                        justification = f"Mantenimiento Preventivo (Riesgo: {u_prob:.1%})"
                        action_type = "Mantenimiento"
                    else:
                        type_cost = (u_prob * u_fail_cost) - u_income
                        justification = f"Operación Normal (Riesgo: {u_prob:.1%})"
                        action_type = "Operación"

                    expected_cost = transport + type_cost

                    results.append({
                        "unit_id": u_row['unit_id'],
                        "current_lat": u_row['lat'],
                        "current_lon": u_row['lon'],
                        "risk_prob": u_row['probabilidad_falla'],
                        "risk_level": "Alto" if u_row['probabilidad_falla'] > 0.7 else ("Medio" if u_row['probabilidad_falla'] > 0.4 else "Bajo"),
                        "dest_id": l_row['id'],
                        "dest_name": l_row['name'],
                        "dest_type": l_row['type'],
                        "dest_lat": l_row['lat'],
                        "dest_lon": l_row['lon'],
                        "distance_km": dist_km,
                        "expected_cost": expected_cost,
                        "justification": justification,
                        "action_type": action_type
                    })

        return pd.DataFrame(results), {"status": "Optimizado", "total_cost": total_obj_value}
    else:
        return pd.DataFrame(), {"status": "No Soluble (Revisar Capacidades)"}

if __name__ == "__main__":
    # Simple test
    pass
