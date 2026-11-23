import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8765/index.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(4000)
        # verify loaded state
        loaded = await page.evaluate("SonoPlay.loaded")
        print("loaded:", loaded)

        # play first sound, measure rms + canvas height during playback
        rms_vals = []
        canvas_heights = []
        for i in range(2):
            await page.evaluate("SonoPlay.play('storm')")
            await page.wait_for_timeout(1100)
            rms = await page.evaluate("SonoPlay.level()")
            rms_vals.append(rms)
            ch = await page.evaluate("""() => {
                const c = document.getElementById('scope');
                const ctx = c.getContext('2d');
                const d = ctx.getImageData(0,0,c.width,c.height).data;
                let mx=0;
                for(let i=0;i<d.length;i+=4) mx=Math.max(mx,d[i]);
                return mx;
            }""")
            canvas_heights.append(ch)
            await page.evaluate("SonoPlay.stop()")
            await page.wait_for_timeout(300)
        print("rms during play:", rms_vals)
        print("canvas pixel max during play:", canvas_heights)
        print("console errors:", errors)
        await browser.close()

asyncio.run(main())
