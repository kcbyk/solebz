"""Debug: Player JS - reverse/splice/swap kullanan fonksiyonlari bul"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
import re

client = SolenzClient(proxy=None)
headers = get_youtube_headers()
headers["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435"

resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
js_match = re.search(r'"(/s/player/[^"]+base\.js)"', resp.text)
js_url = "https://www.youtube.com" + js_match.group(1)
js = client.get(js_url, timeout=30).text

# reverse() kullanilan konumlari bul
print("=== .reverse() kullanim konumlari ===")
for m in re.finditer(r'\.reverse\(\)', js):
    pos = m.start()
    # Bu satirdaki fonksiyonu bul (200 karakter geriye bak)
    ctx = js[max(0,pos-200):pos+50]
    print(f"\n  @{pos}:")
    print(f"    {ctx}")
    print()

# Helper nesnesi: reverse, splice, swap iceren object literal
print("\n=== HELPER NESNESI ARAMA ===")
# Pattern: var XX={YY:function(a,b){...reverse...}, ZZ:function(a,b){...splice...}, ...}
# veya: var XX={YY:function(a){a.reverse()}, ...}
helper_pattern = r'var\s+(\w+)\s*=\s*\{((?:\s*\w+\s*:\s*function\s*\([^)]*\)\s*\{[^}]+\}\s*,?\s*)+)\}'
for m in re.finditer(helper_pattern, js):
    body = m.group(2)
    if 'reverse' in body or 'splice' in body:
        name = m.group(1)
        print(f"  Helper nesnesi: {name}")
        print(f"    {m.group(0)[:500]}")
        print()

        # Bu nesneyi kullanan fonksiyonu bul
        escaped = re.escape(name)
        user_pattern = rf'(\w+)\s*=\s*function\s*\(\s*\w+\s*\)\s*\{{[^}}]*{escaped}\.[^}}]+\}}'
        for um in re.finditer(user_pattern, js):
            print(f"  Kullanan fonksiyon: {um.group(1)}")
            print(f"    {um.group(0)[:400]}")
            print()

client.close()
