FROM python:3.10-slim

# Gerekli sistem paketlerini ve Tailscale'i kur
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://tailscale.com/install.sh | sh

# Proje dosyalarini kopyala
WORKDIR /app
COPY . /app

# Python bagimliliklarini kur
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic curl_cffi requests

# Baslatma scriptine calisma izni ver
RUN chmod +x /app/start.sh

# Render'in kullanacagi port
EXPOSE 8000

# Konteyner basladiginda start.sh calissin
CMD ["/app/start.sh"]
