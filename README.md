# Solenz Downloader

Harici araçlara (yt-dlp, ffmpeg vb.) bağımlı olmayan, TLS parmak izi taklidi yapabilen bir Python medya indirme kütüphanesi.

## Desteklenen Platformlar
- YouTube (✅ Tam destek, 4K'a kadar)
- TikTok (⚠️ Mevcut ancak bakım gerekiyor)
- Instagram (⚠️ Mevcut ancak bakım gerekiyor)

## Kurulum
```bash
pip install solenz-downloader
```

## Kullanım
```python
import solenz_downloader

# Video bilgilerini çıkar
result = solenz_downloader.extract("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(f"Başlık: {result.title}")

# Video indir
yol = solenz_downloader.download(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_dir="./indirilenler",
    quality="1080p"
)

# Sadece ses indir
ses_yolu = solenz_downloader.download_audio(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_dir="./indirilenler"
)
```

## Gereksinimler
- Python 3.10+
- `requests >= 2.31.0`
- `curl_cffi >= 0.7.0` isteğe bağlıdır; desteklenen x86_64/ARM64 sistemlerde TLS taklidi için kullanılır.
- Termux ARMv7 sunucusu için FastAPI, uvicorn veya Rust kurulması gerekmez; API standart Python HTTP sunucusunu kullanır.

## Termux sunucusu ve API

`server/` klasörü, Termux cihazını geçici dosya teslim eden bir API sunucusuna dönüştürür. İş tamamlandığında dosya `/file` endpoint'i üzerinden tamamen gönderildikten sonra silinir. Yarım kalan işler TTL cleanup ile temizlenir.

Termux'ta:

```bash
pkg update -y
pkg install python libffi openssl -y
python -m pip install --upgrade --no-cache-dir requests
python -m pip install --upgrade --no-cache-dir solenz-downloader==0.1.7
```

API anahtarı olmadan servis başlatılmaz:

```bash
export SOLENZ_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SOLENZ_HOST=127.0.0.1
export SOLENZ_PORT=8787
python -m server.run
```

Sağlık kontrolü:

```bash
curl http://127.0.0.1:8787/health
```

İş oluşturma:

```bash
curl -X POST http://127.0.0.1:8787/v1/jobs \
  -H "Authorization: Bearer $SOLENZ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","mode":"audio","prefer_ext":"webm"}'
```

Termux'u uykuya karşı korumak için `termux-wake-lock`, cihaz açılışında başlatmak için Termux:Boot kullanılmalıdır. Android'in pil optimizasyonundan Termux çıkarılmalıdır. Android'in kendisi, güç veya ağ kesintileri nedeniyle hiçbir servis için mutlak 7/24 garantisi vermez; başlangıç script'i servis sürecini otomatik başlatmaya yardımcı olur.

## Vercel web uygulaması

`web/` klasörü, Vercel'e deploy edilebilen Next.js uygulaması ve server-side API proxy'sidir. Vercel değişkenleri:

- `SOLENZ_API_BASE_URL`: Tailscale Funnel veya güvenli HTTPS gateway adresi
- `SOLENZ_API_KEY`: Termux API anahtarı

API anahtarı tarayıcıya gönderilmez. Farklı web siteleri aynı Termux API'sini kendi backend proxy'leri üzerinden kullanabilir.

## Lisans
MIT
