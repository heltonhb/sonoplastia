import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8765/index.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        result = await page.evaluate("""async () => {
            return {
                hasSonoPlay: !!window.SonoPlay,
                state: SonoPlay ? SonoPlay.state : null,
                loaded: SonoPlay ? SonoPlay.loaded : null,
                current: SonoPlay ? SonoPlay.current : null,
            };
        }""")
        print("result:", result)
        print("errors:", errors[:5], "..." if len(errors) > 5 else "")
        await browser.close()

asyncio.run(main())
