import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print('Sayfaya gidiliyor...')
        await page.goto('https://freeytubedownloader.com/tr/')
        
        print('URL yaziliyor...')
        await page.fill('input[type="text"]', "https://www.youtube.com/watch?v=upItYS15DT4")
        
        print('Submit butonuna tiklaniyor...')
        # Formun icindeki submit butonu veya 'Indir' yazan buton
        await page.click('button:has-text("İndir")')
        
        print('Sonucun yuklenmesi bekleniyor...')
        # Video kaynagi veya diger sayfaya yonlendirme
        await page.wait_for_timeout(10000)
        
        await page.screenshot(path='scratch/freeyt_submit.png')
        print("Mevcut URL:", page.url)
        
        # Ekrandaki linklere bakalim
        links = await page.query_selector_all('a')
        for link in links:
            href = await link.get_attribute('href')
            text = await link.inner_text()
            if href and ('googlevideo' in href or 'download' in href):
                print(f"BULUNDU (A): {text} -> {href}")

        # Eger baska bir frame / video varsa:
        video = await page.query_selector('video')
        if video:
            src = await video.get_attribute('src')
            print(f"BULUNDU (VIDEO): {src}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
