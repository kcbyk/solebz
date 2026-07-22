from curl_cffi import requests
import json

s = requests.Session(impersonate="chrome124")

# Test 1: y2mate.is API
try:
    r = s.post("https://y2mate.is/api/v1/analyze", data={"url": "https://www.youtube.com/watch?v=upItYS15DT4"})
    print("y2mate.is status:", r.status_code)
    if r.status_code == 200:
        print("y2mate.is json:", r.json().keys())
except Exception as e:
    print("y2mate.is error:", e)

# Test 2: savefrom API via RapidAPI / SSYouTube endpoint
try:
    r = s.post("https://ssyoutube.com/api/convert", json={"url": "https://www.youtube.com/watch?v=upItYS15DT4"})
    print("ssyoutube status:", r.status_code)
    if r.status_code == 200:
        print("ssyoutube json:", r.json())
except Exception as e:
    print("ssyoutube error:", e)
