"""Generate SYNTHETIC examples; no market data is downloaded or reproduced."""
from pathlib import Path
import numpy as np
import pandas as pd

def generate(destination=None):
    root=Path(destination) if destination else Path(__file__).resolve().parent
    root.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(52)
    excess=pd.DataFrame(rng.normal(.004,.025,(180,4)),columns=["Quality","Trend","Defensive","Value"])
    dates=pd.date_range("2000-01-01",periods=len(excess),freq="MS").strftime("%Y-%m-%d")
    excess.insert(0,"date",dates)
    excess.to_csv(root/"synthetic_excess.csv",index=False,float_format="%.12f")
    total=excess.copy()
    for c in ["Quality","Trend","Defensive","Value"]:total[c]+=.001
    total["cash"]=.001
    total.to_csv(root/"synthetic_total.csv",index=False,float_format="%.12f")
    print("SYNTHETIC examples written to",root)
if __name__=="__main__":generate()
