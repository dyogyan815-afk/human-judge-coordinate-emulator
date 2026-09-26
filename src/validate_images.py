"""Image integrity, SHA-256, perceptual hash, and annotation validation."""
from __future__ import annotations
import argparse, hashlib, json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, UnidentifiedImageError

@dataclass
class ImageResult:
    image_id: str; image_path: str; valid: bool; width: int = 0; height: int = 0
    format: str = ""; sha256: str = ""; error: str = ""

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def dhash(path: Path) -> str:
    with Image.open(path).convert("L").resize((9, 8)) as im:
        pixels = list(im.getdata())
    return "".join("1" if pixels[r * 9 + c] > pixels[r * 9 + c + 1] else "0" for r in range(8) for c in range(8))

def validate_image(path: Path) -> ImageResult:
    try:
        with Image.open(path) as im:
            im.load(); w, h, fmt = im.width, im.height, im.format or "UNKNOWN"
        if w < 2 or h < 2: raise ValueError("dimensions must be at least 2x2")
        return ImageResult(path.stem, str(path), True, w, h, fmt, sha256(path))
    except (OSError, UnidentifiedImageError, ValueError) as e:
        return ImageResult(path.stem, str(path), False, error=str(e))

def validate_annotations(annotation_file: Path, manifest: dict) -> list[str]:
    errors = []
    rows = json.loads(annotation_file.read_text())
    for i, row in enumerate(rows):
        image = manifest.get(row.get("image_id"))
        if not image: errors.append(f"row {i}: unknown image_id"); continue
        for key in ("annotator_id", "x", "y"): 
            if key not in row: errors.append(f"row {i}: missing {key}")
        if not (0 <= float(row["x"]) < image["width"] and 0 <= float(row["y"]) < image["height"]): errors.append(f"row {i}: coordinate out of bounds")
        if row.get("image_hash") and row["image_hash"].replace("sha256:", "") != image["sha256"]: errors.append(f"row {i}: hash mismatch")
    return errors

def main():
    p = argparse.ArgumentParser(); p.add_argument("image_dir", type=Path); p.add_argument("--output", type=Path, default=Path("data/validation_report.json")); args = p.parse_args()
    paths = [p for p in args.image_dir.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    results = [validate_image(p) for p in paths]; seen = {}; duplicates = []
    for r in results:
        if r.sha256 in seen: duplicates.append([seen[r.sha256], r.image_id])
        else: seen[r.sha256] = r.image_id
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "total": len(results), "valid": sum(r.valid for r in results), "duplicates": duplicates, "results": [asdict(r) for r in results]}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(report, indent=2)); print(json.dumps(report, indent=2))
if __name__ == "__main__": main()
