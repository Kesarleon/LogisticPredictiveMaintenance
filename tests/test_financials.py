import unittest
import pandas as pd
from src.data.financials import calculate_cei, calculate_cem, get_recommendation, enrich_data_with_financials

class TestFinancials(unittest.TestCase):
    def test_calculate_cei(self):
        # Prob 0.5, Cost 10000, Income 1000, Days 3
        # Total Fail Cost = 10000 + (1000 * 3) = 13000
        # CEI = 0.5 * 13000 = 6500
        self.assertEqual(calculate_cei(0.5, 10000, 1000, 3), 6500)

    def test_calculate_cem(self):
        self.assertEqual(calculate_cem(5000, 2000), 7000)

    def test_get_recommendation(self):
        # CEI > CEM -> Programar Mantenimiento
        self.assertEqual(get_recommendation(10000, 5000, 0.5), "Programar Mantenimiento")
        # CEI < CEM, but prob > 0.4 -> Monitorear
        self.assertEqual(get_recommendation(2000, 5000, 0.5), "Monitorear")
        # CEI < CEM, prob < 0.4 -> Operar Normal
        self.assertEqual(get_recommendation(2000, 5000, 0.1), "Operar Normal")

    def test_enrich_data(self):
        df = pd.DataFrame([{
            'probabilidad_falla': 0.8,
            'costo_reparacion_promedio': 10000,
            'ingreso_diario_promedio': 1000
        }])
        enriched = enrich_data_with_financials(df, 5000, 2000)
        self.assertIn('CEI', enriched.columns)
        self.assertIn('CEM', enriched.columns)
        # Check calculation
        # CEM = 7000
        # CEI = 0.8 * (10000 + 3000) = 0.8 * 13000 = 10400
        self.assertEqual(enriched.iloc[0]['CEI'], 10400)
        self.assertEqual(enriched.iloc[0]['CEM'], 7000)
        self.assertEqual(enriched.iloc[0]['Accion_Sugerida'], "Programar Mantenimiento")

if __name__ == '__main__':
    unittest.main()
