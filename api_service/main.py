import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from . import models, database, routes

# Veritabani tablolarini olustur
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Solenz API", description="SaaS Media Downloader API")

# CORS ayarlari (Herhangi bir domainden gelen isteklere acik)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router'i ekle
app.include_router(routes.router)

# Statik dosyalari sun (Web sitesi)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
