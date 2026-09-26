"""Minimal research API. It exposes prediction only; no external submission or gameplay."""
import io, os
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

app=FastAPI(title="Human Judge Coordinate Emulator", version=os.getenv("MODEL_VERSION","0.1.0"))
class Prediction(BaseModel):
    x: float; y: float; confidence: float; uncertainty_px: float; model_version: str

def center_prediction(im: Image.Image) -> Prediction:
    w,h=im.size
    return Prediction(x=round((w-1)/2,2),y=round((h-1)/2,2),confidence=0.0,uncertainty_px=0.0,model_version=app.version)
@app.get("/health")
def health(): return {"status":"ok","model_version":app.version}
@app.get("/model")
def model(): return {"model":"center_baseline","model_version":app.version}
@app.post("/predict",response_model=Prediction)
async def predict(image: UploadFile=File(...)):
    if image.content_type not in {"image/jpeg","image/png","image/webp"}: raise HTTPException(415,"Unsupported image type")
    data=await image.read()
    try: im=Image.open(io.BytesIO(data)); im.load()
    except Exception as e: raise HTTPException(400,f"Invalid image: {e}")
    return center_prediction(im)
