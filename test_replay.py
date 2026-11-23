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
        await page.wait_for_timeout(3500)

        btn = page.locator('.fx[data-id="door"]')

        # toca, para no meio, e toca de novo — o botão precisa voltar a funcionar
        await btn.click()
        await page.wait_for_timeout(700)
        rms1 = await page.evaluate("SonoPlay.level()")
        await btn.click()          # toggle: parar
        await page.wait_for_timeout(400)
        rms2 = await page.evaluate("SonoPlay.level()")
        await btn.click()          # deve TOCAR de novo
        await page.wait_for_timeout(700)
        rms3 = await page.evaluate("SonoPlay.level()")
        cur = await page.evaluate("SonoPlay.current")

        print("rms ao tocar:      ", round(rms1, 4))
        print("rms após parar:    ", round(rms2, 4))
        print("rms ao tocar de novo:", round(rms3, 4), "(esperado >> rms2)")
        print("current:           ", cur)
        print("PASSOU:" , rms3 > rms2 + 0.02)

        # estado interno: active não pode acumular entradas mortas
        await page.evaluate("SonoPlay.stop()")
        await page.wait_for_timeout(300)

        # 4) fim natural: o handle precisa sair de active sozinho
        await page.evaluate('SonoPlay.play("window")')
        ended = None
        for _ in range(60):  # até 20s
            await page.wait_for_timeout(333)
            cur = await page.evaluate("SonoPlay.current")
            if cur is None:
                ended = True
                break
        print("limpeza após fim natural:", ended)

        # 5) dois tocando -> texto deve ser "2 tocando"
        await page.evaluate('SonoPlay.play("storm")')
        await page.wait_for_timeout(300)
        await page.evaluate('SonoPlay.play("sad")')
        await page.wait_for_timeout(300)
        status = await page.locator("#nowPlaying").inner_text()
        rms_two = await page.evaluate("SonoPlay.level()")
        print("status com 2 tocando:", repr(status), "| rms:", round(rms_two, 4))
        await page.evaluate("SonoPlay.stop()")

        print("errors:", errors)
        await browser.close()

asyncio.run(main())
