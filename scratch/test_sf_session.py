from curl_cffi import requests

s = requests.Session(impersonate="chrome124")

# Step 1: Visit home page to set cookies
r1 = s.get("https://tr.savefrom.net/")
print("Home status:", r1.status_code)
print("Cookies:", s.cookies.get_dict())

# Step 2: Post to savefrom.php
headers = {
    'Origin': 'https://tr.savefrom.net',
    'Referer': 'https://tr.savefrom.net/',
    'X-Requested-With': 'XMLHttpRequest'
}

r2 = s.post(
    'https://worker.savefrom.net/savefrom.php',
    data={'sf_url': 'https://www.youtube.com/watch?v=upItYS15DT4'},
    headers=headers
)

print("Savefrom status:", r2.status_code)
print("Response text:", r2.text[:1000])
