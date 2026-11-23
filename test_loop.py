"""Regressão: suspense em loop infinito + volume exclusivo dele."""
import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8765/index.html"
FILE_DUR = 11.0   # audio/03-suspense.mp3

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(3500)

        # 1) toca o suspense
        await page.evaluate('SonoPlay.play("sus")')
        await page.wait_for_timeout(1500)
        rms_start = await page.evaluate("SonoPlay.level()")
        cur_start = await page.evaluate("SonoPlay.current")
        has_badge = await page.locator('.fx[data-id="sus"] .loop-badge').count()
        has_tag = await page.locator(".loop-tag").count()

        # 2) espera PASSAR da duração do arquivo -> precisa continuar tocando
        await page.wait_for_timeout(int(FILE_DUR * 1000) + 2500)
        rms_after = await page.evaluate("SonoPlay.level()")
        cur_after = await page.evaluate("SonoPlay.current")
        btn_still_on = await page.locator('.fx[data-id="sus"]').get_attribute("class")

        # 3) volume só dele, em tempo real
        await page.evaluate("SonoPlay.setSusVolume(0.05)")
        await page.wait_for_timeout(600)
        rms_low = await page.evaluate("SonoPlay.level()")
        slider_val = await page.locator("#susVol").input_value()

        await page.evaluate("SonoPlay.setSusVolume(1)")
        await page.wait_for_timeout(600)
        rms_full = await page.evaluate("SonoPlay.level()")

        # 4) volume geral NÃO deve ter sido alterado
        master_val = await page.locator("#vol").input_value()

        # 5) para tudo
        await page.evaluate("SonoPlay.stop()")
        await page.wait_for_timeout(500)
        rms_stop = await page.evaluate("SonoPlay.level()")
        cur_stop = await page.evaluate("SonoPlay.current")

        checks = {
            "toca ao iniciar":            rms_start > 0.05 and cur_start == "sus",
            "badge ∞ no botão":           has_badge == 1 and has_tag == 1,
            "ainda toca após 13,5s (>11s do arquivo)": rms_after > 0.05 and cur_after == "sus"
                                                       and "playing" in (btn_still_on or ""),
            "volume baixo reduz o rms":   rms_low < rms_after * 0.5,
            "slider reflete o valor":     slider_val == "5",
            "volume cheio volta o rms":   rms_full > rms_low * 2,
            "volume geral intacto":       master_val == "80",
            "stop encerra o loop":        rms_stop < 0.05 and cur_stop is None,
            "sem erros de console":       errors == [],
        }
        print("rms: início=%.3f  após13,5s=%.3f  vol0.05=%.3f  vol1=%.3f  stop=%.3f"
              % (rms_start, rms_after, rms_low, rms_full, rms_stop))
        for k, v in checks.items():
            print(("  PASS  " if v else "  FAIL  ") + k)
        print("ERROS:", errors)
        await browser.close()
        assert all(checks.values()), "alguma checagem falhou"

asyncio.run(main())
