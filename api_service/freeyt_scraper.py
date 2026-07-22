import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger("freeyt_scraper")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

async def extract_freeyt(url: str) -> dict:
    """
    Playwright kullanarak freeytubedownloader.com uzerinden indirme linkini (googlevideo) ceker.
    """
    logger.info(f"FreeYT scraper baslatiliyor: {url}")
    
    async with async_playwright() as p:
        # Render uzerinde Tailscale SOCKS5 proxy'sini kullan
        # Boylece istekler datacenter IP'si yerine Exit Node (Ev IP'si) uzerinden cikar
        browser = await p.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled"],
            proxy={"server": "socks5://127.0.0.1:1055"}
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            logger.info("FreeYT sayfasına gidiliyor...")
            await page.goto("https://freeytubedownloader.com/tr/")
            
            logger.info("URL yaziliyor...")
            await page.fill('input[type="text"]', url)
            
            logger.info("Indir butonuna tiklaniyor...")
            await page.click('button:has-text("İndir")')
            
            logger.info("Sonuclarin gelmesi bekleniyor...")
            
            # Sonuc sayfasindaki "Videoyu İndir" butonunun href'ini veya yeni sekmedeki URL'yi almamiz lazim
            download_url = None
            
            # 'Videoyu İndir' butonunu bekle (Bazen sayfada yuklenmesi zaman alir)
            await page.wait_for_selector('button:has-text("Videoyu İndir"), a:has-text("Videoyu İndir")', timeout=30000)
            
            # Butona veya linke tikla ki indirme baslasin veya yeni sekme acilsin
            btn = await page.query_selector('button:has-text("Videoyu İndir"), a:has-text("Videoyu İndir")')
            
            if btn:
                tag = await btn.evaluate("el => el.tagName.toLowerCase()")
                if tag == "a":
                    download_url = await btn.get_attribute("href")
                else:
                    # Yeni sekme acacaksa tikla ve bekle
                    async with context.expect_page() as new_page_info:
                        await btn.click()
                    new_page = await new_page_info.value
                    await new_page.wait_for_load_state()
                    
                    # Sayfa yonlendirmesi googlevideo'ya veya baska bir yere olabilir
                    # Bazen googlevideo dogrudan acilir.
                    download_url = new_page.url
                    await new_page.close()
            
            # Title
            title_el = await page.query_selector("h3") # Resimde sagda title vardi
            title = await title_el.inner_text() if title_el else "Video"
            
            # Thumbnail (YouTube video id'den)
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(url)
            video_id = urlparse.parse_qs(parsed.query).get('v')
            if video_id:
                video_id = video_id[0]
            else:
                video_id = parsed.path.split('/')[-1]
            thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            if not download_url:
                raise Exception("Indirme linki alinamadi.")
            
            logger.info(f"Basariyla cekildi: {download_url[:50]}...")
            return {
                "title": title.strip() if title else "Bilinmeyen Video",
                "thumbnail": thumbnail,
                "download_url": download_url
            }
            
        except Exception as e:
            logger.error(f"Scraper hatasi: {e}")
            await page.screenshot(path="scratch/freeyt_error.png")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    async def test():
        res = await extract_freeyt("https://www.youtube.com/watch?v=upItYS15DT4")
        print("Sonuc:", res)
    asyncio.run(test())
