"""Debug: ANDROID/IOS InnerTube API detayli hata analizi"""
from solenz_downloader.core.client import SolenzClient
import json

client = SolenzClient(proxy=None)

configs = {
    "ANDROID_v19": {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "ANDROID",
                "clientVersion": "19.29.37",
                "androidSdkVersion": 34,
                "userAgent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14) gzip",
                "osName": "Android",
                "osVersion": "14",
            }
        },
        "headers": {
            "User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14) gzip",
            "X-YouTube-Client-Name": "3",
            "X-YouTube-Client-Version": "19.29.37",
        },
        "api_key": "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w",
    },
    "ANDROID_v17": {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "ANDROID",
                "clientVersion": "17.31.35",
                "androidSdkVersion": 30,
                "userAgent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip",
                "osName": "Android",
                "osVersion": "11",
            }
        },
        "headers": {
            "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip",
            "X-YouTube-Client-Name": "3",
            "X-YouTube-Client-Version": "17.31.35",
        },
        "api_key": "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w",
    },
    "ANDROID_EMBED": {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "ANDROID_EMBEDDED_PLAYER",
                "clientVersion": "19.29.37",
                "androidSdkVersion": 34,
            },
            "thirdParty": {
                "embedUrl": "https://www.google.com",
            }
        },
        "headers": {
            "User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14) gzip",
            "X-YouTube-Client-Name": "55",
            "X-YouTube-Client-Version": "19.29.37",
        },
        "api_key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
    },
    "TVHTML5": {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "TVHTML5",
                "clientVersion": "7.20250113.19.00",
                "platform": "TV",
            }
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.5)",
            "X-YouTube-Client-Name": "7",
            "X-YouTube-Client-Version": "7.20250113.19.00",
        },
        "api_key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
    },
    "MEDIA_CONNECT": {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "MEDIA_CONNECT_FRONTEND",
                "clientVersion": "0.1",
            }
        },
        "headers": {},
        "api_key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
    },
    "WEB_EMBEDDED": {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "WEB_EMBEDDED_PLAYER",
                "clientVersion": "1.20250113.01.00",
            },
            "thirdParty": {
                "embedUrl": "https://www.google.com",
            }
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        },
        "api_key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
    },
}

for name, cfg in configs.items():
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")

    api_url = f"https://www.youtube.com/youtubei/v1/player?key={cfg['api_key']}&prettyPrint=false"
    payload = {
        "videoId": "dQw4w9WgXcQ",
        "context": cfg["context"],
        "contentCheckOk": True,
        "racyCheckOk": True,
    }

    req_headers = {
        "Content-Type": "application/json",
        "Origin": "https://www.youtube.com",
        "Referer": "https://www.youtube.com/",
    }
    req_headers.update(cfg.get("headers", {}))

    try:
        resp = client.post(api_url, headers=req_headers, json_data=payload, timeout=15)
        print(f"  Status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            ps = data.get("playabilityStatus", {})
            sd = data.get("streamingData", {})
            print(f"  playabilityStatus: {ps.get('status')}")
            if ps.get('status') != 'OK':
                print(f"  reason: {ps.get('reason', '?')[:100]}")

            formats = sd.get("formats", [])
            adaptive = sd.get("adaptiveFormats", [])
            print(f"  formats: {len(formats)}, adaptive: {len(adaptive)}")

            # URL var mi kontrol
            url_count = 0
            cipher_count = 0
            none_count = 0
            for f in formats + adaptive:
                if "url" in f:
                    url_count += 1
                elif "signatureCipher" in f:
                    cipher_count += 1
                else:
                    none_count += 1
            print(f"  URL: {url_count}, Cipher: {cipher_count}, None: {none_count}")

            if url_count > 0:
                # Ilk URL'li formati goster
                for f in formats + adaptive:
                    if "url" in f:
                        print(f"  ORNEK URL (itag {f.get('itag')}): {f['url'][:120]}...")
                        break
        else:
            body = resp.text[:300]
            print(f"  Body: {body}")
    except Exception as e:
        print(f"  HATA: {type(e).__name__}: {e}")

client.close()
