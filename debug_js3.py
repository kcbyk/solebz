"""Debug: streamingData tam yapi + visitor data"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
import re, json

client = SolenzClient(proxy=None)
headers = get_youtube_headers()

# Consent cookie ekle
headers["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435; GPS=1"

resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
html = resp.text

# VISITOR_DATA ve ytcfg bilgileri
print("=== YTCFG / VISITOR DATA ===")
vd_match = re.search(r'"VISITOR_DATA"\s*:\s*"([^"]+)"', html)
if vd_match:
    print(f"  VISITOR_DATA: {vd_match.group(1)[:60]}...")

id_token = re.search(r'"ID_TOKEN"\s*:\s*"([^"]*)"', html)
if id_token:
    print(f"  ID_TOKEN: {id_token.group(1)[:60]}...")

# streamingData tam yapisinin ust seviye anahtarlari
pr_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", html, re.DOTALL)
if pr_match:
    pr = json.loads(pr_match.group(1))
    sd = pr.get("streamingData", {})
    print(f"\n=== streamingData ust anahtarlar ===")
    print(f"  {list(sd.keys())}")

    # serverAbrStreamingUrl veya benzeri
    for k, v in sd.items():
        if isinstance(v, str) and len(v) < 500:
            print(f"  {k}: {v[:200]}")

    # Adaptif format tam yapi (ilk 2)
    print(f"\n=== ADAPTIF FORMAT TAM YAPI (ilk 2) ===")
    for f in sd.get("adaptiveFormats", [])[:2]:
        print(json.dumps(f, indent=2)[:500])
        print()

    # Playback durumu
    ps = pr.get("playabilityStatus", {})
    print(f"\n=== playabilityStatus ===")
    print(f"  status: {ps.get('status')}")
    print(f"  reason: {ps.get('reason', '-')}")
    lf = ps.get("liveStreamability")
    if lf:
        print(f"  liveStreamability: VAR")

# InnerTube API denemesi - VISITOR_DATA ile
print(f"\n=== INNERTUBE + VISITOR_DATA ===")
visitor_data = vd_match.group(1) if vd_match else ""
sts_match = re.search(r'signatureTimestamp["\s:]+(\d+)', html)
sts = int(sts_match.group(1)) if sts_match else 20648

api_url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
payload = {
    "videoId": "dQw4w9WgXcQ",
    "context": {
        "client": {
            "hl": "en",
            "gl": "US",
            "clientName": "WEB",
            "clientVersion": "2.20250115.01.00",
            "platform": "DESKTOP",
            "visitorData": visitor_data,
        }
    },
    "playbackContext": {
        "contentPlaybackContext": {
            "signatureTimestamp": sts
        }
    },
    "contentCheckOk": True,
    "racyCheckOk": True,
}
api_headers = {
    "Content-Type": "application/json",
    "Origin": "https://www.youtube.com",
    "Referer": "https://www.youtube.com/",
    "X-YouTube-Client-Name": "1",
    "X-YouTube-Client-Version": "2.20250115.01.00",
    "Cookie": "CONSENT=YES+cb.20210328-17-p0.en+FX+435",
}
if visitor_data:
    api_headers["X-Goog-Visitor-Id"] = visitor_data

resp2 = client.post(api_url, headers=api_headers, json_data=payload, timeout=20)
print(f"  Status: {resp2.status_code}")
if resp2.status_code == 200:
    data = resp2.json()
    ps2 = data.get("playabilityStatus", {})
    sd2 = data.get("streamingData", {})
    print(f"  playabilityStatus: {ps2.get('status')}")
    formats2 = sd2.get("formats", [])
    adaptive2 = sd2.get("adaptiveFormats", [])
    print(f"  formats: {len(formats2)}, adaptive: {len(adaptive2)}")

    for f in formats2[:2]:
        has_url = "url" in f
        has_cipher = "signatureCipher" in f
        print(f"    format itag={f.get('itag')} url={'VAR' if has_url else 'YOK'} cipher={'VAR' if has_cipher else 'YOK'}")
        if has_url:
            print(f"      url: {f['url'][:120]}...")

    for f in adaptive2[:5]:
        has_url = "url" in f
        has_cipher = "signatureCipher" in f
        q = f.get("qualityLabel", "")
        print(f"    adaptive itag={f.get('itag')} {q} url={'VAR' if has_url else 'YOK'} cipher={'VAR' if has_cipher else 'YOK'}")
        if has_url:
            print(f"      url: {f['url'][:120]}...")

client.close()
