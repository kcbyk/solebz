import requests
import json

# Test Cobalt API v10
try:
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    r = requests.post("https://api.cobalt.tools", json={"url": "https://www.youtube.com/watch?v=upItYS15DT4"}, headers=headers)
    print("Cobalt status:", r.status_code)
    print("Cobalt json:", r.json())
except Exception as e:
    print("Cobalt error:", e)
