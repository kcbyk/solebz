import asyncio
from playwright.async_api import async_playwright, TimeoutError
import logging

logger = logging.getLogger("savefrom_scraper")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

from playwright_stealth import Stealth

async def extract_savefrom(url: str) -> dict:
    """
    Playwright kullanarak savefrom.net uzerinden indirme linki ve videoya ait verileri ceker.
    """
    logger.info(f"SaveFrom scraper baslatiliyor: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        try:
            # SaveFrom turkce sayfasina git
            logger.info("SaveFrom.net sayfasina gidiliyor...")
            await page.goto("https://tr.savefrom.net/", wait_until="domcontentloaded")
            
            # Linki yapistir
            logger.info("URL arama kutusuna yaziliyor...")
            await page.fill('input#sf_url', url)
            
            # İndir butonuna tikla
            logger.info("Indir butonuna tiklaniyor...")
            await page.click('button#sf_submit')
            
            # Sonuc kutusunun yuklenmesini bekle
            logger.info("Sonuclarin gelmesi bekleniyor (maksimum 30 saniye)...")
            try:
                await page.wait_for_selector('.result-box', timeout=30000)
            except TimeoutError:
                raise Exception("SaveFrom.net yanit vermedi veya zaman asimina ugradi.")

            # Baslik (Title) cek
            title_el = await page.query_selector('.info-box .title')
            title = await title_el.inner_text() if title_el else "Bilinmeyen Video"
            
            # Kapak Fotografi (Thumbnail) cek
            img_el = await page.query_selector('.media-result .thumb')
            thumbnail = await img_el.get_attribute('src') if img_el else None
            
            # Direct Download Link (MP4) cek
            link_el = await page.query_selector('.def-btn-box a.def-btn')
            if not link_el:
                raise Exception("Indirme linki bulunamadi. Video gizli, kısıtlı veya format desteklenmiyor olabilir.")
                
            download_url = await link_el.get_attribute('href')
            
            logger.info(f"Scraping basarili: {title}")
            return {
                "title": title.strip(),
                "thumbnail": thumbnail,
                "download_url": download_url
            }
            
        except Exception as e:
            logger.error(f"Scraper hatasi: {e}")
            await page.screenshot(path="scratch/scraper_error.png")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    # Test block
    async def test():
        res = await extract_savefrom("https://www.youtube.com/watch?v=upItYS15DT4")
        print("Sonuc:", res)
    asyncio.run(test())
