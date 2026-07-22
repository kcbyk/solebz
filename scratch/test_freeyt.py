import asyncio
from playwright.async_api import async_playwright
import json

async def test_freeytubedownloader():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Ag isteklerini dinle
        page.on("response", lambda response: print(f"Response: {response.url} - {response.status}"))
        
        print("Sayfaya gidiliyor...")
        await page.goto("https://freeytubedownloader.com/tr/")
        
        print("URL yaziliyor...")
        await page.fill('input[type="text"]', "https://www.youtube.com/watch?v=upItYS15DT4")
        
        print("Indir veya Ara butonuna basiliyor...")
        # Buton selectorunu bulmamiz lazim. Enter tusu da calisabilir.
        await page.press('input[type="text"]', 'Enter')
        
        print("Bekleniyor...")
        await page.wait_for_timeout(10000)
        
        # Ekrani goruntule
        await page.screenshot(path="scratch/freeyt_test.png")
        print("Tamamlandi.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_freeytubedownloader())
