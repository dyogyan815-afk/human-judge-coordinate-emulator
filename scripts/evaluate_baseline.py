"""Resolution-aware baseline predictors and evaluation."""
import argparse, json, math
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser(); p.add_argument("annotations",type=Path); p.add_argument("--out",type=Path,default=Path("reports/baseline_metrics.json")); a=p.parse_args(); rows=json.loads(a.annotations.read_text())
 errors=[]
 for r in rows:
  # Center baseline. Production training should use image-disjoint splits.
  errors.append(math.hypot(float(r["x"])-float(r["width"])/2,float(r["y"])-float(r["height"])/2))
 report={"model":"center_baseline","n":len(errors),"mean_euclidean":float(np.mean(errors)) if errors else None,"median_euclidean":float(np.median(errors)) if errors else None,"p95_euclidean":float(np.percentile(errors,95)) if errors else None}
 a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
