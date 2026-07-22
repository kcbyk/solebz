import requests

# Test 1: savetube API
try:
    r = requests.get('https://cdn51.savetube.su/info?url=https://www.youtube.com/watch?v=upItYS15DT4', timeout=10)
    print("savetube Status:", r.status_code)
    print("savetube Json keys:", list(r.json().keys()) if r.status_code == 200 else r.text[:200])
except Exception as e:
    print("savetube Error:", e)

# Test 2: yt1s API
try:
    r = requests.post('https://yt1s.ltd/api/ajaxSearch/index', data={'q': 'https://www.youtube.com/watch?v=upItYS15DT4', 'vt': 'home'}, timeout=10)
    print("yt1s Status:", r.status_code)
    print("yt1s Json keys:", list(r.json().keys()) if r.status_code == 200 else r.text[:200])
except Exception as e:
    print("yt1s Error:", e)
