import asyncio
import os

from patchright.async_api import async_playwright
from hcaptcha_bridge import HCaptchaSolver

API_KEY = os.environ["HCAPTCHA_API_KEY"]
URL = "https://example.com/your-page"  # Replace with the page containing hCaptcha.
MAX_ROUNDS = 6
TIMEOUT = 90  # Seconds.


async def main():
    if URL == "https://example.com/your-page":
        raise ValueError("Replace URL with the page containing hCaptcha.")
    async with async_playwright() as runtime:
        browser = await runtime.chromium.launch(channel="chrome", headless=False)
        try:
            page = await browser.new_page()
            await page.goto(URL, wait_until="domcontentloaded")
            # Your navigation or form filling can go here.
            solver = HCaptchaSolver(page, API_KEY, max_rounds=MAX_ROUNDS, timeout=TIMEOUT)
            token = await solver.solve()
            if not token:
                raise RuntimeError("No token received. Check solver.stats for the reason.")

            # Use `token` here, or continue your automation on this page.
            print("Token received.")
            return token
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
