import subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
class ReleaseTests(unittest.TestCase):
 def invoke(self,args):
  return subprocess.run([sys.executable,str(ROOT/'run_report.py'),*args],capture_output=True,text=True)
 def test_demo_and_total_equivalence(self):
  with tempfile.TemporaryDirectory() as t:
   results=[]
   for kind in ['excess','total']:
    out=Path(t)/kind
    args=[str(ROOT/f'examples/synthetic_{kind}.csv'),'--strategies','Quality','Trend','Defensive','Value','--unit','decimal','--return-type',kind,'--fee-status','unknown','--out',str(out)]
    if kind=='total':args+=['--rf-column','cash']
    p=self.invoke(args);self.assertEqual(p.returncode,0,p.stderr)
    self.assertTrue((out/'report.html').is_file());self.assertIn('data:image/png;base64,',(out/'report.html').read_text())
    self.assertEqual(len(pd.read_csv(out/'returns.csv')),144)
    results.append(pd.read_csv(out/'returns.csv').drop(columns='date'))
   np.testing.assert_allclose(results[0],results[1],atol=1e-10)
 def test_total_without_cash_fails(self):
  p=self.invoke([str(ROOT/'examples/synthetic_total.csv'),'--strategies','Quality','Trend','Defensive','Value','--unit','decimal','--return-type','total','--fee-status','unknown','--out','unused-output'])
  self.assertEqual(p.returncode,2);self.assertIn('risk-free',p.stderr)
 def test_nan_target_rejected(self):
  from appendix import run
  with self.assertRaises(ValueError):run(pd.DataFrame(np.ones((50,3))),target=float('nan'))
 def test_cli_version(self):
  p=self.invoke(['--version']);self.assertEqual(p.returncode,0);self.assertIn('0.1.0',p.stdout)
if __name__=='__main__':unittest.main()
