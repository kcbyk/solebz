import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://en.savefrom.net',
    'Referer': 'https://en.savefrom.net/',
}

r = requests.post(
    'https://worker.savefrom.net/savefrom.php',
    data={'sf_url': 'https://www.youtube.com/watch?v=upItYS15DT4'},
    headers=headers
)

print("Status:", r.status_code)
print("Length:", len(r.text))

# Save response text to scratch for inspection
with open("scratch/sf_response.txt", "w", encoding="utf-8") as f:
    f.write(r.text)

print("Saved to scratch/sf_response.txt")
