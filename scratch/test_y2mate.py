from curl_cffi import requests
import json

s = requests.Session(impersonate="chrome124")

# Test y2mate.nu or y2mate.is or y2mate.com
print("--- Y2MATE TEST ---")
try:
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    r = s.post("https://www.y2mate.com/mates/analyzeV2/ajax", data={"k_query": "https://www.youtube.com/watch?v=upItYS15DT4", "k_page": "home", "hl": "en", "q_auto": 0}, headers=headers)
    print("Status:", r.status_code)
    if r.status_code == 200:
        res = r.json()
        print("Status in json:", res.get("status"))
        print("Title:", res.get("title"))
        print("Links count:", len(res.get("links", {})))
except Exception as e:
    print("Error:", e)
