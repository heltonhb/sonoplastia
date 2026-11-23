import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8765/index.html"

async def get_canvas_pixels(page):
    return await page.evaluate("""() => {
        const c = document.getElementById('scope');
        const ctx = c.getContext('2d');
        const d = ctx.getImageData(0,0,c.width,c.height).data;
        let mx=0, count=0;
        for(let i=0;i<d.length;i+=4){
            if(d[i] > 128) { mx=Math.max(mx,d[i]); count++; }
        }
        return { mx, count, width: c.width, height: c.height };
    }""")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # sem som
        p1 = await get_canvas_pixels(page)
        # tocar
        await page.locator('.fx[data-id="storm"]').click()
        await page.wait_for_timeout(800)
        p2 = await get_canvas_pixels(page)
        # parar
        await page.evaluate("SonoPlay.stop()")
        await page.wait_for_timeout(300)
        p3 = await get_canvas_pixels(page)
        print("no-sound pixels:", p1)
        print("play-sound   pixels:", p2)
        print("after-stop   pixels:", p3)
        print("errors:", errors)
        await browser.close()

asyncio.run(main())
