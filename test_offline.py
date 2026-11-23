import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8765/index.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await context.new_page()
        errors = []
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        # click storm, then go offline
        await page.locator('.fx[data-id="storm"]').click()
        await page.wait_for_timeout(800)
        rms_online = await page.evaluate("SonoPlay.level()")
        print("rms online:", rms_online)
        # go offline
        await context.set_offline(True)
        await page.goto(URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        # check if the app still works
        plays = await page.evaluate("""async () => {
            const res = await SonoPlay.play('hits');
            const loaded = SonoPlay.loaded;
            return { ok: true, loaded, state: SonoPlay.state };
        }""")
        print("after offline reload:", plays)
        # check if console had errors
        print("errors:", errors)
        await browser.close()

asyncio.run(main())
