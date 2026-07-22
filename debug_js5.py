"""Debug: Embed sayfasi + alternatif URL elde etme yontemleri"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
from urllib.parse import urlparse, parse_qs, urlencode
import re, json

client = SolenzClient(proxy=None)

# --- YONTEM 1: Embed sayfasi ---
print("=== YONTEM 1: EMBED SAYFASI ===")
headers = get_youtube_headers(referer="https://www.youtube.com/")
resp = client.get("https://www.youtube.com/embed/dQw4w9WgXcQ", headers=headers)
html = resp.text
print(f"  Status: {resp.status_code}, Boyut: {len(html)}")

# Embed sayfasinda player response ara
for pattern_name, pattern in [
    ("ytInitialPlayerResponse", r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;"),
    ("ytcfg.set playerResponse", r'"embedPreview".*?"playerResponse"\s*:\s*"(\{.+?\})"'),
    ("embedded_player_response", r'"embedded_player_response"\s*:\s*"(.+?)"'),
    ("ytInitialData", r"ytInitialData\s*=\s*(\{.+?\})\s*;"),
]:
    m = re.search(pattern, html, re.DOTALL)
    if m:
        print(f"  {pattern_name}: BULUNDU ({len(m.group(1))} karakter)")
        try:
            raw = m.group(1)
            # JSON unicode escape coz
            if "\\x" in raw or "\\u" in raw:
                raw = raw.encode().decode("unicode_escape")
            data = json.loads(raw)
            sd = data.get("streamingData", {})
            if sd:
                fmts = sd.get("formats", [])
                adap = sd.get("adaptiveFormats", [])
                print(f"    formats: {len(fmts)}, adaptive: {len(adap)}")
                for f in (fmts + adap)[:3]:
                    has_url = "url" in f
                    has_cipher = "signatureCipher" in f or "cipher" in f
                    print(f"    itag={f.get('itag')} url={'VAR' if has_url else 'YOK'} cipher={'VAR' if has_cipher else 'YOK'}")
        except Exception as e:
            print(f"    Parse hatasi: {e}")
    else:
        print(f"  {pattern_name}: BULUNAMADI")

# --- YONTEM 2: SABR URL + sabr=0 ---
print("\n=== YONTEM 2: SABR DEVRE DISI ===")
headers2 = get_youtube_headers()
headers2["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435"
resp2 = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers2)
pr_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", resp2.text, re.DOTALL)
pr = json.loads(pr_match.group(1))
sd = pr.get("streamingData", {})
sabr_url = sd.get("serverAbrStreamingUrl", "")

if sabr_url:
    # sabr=1 -> sabr=0 dene
    no_sabr = sabr_url.replace("sabr=1", "sabr=0").replace("&sabr_redirect=1", "")
    parsed = urlparse(no_sabr)
    params = parse_qs(parsed.query, keep_blank_values=True)

    for itag in [18, 137, 140]:
        params["itag"] = [str(itag)]
        if "sabr" in params:
            del params["sabr"]
        test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode({k: v[0] for k, v in params.items()})}"
        try:
            r = client.head(test_url, headers={"Referer": "https://www.youtube.com/"}, timeout=10)
            ct = r.headers.get("Content-Type", "?")
            cl = r.headers.get("Content-Length", "?")
            print(f"  itag={itag}: {r.status_code} | CT={ct} | CL={cl}")
        except Exception as e:
            print(f"  itag={itag}: HATA - {e}")

# --- YONTEM 3: signatureCipher coz (itag 18) ve URL yapisini analiz et ---
print("\n=== YONTEM 3: SIGNATURE CIPHER ANALIZ ===")
for f in sd.get("formats", []):
    cipher = f.get("signatureCipher", "")
    if cipher:
        cp = parse_qs(cipher)
        raw_url = cp.get("url", [""])[0]
        sig = cp.get("s", [""])[0]
        sp = cp.get("sp", [""])[0]
        print(f"  itag={f.get('itag')}")
        print(f"  s (imza): {sig[:60]}...  (uzunluk: {len(sig)})")
        print(f"  sp: {sp}")
        print(f"  url: {raw_url[:150]}...")

        # URL parametrelerini analiz et
        url_parsed = urlparse(raw_url)
        url_params = parse_qs(url_parsed.query)
        print(f"  URL parametreleri: {list(url_params.keys())}")

        # Bu URL'nin yapisini kullanarak diger itaglar icin URL uretebilir miyiz?
        # Temel bilgiler: host, path, expire, ei, ip, id, source, sig vs.

# --- YONTEM 4: get_video_info (eski endpoint) ---
print("\n=== YONTEM 4: get_video_info ===")
try:
    gvi_url = "https://www.youtube.com/get_video_info?video_id=dQw4w9WgXcQ&eurl=https://youtube.googleapis.com/v/dQw4w9WgXcQ&html5=1&c=TVHTML5&cver=6.20180913"
    r = client.get(gvi_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        from urllib.parse import unquote
        body = r.text
        if "player_response=" in body or "player_response" in body:
            print(f"  player_response BULUNDU")
        else:
            print(f"  Body (ilk 200): {body[:200]}")
except Exception as e:
    print(f"  HATA: {e}")

client.close()
