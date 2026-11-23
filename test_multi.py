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

        # 1) tocar o mesmo botão duas vezes seguidas -> deve aprimorar só esse
        btn = page.locator('.fx[data-id="door"]')
        await btn.click()
        await page.wait_for_timeout(1000)
        rms1 = await page.evaluate("SonoPlay.level()")
        await btn.click()
        await page.wait_for_timeout(1000)
        rms2 = await page.evaluate("SonoPlay.level()")
        print("same-button second tap rms1/rms2:", rms1, rms2)

        # 2) tocar dois botões diferentes simultaneamente
        btn2 = page.locator('.fx[data-id="sad"]')
        await btn.click()  # door
        await page.wait_for_timeout(400)
        await btn2.click()
        await page.wait_for_timeout(800)
        rms3 = await page.evaluate("SonoPlay.level()")
        print("two sounds rms:", rms3)
        await page.evaluate("SonoPlay.stop()")
        await page.wait_for_timeout(300)
        rms4 = await page.evaluate("SonoPlay.level()")
        print("after SonoPlay.stop rms:", rms4)

        # 3) check current API
        cur = await page.evaluate("SonoPlay.current")
        print("current after two:", cur)

        print("errors:", errors)
        await browser.close()

asyncio.run(main())
