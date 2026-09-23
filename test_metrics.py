import unittest
import pandas as pd
from metrics import summarize, rsi_wilder, clean


class MetricsTests(unittest.TestCase):
    def series(self, values):
        return pd.Series(values, index=pd.date_range("2025-01-01", periods=len(values)))

    def test_rsi_extremes_and_flat(self):
        self.assertEqual(rsi_wilder(self.series(range(1, 40))), 100)
        self.assertEqual(rsi_wilder(self.series(range(40, 1, -1))), 0)
        self.assertEqual(rsi_wilder(self.series([10] * 30)), 50)
        self.assertIsNone(rsi_wilder(self.series([10] * 14)))

    def test_known_wilder_seed(self):
        prices = [44.34,44.09,44.15,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28]
        self.assertAlmostEqual(rsi_wilder(self.series(prices)), 70.4641, places=3)

    def test_returns_and_averages(self):
        m = summarize(self.series(range(1, 251)))
        self.assertAlmostEqual(m['week'], (250 / 245 - 1) * 100)
        self.assertAlmostEqual(m['month'], (250 / 229 - 1) * 100)
        self.assertEqual(m['ma200'], 150.5)
        self.assertEqual(m['mdd'], 0)

    def test_drawdown_and_missing(self):
        m = summarize(self.series([100, 120, 90, 110]))
        self.assertEqual(m['mdd'], -25)
        self.assertIsNone(m['ma20'])
        self.assertIsNone(m['volatility'])
        self.assertIsNone(m['week'])

    def test_invalid_values(self):
        self.assertEqual(len(clean(self.series([0, float('inf'), None, -1, 2]))), 1)
        with self.assertRaises(ValueError):
            summarize(self.series([None]))


if __name__ == "__main__":
    unittest.main()
