import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from . import models, database
from solenz_downloader import download_audio, download_video, search_youtube

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
from fastapi.responses import FileResponse
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.core.downloader import SolenzDownloader
from solenz_downloader.extractors.youtube import YouTubeExtractor

def background_download(job_id: str, url: str, mode: str, output_dir: str = "./downloads"):
    db = database.SessionLocal()
    try:
        job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
        if not job:
            return
        
        job.status = "downloading"
        db.commit()
        
        # Meta verileri (Baslik, Kapak Fotografi) al
        try:
            client = SolenzClient()
            ext = YouTubeExtractor(client)
            info = ext.extract(url)
            job.title = info.title
            job.cover = info.thumbnail
            db.commit()
        except Exception as e:
            print("Metadata alinirken hata:", e)

        # Update progress via callback
        def progress_callback(downloaded: int, total: int | None, speed: float):
            if total and total > 0:
                pct = int((downloaded / total) * 100)
                # Only update DB if progress increases by at least 2% to avoid DB spam
                current_job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
                if current_job and pct >= current_job.progress + 2:
                    current_job.progress = pct
                    db.commit()

        os.makedirs(output_dir, exist_ok=True)
        
        if mode == "audio":
            file_path = download_audio(url, output_dir=output_dir, on_progress=progress_callback, silent=True, max_concurrent=16)
            if file_path and not file_path.endswith(".mp3"):
                mp3_path = os.path.splitext(file_path)[0] + ".mp3"
                try:
                    subprocess.run(["ffmpeg", "-y", "-i", file_path, "-q:a", "0", "-map", "a", mp3_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    file_path = mp3_path
                except Exception as e:
                    print("FFmpeg mp3 donusturme hatasi:", e)
        else:
            with SolenzClient() as client:
                ext = YouTubeExtractor(client)
                info = ext.extract(url)
                
                # Sadece MP4 (H264) olan en iyi videoyu sec
                video_stream = info.best_video(prefer_ext="mp4")
                if not video_stream:
                    raise Exception("Uygun MP4 video akisi bulunamadi.")
                
                if video_stream.has_audio:
                    # Video zaten ses iceriyorsa direkt indir
                    downloader = SolenzDownloader(client, on_progress=progress_callback, max_concurrent=16)
                    file_path = downloader.download_stream(video_stream, output_dir=output_dir, filename=f"v_{job_id}.mp4", referer=info.url)
                else:
                    # Ses yoksa, sesi ayri indir ve copy ile birlestir
                    audio_stream = info.best_audio(prefer_ext="m4a")
                    if not audio_stream:
                        raise Exception("Uygun ses akisi bulunamadi.")
                        
                    downloader_video = SolenzDownloader(client, on_progress=progress_callback, max_concurrent=16)
                    v_path = downloader_video.download_stream(video_stream, output_dir=output_dir, filename=f"v_{job_id}.mp4", referer=info.url)
                    
                    downloader_audio = SolenzDownloader(client, on_progress=None, max_concurrent=16)
                    a_path = downloader_audio.download_stream(audio_stream, output_dir=output_dir, filename=f"a_{job_id}.m4a", referer=info.url)
                    
                    final_path = os.path.join(output_dir, f"{job_id}.mp4")
                    
                    try:
                        # -c copy kullanarak SIFIR CPU ve SIFIR kalite kaybi ile aninda birlestirme
                        subprocess.run([
                            "ffmpeg", "-y", "-i", v_path, "-i", a_path,
                            "-c:v", "copy", "-c:a", "copy", final_path
                        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        if os.path.exists(v_path): os.remove(v_path)
                        if os.path.exists(a_path): os.remove(a_path)
                        file_path = final_path
                    except Exception as e:
                        print("FFmpeg birlestirme hatasi:", e)
                        file_path = v_path  # Birlestirme cokuyorsa en azindan sessiz videoyu ver
            
        current_job = db.query(models.DownloadJob).filter(models.DownloadJob.id == job_id).first()
        if current_job:
            current_job.status = "completed"
            current_job.progress = 100
            current_job.file_path = file_path
            db.commit()

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
    
    # Dosya gonderildikten SONRA degil, 10 dakika sonra silinmesi icin zamanlayici ekliyoruz.
    # Bu sayede tarayici HEAD (pre-flight) istegi atarsa dosya erkenden silinmez.
    threading.Timer(600, cleanup_file, args=[job.file_path]).start()
    
    media_type = "video/mp4" if filename.endswith(".mp4") else "audio/mpeg" if filename.endswith(".mp3") else "application/octet-stream"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    
    return FileResponse(path=job.file_path, filename=filename, media_type=media_type, headers=headers)

@router.get("/api/v1/search")
def search_media(query: str, limit: int = 10, api_key: models.APIKey = Depends(verify_api_key)):
    try:
        results = search_youtube(query, limit=limit)
        return {"status": "success", "results": [r.__dict__ for r in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/stats")
def get_stats(api_key: models.APIKey = Depends(verify_api_key)):
    return {"key_name": api_key.name, "uses": api_key.uses, "created_at": api_key.created_at}
