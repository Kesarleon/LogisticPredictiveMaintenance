import pandas as pd
import numpy as np
from .data_layer import LogisticDataLayer

class LogisticRiskEngine:
    """
    Core engine for calculating logistic risks.
    Orchestrates data retrieval, preprocessing, and risk scoring.
    """

    def __init__(self):
        self.data_layer = LogisticDataLayer()
        self.current_data = {}
        # Default weights
        self.weights = {
            "w_traffic": 0.4,
            "w_accident": 0.3,
            "w_reten": 0.1,
            "w_climate": 0.2
        }
        # Risk thresholds
        self.thresholds = {
            "low": 0.3,
            "medium": 0.6
        }

    def generate_simulated_data(self, seed=42):
        """Generates or refreshes the simulated data via the Data Layer."""
        self.current_data = self.data_layer.generate_simulated_data(seed)
        return self.current_data

    def preprocess_data(self):
        """
        Prepares data for analysis.
        In a real scenario, this would handle missing values, normalization, or feature engineering.
        """
        if not self.current_data:
            self.generate_simulated_data()
        # Simulation data is already clean, but we ensure structure here.
        return True

    def set_weights(self, w_traffic, w_accident, w_reten, w_climate):
        """Updates the weights for the scoring model."""
        self.weights = {
            "w_traffic": w_traffic,
            "w_accident": w_accident,
            "w_reten": w_reten,
            "w_climate": w_climate
        }

    def _get_time_modifiers(self, hour):
        """Returns risk modifiers based on the hour of the day."""
        # Traffic peaks
        traffic_mod = 1.0
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            traffic_mod = 1.8
        elif 10 <= hour <= 16:
            traffic_mod = 1.2
        elif hour < 6:
            traffic_mod = 0.5

        # Accident risk higher at night
        accident_mod = 1.0
        if hour >= 22 or hour <= 5:
            accident_mod = 1.6

        # Climate visibility issues (fog/darkness)
        climate_mod = 1.0
        if hour <= 6 or hour >= 20:
            climate_mod = 1.3

        return traffic_mod, accident_mod, climate_mod

    def calculate_segment_risk(self, segment, hour):
        """
        Calculates the risk score for a single segment at a given hour.
        Implements the formula: Risk Score = Sum(w_i * factor_i)
        """
        # Extract base factors
        base_traffic = segment['base_traffic']
        base_accident = segment['base_accident']
        is_reten = segment['is_reten']
        climate_vuln = segment['climate_vulnerability']

        # Apply time modifiers
        t_mod, a_mod, c_mod = self._get_time_modifiers(hour)

        # Calculate individual component risks (clamped to sensible ranges)
        traffic_risk = np.clip(base_traffic * t_mod, 0, 1.0)
        accident_risk = np.clip(base_accident * a_mod, 0, 1.0)
        reten_risk = float(is_reten) # Binary 0 or 1 usually
        climate_risk = np.clip(climate_vuln * c_mod, 0, 1.0)

        # Weighted sum
        w = self.weights
        raw_score = (w['w_traffic'] * traffic_risk +
                     w['w_accident'] * accident_risk +
                     w['w_reten'] * reten_risk +
                     w['w_climate'] * climate_risk)

        # Robust normalization: Divide by sum of weights
        weight_sum = sum(w.values())
        normalized_score = raw_score / weight_sum if weight_sum > 0 else 0
        normalized_score = np.clip(normalized_score, 0, 1)

        return {
            'risk_score': normalized_score,
            'traffic_risk': traffic_risk,
            'accident_risk': accident_risk,
            'reten_risk': reten_risk,
            'climate_risk': climate_risk,
            'risk_level': self.classify_risk(normalized_score)
        }

    def classify_risk(self, score):
        """Dynamic classification of risk score."""
        if score < self.thresholds['low']:
            return "Bajo"
        elif score < self.thresholds['medium']:
            return "Medio"
        else:
            return "Alto"

    def aggregate_route_risk(self, route_name, hour):
        """
        Aggregates risk across an entire route for a specific hour.
        Returns detailed stats and a composite index.
        """
        self.preprocess_data()

        if route_name not in self.current_data:
            raise ValueError(f"Route {route_name} not found.")

        df = self.current_data[route_name].copy()

        # Apply calculation to all segments
        # Using list comprehension for clarity and ease of debugging individual segment logic
        results = [self.calculate_segment_risk(row, hour) for _, row in df.iterrows()]
        risk_df = pd.DataFrame(results)

        # Combine original data with risk calculations
        df_result = pd.concat([df.reset_index(drop=True), risk_df], axis=1)

        # Aggregation metrics
        avg_risk = df_result['risk_score'].mean()
        max_risk = df_result['risk_score'].max()

        # Composite Index: Penalize max risk segments heavily (bottlenecks)
        # 60% average, 40% worst case segment
        composite_index = (avg_risk * 0.6) + (max_risk * 0.4)

        estimated_speed = 80 * (1 - avg_risk) # Simple speed estimation model

        return {
            'route_name': route_name,
            'hour': hour,
            'composite_risk_index': composite_index,
            'avg_risk': avg_risk,
            'max_segment_risk': max_risk,
            'risk_level': self.classify_risk(composite_index),
            'estimated_speed_kmh': estimated_speed,
            'details': df_result
        }

    def find_optimal_departure(self, route_name):
        """
        Simulates the route across 24 hours to find the window with lowest risk.
        """
        results = []
        for h in range(24):
            res = self.aggregate_route_risk(route_name, h)
            results.append({
                'hour': h,
                'composite_risk_index': res['composite_risk_index'],
                'avg_risk': res['avg_risk'],
                'max_segment_risk': res['max_segment_risk'],
                'risk_level': res['risk_level']
            })

        df_res = pd.DataFrame(results)
        best_row = df_res.loc[df_res['composite_risk_index'].idxmin()]

        return {
            'best_hour': int(best_row['hour']),
            'min_risk_index': best_row['composite_risk_index'],
            'analysis': df_res
        }

    # --- Scalability Placeholders ---

    def train_ml_model(self):
        """Placeholder: Integrate XGBoost training here."""
        pass

    def save_results(self, results):
        """Placeholder: Persist to database."""
        pass
