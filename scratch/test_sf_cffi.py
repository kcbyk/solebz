from curl_cffi import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://tr.savefrom.net',
    'Referer': 'https://tr.savefrom.net/',
}

try:
    s = requests.Session(impersonate="chrome124")
    r = s.post(
        'https://worker.savefrom.net/savefrom.php',
        data={'sf_url': 'https://www.youtube.com/watch?v=upItYS15DT4'},
        headers=headers,
        timeout=15
    )
    print("Status:", r.status_code)
    print("Length:", len(r.text))
    with open("scratch/sf_cffi.txt", "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Written to scratch/sf_cffi.txt")
except Exception as e:
    print("Error:", e)
