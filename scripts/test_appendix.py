import unittest
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from appendix import allocate,max_return,run
class AppendixTests(unittest.TestCase):
 def setUp(self):self.a=np.random.default_rng(21).normal(.004,.02,(100,5))
 def test_rules(self):
  e,r,c=allocate(self.a)
  mu=self.a.mean(0)*12;sd=self.a.std(0,ddof=1)*np.sqrt(12);sr=mu/sd
  np.testing.assert_allclose(r['MEAN'],mu/mu.sum());np.testing.assert_allclose(r['SR'],sr/sr.sum())
  top=np.argsort(-sr)[:3];self.assertEqual(set(np.flatnonzero(r['TOP3'])),set(top))
  for w in e.values():self.assertAlmostEqual(np.sqrt(w@c@w),.1,places=11)
  self.assertAlmostEqual(e['MaxRet'].sum(),1,places=11)
 def test_maxret_optimality(self):
  mu=np.array([.03,.07,.10]);c=np.diag([.02,.03,.04]);w=max_return(mu,c,.2)
  fit=minimize(lambda z:-mu@z,np.ones(3)/3,constraints=[{'type':'eq','fun':lambda z:z.sum()-1},{'type':'eq','fun':lambda z:z@c@z-.04}],method='SLSQP',options={'ftol':1e-13,'maxiter':1000})
  self.assertTrue(fit.success);np.testing.assert_allclose(mu@w,mu@fit.x,atol=1e-8)
  with self.assertRaises(ValueError):max_return(mu,c,.001)
 def test_three_factor_duplicate_and_future(self):
  x=pd.DataFrame(self.a[:,:3],index=pd.period_range('2000-01',periods=100,freq='M'))
  r,_=run(x);np.testing.assert_allclose(r.SR,r.TOP3)
  y=x.copy();y.iloc[80:]+=.03;s,_=run(y)
  np.testing.assert_allclose(r.iloc[:44],s.iloc[:44])
 def test_negative_means_not_clipped(self):
  a=self.a.copy();a[:,0]-=.03
  _,r,_=allocate(a);mu=a.mean(0)*12
  np.testing.assert_allclose(r['MEAN'],mu/mu.sum());self.assertTrue((r['MEAN']<0).any())
if __name__=='__main__':unittest.main()
