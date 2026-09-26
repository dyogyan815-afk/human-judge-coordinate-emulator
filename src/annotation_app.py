"""Human annotation UI for permitted research images."""
import hashlib, io, json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
from PIL import Image

DB = os.getenv("ANNOTATION_DB", "data/annotations.sqlite3")
IMAGE_ROOT = Path(os.getenv("IMAGE_ROOT", "data/raw"))
INTERFACE_VERSION = "annotation-ui-1.0.0"

def db():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS annotations (
      annotation_id INTEGER PRIMARY KEY AUTOINCREMENT, image_id TEXT NOT NULL,
      image_hash TEXT NOT NULL, annotator_id TEXT NOT NULL, x REAL NOT NULL,
      y REAL NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
      timestamp TEXT NOT NULL, interface_version TEXT NOT NULL,
      UNIQUE(image_id, annotator_id))""")
    c.commit(); return c

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return f"sha256:{h.hexdigest()}"

def image_files():
    return sorted(p for p in IMAGE_ROOT.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})

def main():
    st.set_page_config(page_title="Human coordinate annotation", layout="wide")
    st.title("Human Coordinate Annotation")
    st.caption("Independent research annotation. Do not use this UI to submit or automate entries.")
    files = image_files()
    if not files: st.error(f"No images found in {IMAGE_ROOT}"); return
    annotator = st.text_input("Annotator ID", key="annotator")
    if not annotator.strip(): st.warning("Enter an annotator ID to begin."); return
    labels = [p.stem for p in files]
    selected = st.selectbox("Image", labels, key="image_id")
    path = files[labels.index(selected)]
    img = Image.open(path); width, height = img.size
    st.write(f"Image: `{selected}` · source dimensions: `{width} × {height}`")
    # Streamlit's image click component is intentionally avoided: the native uploader/display
    # keeps the coordinate transform explicit. Use the numeric fields for exact reproducibility.
    st.image(img, use_container_width=True)
    x = st.number_input("X (source pixel coordinate)", min_value=0.0, max_value=float(width - 1), value=float(width / 2), step=1.0)
    y = st.number_input("Y (source pixel coordinate)", min_value=0.0, max_value=float(height - 1), value=float(height / 2), step=1.0)
    if st.button("Confirm annotation", type="primary"):
        c = db(); digest = sha256(path); now = datetime.now(timezone.utc).isoformat()
        try:
            c.execute("INSERT INTO annotations(image_id,image_hash,annotator_id,x,y,width,height,timestamp,interface_version) VALUES(?,?,?,?,?,?,?,?,?)",
                      (selected,digest,annotator.strip(),x,y,width,height,now,INTERFACE_VERSION)); c.commit()
            st.success(f"Saved ({x:.0f}, {y:.0f}) for {selected}.")
        except sqlite3.IntegrityError: st.error("This annotator already submitted this image.")
    if st.button("Export annotations"):
        rows = db().execute("SELECT * FROM annotations ORDER BY annotation_id").fetchall()
        st.download_button("Download JSON", json.dumps([dict(zip([d[0] for d in db().execute('PRAGMA table_info(annotations)').fetchall()], r)) for r in rows], indent=2), "annotations.json", "application/json")

if __name__ == "__main__": main()
