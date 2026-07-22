import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from . import models, database
from solenz_downloader import download_audio, download_video

router = APIRouter()

class KeyCreate(BaseModel):
    name: str

class DownloadRequest(BaseModel):
    url: str
    mode: str = "audio" # or "video"
    quality: Optional[str] = None
    prefer_ext: Optional[str] = None

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(x_api_key: str = Header(None), db: Session = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key eksik.")
    db_key = db.query(models.APIKey).filter(models.APIKey.key == x_api_key).first()
    if not db_key or not db_key.is_active:
        raise HTTPException(status_code=401, detail="Gecersiz veya pasif API Key.")
    
    # Kullanim sayisini artir
    db_key.uses += 1
    db.commit()
    return db_key

@router.post("/api/keys")
def generate_key(req: KeyCreate, db: Session = Depends(get_db)):
    new_key = f"solenz_{uuid.uuid4().hex}"
    db_item = models.APIKey(key=new_key, name=req.name)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"key": db_item.key, "name": db_item.name}

def background_download(url: str, mode: str, output_dir: str = "./downloads"):
    try:
        if mode == "audio":
            download_audio(url, output_dir=output_dir, silent=True)
        else:
            download_video(url, output_dir=output_dir, silent=True)
    except Exception as e:
        print(f"Indirme hatasi: {e}")

@router.post("/api/v1/download")
def start_download(req: DownloadRequest, background_tasks: BackgroundTasks, api_key: models.APIKey = Depends(verify_api_key)):
    # Asenkron (arka planda) indirme baslatilir
    background_tasks.add_task(background_download, req.url, req.mode)
    return {"status": "accepted", "message": "Indirme arka planda baslatildi.", "url": req.url}

@router.get("/api/stats")
def get_stats(api_key: models.APIKey = Depends(verify_api_key)):
    return {"key_name": api_key.name, "uses": api_key.uses, "created_at": api_key.created_at}
