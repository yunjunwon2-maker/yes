import json
import tempfile
import unittest
from pathlib import Path
from portfolio import read_portfolio, validate_portfolio, calculate, allocation_status


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.h = {'GOOGL':dict(shares=2, average_price=80, target_weight=50),
                  'NEE':dict(shares=1, average_price=120, target_weight=50)}
        self.q = {'GOOGL':dict(price=110, previous=100, date='2026-09-23', previous_date='2026-09-22', daily_valid=True),
                  'NEE':dict(price=100, previous=105, date='2026-09-23', previous_date='2026-09-22', daily_valid=True)}

    def test_default_json(self):
        h = read_portfolio()
        self.assertEqual(set(h), {'GOOGL','NEE','SPY','SCHD','SGOV'})
        self.assertEqual(sum(x['target_weight'] for x in h.values()), 100)

    def test_accounting_fx_and_contribution(self):
        rows, t = calculate(self.h, self.q, 1300)
        self.assertEqual(rows[0]['value'], 220)
        self.assertEqual(rows[0]['cost'], 160)
        self.assertEqual(rows[0]['pnl'], 60)
        self.assertEqual(rows[0]['return_pct'], 37.5)
        self.assertEqual(t['value'], 320)
        self.assertEqual(t['cost'], 280)
        self.assertEqual(t['pnl'], 40)
        self.assertAlmostEqual(t['return_pct'], 40/280*100)
        self.assertEqual(t['day'], 15)
        self.assertAlmostEqual(t['day_return'], 15/305*100)
        self.assertAlmostEqual(sum(r['contribution'] for r in rows), t['day_return'])
        self.assertEqual(rows[0]['weight'], 68.75)
        self.assertEqual(rows[0]['difference'], 18.75)
        self.assertEqual(t['drift'], 18.75)
        self.assertEqual(t['value_krw'], 416000)
        self.assertEqual(rows[0]['pnl_krw'], 78000)

    def test_partial_no_false_totals(self):
        del self.q['NEE']
        rows, t = calculate(self.h, self.q)
        self.assertIsNone(t['value'])
        self.assertIsNone(t['drift'])
        self.assertIsNone(t['day'])
        self.assertEqual(t['cost'], 280)
        self.assertEqual(t['subtotal'], 220)
        self.assertIsNone(rows[0]['weight'])

    def test_no_holdings(self):
        for h in self.h.values():
            h.update(shares=0, average_price=0)
        rows, t = calculate(self.h, {})
        self.assertEqual(t['value'], 0)
        self.assertIsNone(t['return_pct'])
        self.assertIsNone(t['drift'])

    def test_different_dates_and_stale(self):
        self.q['NEE']['date'] = '2026-09-22'
        _, t = calculate(self.h, self.q)
        self.assertIsNone(t['day'])
        self.q['NEE']['date'] = '2026-09-23'
        self.q['NEE']['daily_valid'] = False
        _, t = calculate(self.h, self.q)
        self.assertIsNone(t['day'])
        self.assertEqual(t['value'], 320)

    def test_target_sum_and_fx_missing(self):
        self.h['NEE']['target_weight'] = 20
        _, t = calculate(self.h, self.q, float('nan'))
        self.assertIsNone(t['drift'])
        self.assertIsNone(t['value_krw'])

    def test_validation(self):
        for bad in [-1, float('nan'), float('inf'), True, '2']:
            self.h['GOOGL']['shares'] = bad
            with self.assertRaises(ValueError):
                validate_portfolio(self.h)
        with self.assertRaises(ValueError):
            validate_portfolio({'BAD<script>': {}})

    def test_thresholds(self):
        for value, expected in [(2,'Balanced'),(-2,'Balanced'),(2.01,'Watch'),(-5,'Watch'),(5.01,'Large Deviation'),(None,'Unavailable')]:
            self.assertEqual(allocation_status(value), expected)


if __name__ == '__main__':
    unittest.main()
