"""Human-vs-human agreement report."""
import argparse, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser(); p.add_argument("annotations",type=Path); p.add_argument("--out",type=Path,default=Path("reports/human_agreement.json")); a=p.parse_args(); rows=json.loads(a.annotations.read_text()); groups=defaultdict(list)
 for r in rows: groups[r["image_id"]].append((float(r["x"]),float(r["y"])))
 distances=[]; per_image={}
 for image_id, pts in groups.items():
  ds=[math.hypot(x1-x2,y1-y2) for i,(x1,y1) in enumerate(pts) for x2,y2 in pts[i+1:]]
  if ds: distances.extend(ds); per_image[image_id]={"n":len(pts),"mean":float(np.mean(ds)),"median":float(np.median(ds)),"p95":float(np.percentile(ds,95))}
 def pct(n): return 100*sum(d<=n for d in distances)/len(distances) if distances else 0
 report={"images":len(groups),"pairwise_distances":len(distances),"mean":float(np.mean(distances)) if distances else None,"median":float(np.median(distances)) if distances else None,"p90":float(np.percentile(distances,90)) if distances else None,"p95":float(np.percentile(distances,95)) if distances else None,"within_px":{str(n):pct(n) for n in (1,2,5,10,20)},"per_image":per_image}
 a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
