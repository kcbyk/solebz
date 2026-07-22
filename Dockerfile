FROM python:3.10-slim

# Gerekli sistem paketlerini ve Tailscale'i kur (FFmpeg destegi ile)
RUN apt-get update && apt-get install -y curl ffmpeg
RUN curl -fsSL https://tailscale.com/install.sh | sh

# Proje dosyalarini kopyala
WORKDIR /app
COPY . /app

# Python bagimliliklarini kur (yt-dlp yerine playwright ekliyoruz)
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic curl_cffi requests pysocks playwright playwright-stealth

# Playwright tarayicisini ve bagimliliklarini kur
RUN playwright install --with-deps chromium
# Baslatma scriptine calisma izni ver
RUN chmod +x /app/start.sh

# Render'in kullanacagi port
EXPOSE 8000

# Konteyner basladiginda start.sh calissin
CMD ["/app/start.sh"]
