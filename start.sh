#!/bin/sh

# 1. Arka planda Tailscale servisini (daemon) baslat
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
sleep 3

# 2. Tailscale agina katil ve Android TV'yi Cikis Dugumu (Exit Node) olarak ayarla
# Not: TAILSCALE_AUTHKEY ve EXIT_NODE_IP ortam degiskenleri (Environment Variables) Render uzerinden verilmeli.
if [ -n "$TAILSCALE_AUTHKEY" ] && [ -n "$EXIT_NODE_IP" ]; then
    echo "Tailscale'e baglaniliyor ve Exit Node ayarlaniyor..."
    tailscale up --authkey=${TAILSCALE_AUTHKEY} --exit-node=${EXIT_NODE_IP} --exit-node-allow-lan-access=true
else
    echo "UYARI: TAILSCALE_AUTHKEY veya EXIT_NODE_IP bulunamadi. Dogrudan baglanti kullanilacak."
fi

# 3. FastAPI Sunucusunu baslat
echo "FastAPI sunucusu baslatiliyor..."
uvicorn api_service.main:app --host 0.0.0.0 --port 8000
