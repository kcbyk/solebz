"""Debug: WEB_REMIX + ANDROID_MUSIC + ANDROID_TESTSUITE + diger istemciler"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
from urllib.parse import urlparse, parse_qs
import re, json

client = SolenzClient(proxy=None)

# Visitor data al
headers = get_youtube_headers()
headers["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435"
resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
vd_match = re.search(r'"VISITOR_DATA"\s*:\s*"([^"]+)"', resp.text)
visitor_data = vd_match.group(1) if vd_match else ""
sts_match = re.search(r'signatureTimestamp["\s:]+(\d+)', resp.text)
sts = int(sts_match.group(1)) if sts_match else 20648
print(f"visitor_data: {visitor_data[:40]}...")
print(f"sts: {sts}")

configs = {
    "WEB_REMIX": {
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "WEB_REMIX",
                "clientVersion": "1.20250113.01.00",
                "platform": "DESKTOP",
                "visitorData": visitor_data,
            }
        },
        "headers": {
            "X-YouTube-Client-Name": "67",
            "X-YouTube-Client-Version": "1.20250113.01.00",
            "Referer": "https://music.youtube.com/",
            "Origin": "https://music.youtube.com",
        },
    },
    "WEB_CREATOR": {
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "WEB_CREATOR",
                "clientVersion": "1.20250113.01.00",
                "platform": "DESKTOP",
                "visitorData": visitor_data,
            }
        },
        "headers": {
            "X-YouTube-Client-Name": "62",
            "X-YouTube-Client-Version": "1.20250113.01.00",
        },
    },
    "ANDROID_MUSIC": {
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "ANDROID_MUSIC",
                "clientVersion": "7.27.52",
                "androidSdkVersion": 34,
                "userAgent": "com.google.android.apps.youtube.music/7.27.52 (Linux; U; Android 14) gzip",
                "osName": "Android",
                "osVersion": "14",
            }
        },
        "headers": {
            "User-Agent": "com.google.android.apps.youtube.music/7.27.52 (Linux; U; Android 14) gzip",
            "X-YouTube-Client-Name": "21",
            "X-YouTube-Client-Version": "7.27.52",
        },
    },
    "ANDROID_TESTSUITE": {
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "ANDROID_TESTSUITE",
                "clientVersion": "1.9",
                "androidSdkVersion": 34,
                "userAgent": "com.google.android.youtube/1.9 (Linux; U; Android 14) gzip",
                "osName": "Android",
                "osVersion": "14",
            }
        },
        "headers": {
            "User-Agent": "com.google.android.youtube/1.9 (Linux; U; Android 14) gzip",
            "X-YouTube-Client-Name": "30",
            "X-YouTube-Client-Version": "1.9",
        },
    },
    "WEB_KIDS": {
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "WEB_KIDS",
                "clientVersion": "2.20250113.00.00",
                "platform": "DESKTOP",
                "visitorData": visitor_data,
            }
        },
        "headers": {
            "X-YouTube-Client-Name": "76",
            "X-YouTube-Client-Version": "2.20250113.00.00",
        },
    },
    "ANDROID_VR": {
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "ANDROID_VR",
                "clientVersion": "1.60.19",
                "androidSdkVersion": 34,
                "userAgent": "com.google.android.apps.youtube.vr.oculus/1.60.19 (Linux; U; Android 14) gzip",
                "osName": "Android",
                "osVersion": "14",
                "deviceMake": "Oculus",
                "deviceModel": "Quest 3",
            }
        },
        "headers": {
            "User-Agent": "com.google.android.apps.youtube.vr.oculus/1.60.19 (Linux; U; Android 14) gzip",
            "X-YouTube-Client-Name": "28",
            "X-YouTube-Client-Version": "1.60.19",
        },
    },
}

for name, cfg in configs.items():
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    api_url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
    payload = {
        "videoId": "dQw4w9WgXcQ",
        "context": cfg["context"],
        "playbackContext": {"contentPlaybackContext": {"signatureTimestamp": sts}},
        "contentCheckOk": True,
        "racyCheckOk": True,
    }

    req_headers = {
        "Content-Type": "application/json",
        "Origin": "https://www.youtube.com",
        "Referer": "https://www.youtube.com/",
        "Cookie": "CONSENT=YES+cb.20210328-17-p0.en+FX+435",
    }
    if visitor_data:
        req_headers["X-Goog-Visitor-Id"] = visitor_data
    req_headers.update(cfg.get("headers", {}))

    try:
        r = client.post(api_url, headers=req_headers, json_data=payload, timeout=15)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            ps = data.get("playabilityStatus", {})
            sd = data.get("streamingData", {})
            print(f"  playability: {ps.get('status')}")
            if ps.get("status") != "OK":
                print(f"  reason: {ps.get('reason', '?')[:80]}")
                continue

            fmts = sd.get("formats", [])
            adap = sd.get("adaptiveFormats", [])
            print(f"  formats: {len(fmts)}, adaptive: {len(adap)}")

            url_count = sum(1 for f in fmts+adap if "url" in f)
            cipher_count = sum(1 for f in fmts+adap if "signatureCipher" in f)
            none_count = sum(1 for f in fmts+adap if "url" not in f and "signatureCipher" not in f)
            print(f"  URL: {url_count}, Cipher: {cipher_count}, None: {none_count}")

            if url_count > 0:
                # En yuksek kalite
                best = None
                for f in adap:
                    if "url" in f and f.get("qualityLabel"):
                        if not best or (f.get("height",0) > best.get("height",0)):
                            best = f
                if best:
                    print(f"  EN IYI: itag={best['itag']} {best.get('qualityLabel','')} {best.get('mimeType','')[:30]}")
                    print(f"    URL: {best['url'][:150]}...")
                    # URL'yi test et
                    try:
                        tr = client.head(best["url"], headers={"Referer":"https://www.youtube.com/"}, timeout=10)
                        print(f"    HEAD test: {tr.status_code} CT={tr.headers.get('Content-Type','?')} CL={tr.headers.get('Content-Length','?')}")
                    except:
                        pass

                for f in fmts:
                    if "url" in f:
                        print(f"  FMT: itag={f['itag']} {f.get('qualityLabel','')} url=VAR")
                        break
        else:
            print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  HATA: {type(e).__name__}: {e}")

client.close()
