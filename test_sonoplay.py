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

        btns = await page.locator(".fx").all()
        results = {"buttons": len(btns)}
        ids = await page.locator(".fx").evaluate_all("els => els.map(b => b.dataset.id)")
        results["button_ids"] = ids

        # Play all 8 buttons
        plays = []
        for i in range(len(btns)):
            bid = await btns[i].get_attribute("data-id")
            r = await page.evaluate("""async (id) => {
                const t0 = performance.now();
                await SonoPlay.play(id);
                const t1 = performance.now();
                return { ok: true, ms: t1 - t0 };
            }""", bid)
            plays.append(r)
        results["plays"] = plays

        await page.wait_for_timeout(2500)
        await page.locator("#stopBtn").click()
        await page.wait_for_timeout(300)
        results["stopped_rms"] = await page.evaluate("SonoPlay.level()")

        results["sw_registered"] = await page.evaluate("(async () => { if (!navigator.serviceWorker) return false; const r = await navigator.serviceWorker.getRegistration(); return !!r; })()")
        results["console_errors"] = errors
        results["page_title"] = await page.title()

        await browser.close()
    print("=== RESULTS ===")
    print(results)

asyncio.run(main())
