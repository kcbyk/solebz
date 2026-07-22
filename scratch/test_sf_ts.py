from curl_cffi import requests
import time
import re

s = requests.Session(impersonate="chrome124")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://tr.savefrom.net',
    'Referer': 'https://tr.savefrom.net/',
    'X-Requested-With': 'XMLHttpRequest'
}

data = {
    'sf_url': 'https://www.youtube.com/watch?v=upItYS15DT4',
    'ts': str(int(time.time())),
    'app': '',
    'sh': ''
}

r = s.post('https://worker.savefrom.net/savefrom.php', data=data, headers=headers)
print("Status:", r.status_code)
print("Text preview:", r.text[:1500])
