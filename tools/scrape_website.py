# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright"]
# ///
from playwright.async_api import async_playwright
import asyncio

async def scrape_website(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            content = await page.content()
            with open("scraped_content.html", "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print("Failed to load page:", e)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(
        scrape_website(
            "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
        )
    )
    print("Scraping completed and content saved to scraped_content.html")
