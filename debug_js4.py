"""Debug: serverAbrStreamingUrl analizi ve URL insa"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
from urllib.parse import urlparse, parse_qs, urlencode, unquote
import re, json

client = SolenzClient(proxy=None)
headers = get_youtube_headers()
headers["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435"

resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
html = resp.text

pr_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", html, re.DOTALL)
pr = json.loads(pr_match.group(1))
sd = pr.get("streamingData", {})

sabr_url = sd.get("serverAbrStreamingUrl", "")
print("=== serverAbrStreamingUrl ===")
print(f"  URL: {sabr_url[:200]}...")
print()

# URL parametrelerini parse et
parsed = urlparse(sabr_url)
params = parse_qs(parsed.query)
print("=== URL Parametreleri ===")
for k, v in sorted(params.items()):
    val = v[0] if len(v) == 1 else v
    if isinstance(val, str) and len(val) > 80:
        val = val[:80] + "..."
    print(f"  {k}: {val}")

# Test: sabr_url'den dogrudan itag ile indirme URL'si olusturma
# YouTube'da /videoplayback endpoint'i itag parametresiyle calisir
print("\n=== ITAG ILE URL INSA DENEMESI ===")

# sabr_url'nin base kismini al, itag parametresi ekle
base_url = sabr_url.split("&sabr_redirect")[0] if "&sabr_redirect" in sabr_url else sabr_url

# farkli yontemler
for itag in [137, 248, 140]:  # 1080p mp4, 1080p webm, audio m4a
    test_url = re.sub(r'itag=\d+', f'itag={itag}', base_url) if 'itag=' in base_url else f"{base_url}&itag={itag}"
    # ot (output type) parametresini ayarla
    if "ot=" in test_url:
        test_url = re.sub(r'ot=[^&]+', 'ot=fmp4', test_url)

    print(f"\n  itag={itag} test ediliyor...")
    try:
        test_resp = client.head(test_url, headers={"Referer": "https://www.youtube.com/"}, timeout=10)
        print(f"    Status: {test_resp.status_code}")
        print(f"    Content-Type: {test_resp.headers.get('Content-Type', '?')}")
        print(f"    Content-Length: {test_resp.headers.get('Content-Length', '?')}")
    except Exception as e:
        print(f"    Hata: {e}")

# /videoplayback endpoint'ini dene - sabr URL'sinden olustur
print("\n=== /videoplayback DOGRUDAN DENEME ===")
# googlevideo.com host'unu al
host = parsed.netloc
scheme = parsed.scheme
base_path = parsed.path

# Temel parametreleri koru, itag degistir
core_params = {}
for k in ["id", "expire", "ei", "ip", "source", "requiressl", "xpc", "bui", "spc", "vprv", "svpuc", "mime", "rqh", "gir", "clen", "dur", "lmt", "mt", "fvip", "c", "txp", "n", "sparams", "sig", "lsparams", "lsig"]:
    if k in params:
        core_params[k] = params[k][0]

for itag in [137, 140, 18]:
    core_params["itag"] = str(itag)
    test_url2 = f"{scheme}://{host}{base_path}?{urlencode(core_params)}"
    print(f"\n  itag={itag} videoplayback test...")
    try:
        test_resp2 = client.head(test_url2, headers={"Referer": "https://www.youtube.com/", "Origin": "https://www.youtube.com"}, timeout=10)
        print(f"    Status: {test_resp2.status_code}")
        ct = test_resp2.headers.get("Content-Type", "?")
        cl = test_resp2.headers.get("Content-Length", "?")
        print(f"    Content-Type: {ct}, Content-Length: {cl}")
    except Exception as e:
        print(f"    Hata: {e}")

client.close()
