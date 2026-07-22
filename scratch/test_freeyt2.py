import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print('Navigating...')
        await page.goto('https://freeytubedownloader.com/tr/?mediaLink=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DupItYS15DT4')
        await page.wait_for_timeout(5000)
        
        # Ekrandaki video etiketini bul
        video = await page.query_selector('video')
        if video:
            src = await video.get_attribute('src')
            print('Video src:', src)
            
        # Ekrandaki a (link) etiketlerine bakalim
        links = await page.query_selector_all('a')
        for link in links:
            text = await link.inner_text()
            href = await link.get_attribute('href')
            if href and ('googlevideo' in href or 'download' in href):
                print('Found link:', text.strip(), href)
        
        await page.screenshot(path='scratch/freeyt_result.png')
        await browser.close()

asyncio.run(run())
