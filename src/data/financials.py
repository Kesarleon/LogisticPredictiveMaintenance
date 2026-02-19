import pandas as pd
import numpy as np

def calculate_cem(costo_preventivo: float, costo_paro: float) -> float:
    """
    Calculates the Expected Cost of Maintenance (CEM).
    CEM = Cost of Preventive Maintenance + Cost of Planned Downtime
    """
    return costo_preventivo + costo_paro

def calculate_cei(probabilidad_falla: float, costo_reparacion: float, ingreso_diario: float, dias_perdidos: int = 3) -> float:
    """
    Calculates the Expected Cost of Inaction (CEI).
    CEI = Probability of Failure * Total Failure Cost
    Total Failure Cost = Repair Cost + (Daily Income * Days Lost)
    """
    costo_total_falla = costo_reparacion + (ingreso_diario * dias_perdidos)
    return probabilidad_falla * costo_total_falla

def get_recommendation(cei: float, cem: float, prob_falla: float) -> str:
    """
    Determines the recommended action based on financial comparison.
    """
    if cei > cem:
        return "Programar Mantenimiento"
    elif prob_falla > 0.4:
        return "Monitorear"
    else:
        return "Operar Normal"

def get_risk_level(prob: float) -> str:
    """
    Classifies risk based on probability.
    """
    if prob > 0.7: return "Alto"
    if prob > 0.4: return "Medio"
    return "Bajo"

def enrich_data_with_financials(df: pd.DataFrame, costo_preventivo: float, costo_paro: float) -> pd.DataFrame:
    """
    Applies financial calculations to the dataframe.
    """
    # Create a copy to avoid SettingWithCopy warnings if a slice is passed
    df = df.copy()

    # Calculate CEM (Constant for now, but could be dynamic per unit type if needed)
    cem = calculate_cem(costo_preventivo, costo_paro)
    df['CEM'] = cem

    # Calculate Total Failure Cost (Intermediate step for clarity)
    # Assuming 3 days lost as per original logic
    df['Costo_Falla_Total'] = df['costo_reparacion_promedio'] + (df['ingreso_diario_promedio'] * 3)

    # Calculate CEI
    df['CEI'] = df.apply(
        lambda row: calculate_cei(
            row['probabilidad_falla'],
            row['costo_reparacion_promedio'],
            row['ingreso_diario_promedio']
        ), axis=1
    )

    # Recommendations & Risk
    df['Accion_Sugerida'] = df.apply(
        lambda row: get_recommendation(row['CEI'], row['CEM'], row['probabilidad_falla']), axis=1
    )

    df['Nivel_Riesgo'] = df['probabilidad_falla'].apply(get_risk_level)

    # Potential Savings (CEI - CEM if Action is justified)
    df['Ahorro_Potencial'] = df.apply(
        lambda x: (x['CEI'] - x['CEM']) if x['CEI'] > x['CEM'] else 0, axis=1
    )

    return df
