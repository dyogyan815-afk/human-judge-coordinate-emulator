"""Create a synthetic, clearly-labelled pilot fixture for pipeline testing.
Real BOTB collection requires permitted source images and independent human annotators.
"""
import argparse, json, random
from pathlib import Path
from PIL import Image, ImageDraw

def main():
    p=argparse.ArgumentParser(); p.add_argument("--images", type=int, default=20); p.add_argument("--annotators", type=int, default=3); p.add_argument("--out", type=Path, default=Path("data/pilot_fixture")); a=p.parse_args()
    random.seed(42); image_dir=a.out/"images"; image_dir.mkdir(parents=True, exist_ok=True); labels=[]
    for i in range(a.images):
        w,h=640,360; im=Image.new("RGB",(w,h),(35+i%5*10,90,130)); d=ImageDraw.Draw(im)
        d.rectangle((40,40,w-40,h-40), outline="white", width=3); d.ellipse((random.randint(100,540),random.randint(70,290),random.randint(100,540)+12,random.randint(70,290)+12), fill="orange")
        path=image_dir/f"img_{i:06d}.png"; im.save(path)
        # Fixture labels are not human labels; they only test ingestion and metrics.
        for j in range(a.annotators): labels.append({"image_id":path.stem,"annotator_id":f"fixture_{j:03d}","x":w/2+random.gauss(0,8),"y":h/2+random.gauss(0,8),"width":w,"height":h,"synthetic":True})
    (a.out/"annotations.json").write_text(json.dumps(labels,indent=2)); print(f"Wrote {a.images} images and {len(labels)} synthetic labels to {a.out}")
if __name__ == "__main__": main()
