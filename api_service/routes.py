import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from . import models, database

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
        
    master_key = os.getenv("MASTER_API_KEY", "solebz_benimsifrem_123")
    if x_api_key == master_key:
        db_key = db.query(models.APIKey).filter(models.APIKey.key == master_key).first()
        if not db_key:
            db_key = models.APIKey(key=master_key, name="Master Key")
            db.add(db_key)
            db.commit()
            db.refresh(db_key)
        db_key.uses += 1
        db.commit()
        return db_key

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

import os
import subprocess
import threading
import asyncio
import asyncio
from fastapi.responses import FileResponse
from .youtube_scraper import download_with_ytdlp

def cleanup_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Dosya temizlenemedi: {e}")

def background_download(job_id: str, url: str, mode: str, output_dir: str = "./downloads"):
    db = database.SessionLocal()
    try:
        job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
        if not job:
            return
        
        job.status = "downloading"
        db.commit()
        
        # freeytubedownloader.com uzerinden link ve metadata cekme
        try:
            os.makedirs(output_dir, exist_ok=True)
            file_ext = ".mp4" if mode != "audio" else ".mp3"
            output_path = os.path.join(output_dir, f"{job_id}{file_ext}")
            
            def progress_cb(downloaded, total):
                if total > 0:
                    pct = int((downloaded / total) * 100)
                    current_job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
                    if current_job and pct >= current_job.progress + 2:
                        current_job.progress = pct
                        db.commit()

            info = download_with_ytdlp(url, output_path, progress_callback=progress_cb, mode=mode)
            
            job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
            job.title = info.get("title", "Video")
            job.cover = info.get("thumbnail")
            job.progress = 100
            job.status = "completed"
            job.file_path = output_path
            db.commit()
            
        except Exception as e:
            print("Metadata/Link alinirken hata:", e)
            raise e

    except Exception as e:
        current_job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
        if current_job:
            current_job.status = "error"
            current_job.error_message = str(e)
            db.commit()
        print(f"Indirme hatasi: {e}")
    finally:
        db.close()

@router.post("/api/v1/download")
def start_download(req: DownloadRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), api_key: models.APIKey = Depends(verify_api_key)):
    job_id = uuid.uuid4().hex
    new_job = models.DownloadJob(id=job_id, url=req.url, status="pending", progress=0)
    db.add(new_job)
    db.commit()
    
    background_tasks.add_task(background_download, job_id, req.url, req.mode)
    return {"status": "accepted", "message": "Indirme baslatildi.", "job_id": job_id}

@router.get("/api/v1/status/{job_id}")
def get_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Islem bulunamadi.")
    
    response_data = {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "error": job.error_message
    }
    
    if job.status == "completed":
        response_data["url"] = f"https://solebz.onrender.com/api/v1/file/{job.id}"
        if job.title:
            response_data["title"] = job.title
        if job.cover:
            response_data["cover"] = job.cover
            
    return response_data

def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Dosya temizleme hatasi: {e}")

@router.get("/api/v1/file/{job_id}")
def download_file(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
    if not job or job.status != "completed" or not job.file_path:
        raise HTTPException(status_code=404, detail="Dosya hazir degil veya bulunamadi.")
    
    if not os.path.exists(job.file_path):
        raise HTTPException(status_code=404, detail="Dosya sunucudan silinmis.")
        
    filename = os.path.basename(job.file_path)
    if job.title:
        filename = f"{job.title}{os.path.splitext(job.file_path)[1]}"
        
    # Dosya gonderildikten 10 dakika sonra silinsin
    threading.Timer(600, cleanup_file, args=[job.file_path]).start()
    
    media_type = "video/mp4" if job.file_path.endswith(".mp4") else "audio/mpeg"
    from urllib.parse import quote
    encoded_filename = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    
    return FileResponse(path=job.file_path, filename=filename, media_type=media_type, headers=headers)

@router.get("/api/v1/search")
def search_media(query: str, limit: int = 10, api_key: models.APIKey = Depends(verify_api_key)):
    try:
        # Arama ozelligi freeytubedownloader scraper ile desteklenmiyor.
        return {"status": "success", "results": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/stats")
def get_stats(api_key: models.APIKey = Depends(verify_api_key)):
    return {"key_name": api_key.name, "uses": api_key.uses, "created_at": api_key.created_at}
