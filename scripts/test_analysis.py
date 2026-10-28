import tempfile
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from analyze import backtest, statistics, load

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.x = pd.DataFrame(np.random.default_rng(42).normal(.003,.025,(100,3)),
                              index=pd.period_range('2000-01', periods=100, freq='M'), columns=['CAR','VAL','M1M'])
    def test_future_invariance_and_exposure(self):
        r,w = backtest(self.x)
        changed=self.x.copy(); changed.iloc[80:] += .1
        r2,w2=backtest(changed)
        np.testing.assert_allclose(r.iloc[:44],r2.iloc[:44])
        pd.testing.assert_frame_equal(w[w.date < '2006-09'], w2[w2.date < '2006-09'])
        g=w.groupby(['date','method'])
        np.testing.assert_allclose(g.base_weight.sum(),1)
        self.assertTrue((g.exposure.sum() <= 2+1e-12).all())
    def test_metrics(self):
        s=statistics(np.array([-.1,.1]))
        self.assertAlmostEqual(s['max_drawdown'],.1)
        self.assertAlmostEqual(s['terminal_excess_wealth'],.99)
        self.assertAlmostEqual(s['ann_arithmetic_mean'],0)
        self.assertAlmostEqual(s['ann_vol'],np.sqrt(.02)*np.sqrt(12))
        self.assertIsNone(statistics(np.zeros(3))['sharpe_arithmetic'])
    def test_bad_data_and_units(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x.csv'
            a=self.x.copy();a.index=a.index.to_timestamp();a.index.name='date';a.to_csv(p)
            x=load(p,'All',list(self.x.columns),'decimal')
            np.testing.assert_allclose(x,self.x)
            a=a*100;a.to_csv(p)
            np.testing.assert_allclose(load(p,'All',list(self.x.columns),'percent'),self.x)
            a.iloc[0,0]=np.nan;a.to_csv(p)
            with self.assertRaises(ValueError):load(p,'All',list(self.x.columns),'percent')
            a=self.x.iloc[[0,2,3]].copy();a.index=a.index.to_timestamp();a.index.name='date';a.to_csv(p)
            with self.assertRaises(ValueError):load(p,'All',list(self.x.columns),'decimal')

if __name__ == '__main__':unittest.main()
