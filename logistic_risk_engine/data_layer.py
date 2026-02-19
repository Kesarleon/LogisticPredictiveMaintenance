import numpy as np
import pandas as pd

class LogisticDataLayer:
    """
    Data access layer for Logistic Risk Engine.
    Simulates route data, serving as a placeholder for a future database or API connection.
    """

    def __init__(self):
        self.routes_cache = {}

    def generate_simulated_data(self, seed=42):
        """
        Generates simulated data for routes and their segments.

        Args:
            seed (int): Random seed for reproducibility.

        Returns:
            dict: Dictionary where keys are route names and values are DataFrames containing segment data.
        """
        np.random.seed(seed)

        routes = ['Ruta Norte-Sur', 'Ruta Este-Oeste']
        data = {}

        # Starting point (Mexico City approximate)
        base_lat = 19.4326
        base_lon = -99.1332

        for route_name in routes:
            n_segments = 200
            segments = []

            # Route specific characteristics
            if route_name == 'Ruta Norte-Sur':
                # More mountainous/complex
                base_risk_bias = 0.4
                climate_impact = 0.7
                lat_dir = 1.0 # North
                lon_dir = 0.1 # Slight drift
            else:
                # Flatter, highway
                base_risk_bias = 0.2
                climate_impact = 0.3
                lat_dir = 0.1 # Slight drift
                lon_dir = 1.0 # East

            current_lat = base_lat
            current_lon = base_lon

            for i in range(n_segments):
                # Simulate segment properties
                # Factors are normalized 0-1 (low to high intensity)

                # Traffic density baseline for this segment
                base_traffic = np.clip(np.random.normal(0.5, 0.2), 0.1, 0.9)

                # Inherent accident probability (road condition)
                base_accident = np.clip(np.random.exponential(0.1) + (base_risk_bias * 0.2), 0, 1)

                # Checkpoint (Reten) probability
                # Sparse, but present
                is_reten = 1 if np.random.random() < 0.02 else 0

                # Climate vulnerability (how much this segment is affected by weather)
                climate_vulnerability = np.clip(np.random.normal(climate_impact, 0.2), 0, 1)

                distance_km = np.round(np.random.uniform(1.0, 5.0), 2)

                # Estimate coordinate change (very rough approx: 1 deg ~ 111km)
                d_lat = (distance_km / 111.0) * lat_dir
                d_lon = (distance_km / 111.0) * lon_dir

                # Add some winding to the road
                d_lat += np.random.uniform(-0.005, 0.005)
                d_lon += np.random.uniform(-0.005, 0.005)

                start_lat = current_lat
                start_lon = current_lon
                end_lat = current_lat + d_lat
                end_lon = current_lon + d_lon

                segment = {
                    'segment_id': i,
                    'route_name': route_name,
                    'distance_km': distance_km,
                    'base_traffic': base_traffic,
                    'base_accident': base_accident,
                    'is_reten': is_reten,
                    'climate_vulnerability': climate_vulnerability,
                    # Simulated "type" of road for display
                    'road_type': np.random.choice(['Autopista', 'Carretera', 'Urbano'], p=[0.6, 0.3, 0.1]),
                    'start_lat': start_lat,
                    'start_lon': start_lon,
                    'end_lat': end_lat,
                    'end_lon': end_lon
                }
                segments.append(segment)

                # Update current position for next segment
                current_lat = end_lat
                current_lon = end_lon

            df = pd.DataFrame(segments)
            data[route_name] = df

        self.routes_cache = data
        return data

    def get_route_data(self, route_name):
        """Retrieves data for a specific route."""
        if not self.routes_cache:
            self.generate_simulated_data()
        return self.routes_cache.get(route_name)
