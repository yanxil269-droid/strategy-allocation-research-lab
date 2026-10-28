import unittest
import numpy as np
import pandas as pd
from pricing import fit_pricing,hac_mean
class PricingTests(unittest.TestCase):
 def test_known_prices_and_permutation(self):
  rng=np.random.default_rng(6);T=240;idx=pd.period_range('2000-01',periods=T,freq='M')
  f=rng.normal(size=(T,2))*.02;f=f-f.mean(axis=0)+[.002,.004]
  b=rng.normal(size=(30,2));r=f@b.T+.001
  F=pd.DataFrame(f,index=idx,columns=['DOL','CAR']);R=pd.DataFrame(r,index=idx)
  risk,*_=fit_pricing(R,F,4)
  np.testing.assert_allclose(risk.lambda_monthly_decimal,[.001,.002,.004],atol=1e-12)
  reversed_risk,*_=fit_pricing(R.iloc[:,::-1],F,4)
  np.testing.assert_allclose(risk.lambda_monthly_decimal,reversed_risk.lambda_monthly_decimal,atol=1e-12)
 def test_three_factor_recovery(self):
  rng=np.random.default_rng(17);T=180;idx=pd.period_range('2000-01',periods=T,freq='M')
  f=rng.normal(size=(T,3))*.02;f=f-f.mean(axis=0)+[.002,.004,.01]
  b=rng.normal(size=(30,3));r=f@b.T+.001
  F=pd.DataFrame(f,index=idx,columns=['DOL','CAR','dlnGRV']);R=pd.DataFrame(r,index=idx)
  risk,*_=fit_pricing(R,F,4)
  np.testing.assert_allclose(risk.lambda_monthly_decimal,[.001,.002,.004,.01],atol=1e-12)
 def test_hac_zero_lag(self):
  x=np.array([[1.,3.],[2.,1.],[3.,2.]])
  u=x-x.mean(axis=0)
  np.testing.assert_allclose(hac_mean(x,0),u.T@u/9)
 def test_rank_rejection(self):
  idx=pd.period_range('2000-01',periods=20,freq='M')
  with self.assertRaises(ValueError):fit_pricing(pd.DataFrame(np.ones((20,30)),index=idx),pd.DataFrame(np.ones((20,2)),index=idx),2)
if __name__=='__main__':unittest.main()
