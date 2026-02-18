import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_historical_data(n_units=30, days=90):
    """
    Genera datos históricos simulados para n_units durante los últimos days.
    """
    np.random.seed(42)

    data = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    unit_ids = [f"U-{100+i}" for i in range(n_units)]

    # Base profiles for units (some are healthier than others)
    unit_profiles = {}
    for uid in unit_ids:
        unit_profiles[uid] = {
            'base_temp': np.random.uniform(80, 95),
            'base_vibration': np.random.uniform(0.5, 2.0),
            'deterioration_rate': np.random.uniform(0.001, 0.05),
            'avg_repair_cost': np.random.uniform(15000, 50000),
            'avg_daily_income': np.random.uniform(8000, 15000)
        }

    for day in range(days + 1):
        current_date = start_date + timedelta(days=day)

        for uid in unit_ids:
            profile = unit_profiles[uid]

            # Simulate sensor readings with noise and drift
            drift = day * profile['deterioration_rate']

            temp_motor = np.random.normal(profile['base_temp'] + drift * 10, 2)
            presion_aceite = np.random.normal(40 - drift * 2, 5) # Pressure drops with wear
            vibracion_rms = np.random.normal(profile['base_vibration'] + drift, 0.2)
            voltaje_bateria = np.random.normal(24, 0.5)

            # Mileage and hours
            daily_km = np.random.uniform(300, 800)
            daily_hours = daily_km / np.random.uniform(40, 80) # Avg speed

            # ML Model Simulation
            # Probability increases with temp and vibration
            prob_falla = (temp_motor - 80) / 40 + (vibracion_rms) / 5
            prob_falla = np.clip(prob_falla, 0.01, 0.99)

            # Add some randomness to probability
            prob_falla = np.clip(prob_falla + np.random.normal(0, 0.05), 0, 1)

            score_riesgo = int(prob_falla * 100)

            # Recommendation logic
            if prob_falla > 0.7:
                recomendacion = "Programar Mantenimiento"
            elif prob_falla > 0.4:
                recomendacion = "Monitorear"
            else:
                recomendacion = "Operar Normal"

            record = {
                'unit_id': uid,
                'fecha': pd.to_datetime(current_date),
                'kilometraje': float(np.random.randint(50000, 500000)), # Placeholder, will be overwritten
                'horas_motor': float(np.random.randint(2000, 15000)),
                'temperatura_motor': round(temp_motor, 1),
                'presion_aceite': round(presion_aceite, 1),
                'vibracion_rms': round(vibracion_rms, 2),
                'voltaje_bateria': round(voltaje_bateria, 1),
                'consumo_combustible': round(np.random.uniform(2.5, 4.0), 2), # km/l
                'fallas_historicas': np.random.choice([0, 1], p=[0.95, 0.05]),
                'costo_reparacion_promedio': round(profile['avg_repair_cost'], 2),
                'ingreso_diario_promedio': round(profile['avg_daily_income'], 2),
                'probabilidad_falla': round(prob_falla, 4),
                'score_riesgo': score_riesgo,
                'recomendacion': recomendacion,
                # Costo Esperado de Falla (ML Output usually refers to potential cost of this specific failure event)
                # Here we assume it's related to the avg repair cost but could vary
                'costo_esperado_falla': round(profile['avg_repair_cost'] * 1.2, 2) # A bit higher than avg for risk calc
            }
            data.append(record)

    df = pd.DataFrame(data)

    # Fix accumulated values (mileage/hours) to be consistent
    for uid in unit_ids:
        unit_mask = df['unit_id'] == uid

        # Start with a random base
        base_km = float(np.random.randint(50000, 400000))
        base_hours = base_km / 60.0

        # Add daily accumulation
        daily_km_inc = np.random.uniform(300, 800, size=unit_mask.sum())
        daily_hours_inc = daily_km_inc / 60.0

        df.loc[unit_mask, 'kilometraje'] = base_km + np.cumsum(daily_km_inc)
        df.loc[unit_mask, 'horas_motor'] = base_hours + np.cumsum(daily_hours_inc)

    return df

# Geolocation Helpers
def get_locations_data():
    """
    Returns a list of predefined locations in Mexico (Stations and Workshops).
    """
    locations = [
        # Major Hubs (Stations + Workshops potential)
        {"id": "LOC-001", "name": "CDMX Central", "lat": 19.4326, "lon": -99.1332, "type": "Taller"},
        {"id": "LOC-002", "name": "Guadalajara Hub", "lat": 20.6597, "lon": -103.3496, "type": "Taller"},
        {"id": "LOC-003", "name": "Monterrey North", "lat": 25.6866, "lon": -100.3161, "type": "Taller"},
        {"id": "LOC-004", "name": "Veracruz Port", "lat": 19.1738, "lon": -96.1342, "type": "Estación"},
        {"id": "LOC-005", "name": "Tijuana Border", "lat": 32.5149, "lon": -117.0382, "type": "Estación"},
        {"id": "LOC-006", "name": "Cancun Logistics", "lat": 21.1619, "lon": -86.8515, "type": "Estación"},
        {"id": "LOC-007", "name": "Puebla Ind.", "lat": 19.0414, "lon": -98.2063, "type": "Estación"},
        {"id": "LOC-008", "name": "Querétaro Hub", "lat": 20.5888, "lon": -100.3899, "type": "Taller"},
        {"id": "LOC-009", "name": "León Bajío", "lat": 21.1221, "lon": -101.6664, "type": "Estación"},
        {"id": "LOC-010", "name": "Mérida South", "lat": 20.9674, "lon": -89.5926, "type": "Estación"},
        {"id": "LOC-011", "name": "San Luis Potosí", "lat": 22.1565, "lon": -100.9855, "type": "Estación"},
        {"id": "LOC-012", "name": "Hermosillo", "lat": 29.0729, "lon": -110.9559, "type": "Taller"},
    ]
    return pd.DataFrame(locations)

def assign_unit_locations(df_units):
    """
    Assigns simulated current GPS coordinates to each unique unit in the dataframe.
    """
    unique_units = df_units['unit_id'].unique()
    locations = get_locations_data()

    unit_locs = []
    for uid in unique_units:
        # Pick a random "target" location to be near
        target = locations.sample(1).iloc[0]

        # Add random noise (simulate being en-route, within ~50-100km)
        # 1 degree lat/lon is approx 111km
        lat_noise = np.random.uniform(-0.5, 0.5)
        lon_noise = np.random.uniform(-0.5, 0.5)

        unit_locs.append({
            "unit_id": uid,
            "lat": target["lat"] + lat_noise,
            "lon": target["lon"] + lon_noise
        })

    return pd.DataFrame(unit_locs)

if __name__ == "__main__":
    df = generate_historical_data()
    print(df.head())
    print(df.info())
    print(get_locations_data())
    print(assign_unit_locations(df).head())
