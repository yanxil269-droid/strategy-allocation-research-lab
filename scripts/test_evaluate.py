import unittest
import numpy as np
import pandas as pd
from evaluate import activity_costs,exposure_summary,period_summary
class EvaluationTests(unittest.TestCase):
 def test_cost_hand_calculation(self):
  idx=pd.period_range('2020-01',periods=2,freq='M');r=pd.DataFrame({'M':[.01,.02]},index=idx)
  w=pd.DataFrame([{'date':str(d),'method':'M','factor':f,'exposure':v} for d,vs in zip(idx,[[.6,.4],[.5,.5]]) for f,v in zip(['A','B'],vs)])
  adjusted,a=activity_costs(r,w,10)
  np.testing.assert_allclose(a.activity_proxy,[1,.2]);np.testing.assert_allclose(adjusted.M,[.009,.0198])
  z,_=activity_costs(r,w,0);pd.testing.assert_frame_equal(z,r)
  self.assertAlmostEqual(exposure_summary(w).loc['M','max_gross_exposure'],1)
 def test_short_period(self):
  r=pd.DataFrame({"M":[.01]*6},index=pd.period_range("2000-01",periods=6,freq="M"))
  d=period_summary(r);self.assertTrue(d.empty);self.assertIn("method",d.columns)
 def test_period_partition(self):
  idx=pd.period_range('1999-01',periods=84,freq='M');r=pd.DataFrame({'M':np.random.default_rng(3).normal(0,.01,84)},index=idx)
  d=period_summary(r);self.assertEqual(d.months.sum(),84);self.assertEqual(list(d.months),[12,60,12])
if __name__=='__main__':unittest.main()
