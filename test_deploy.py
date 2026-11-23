"""E2E no app PUBLICADO: HTTPS + service worker + som + modo avião (offline)."""
import asyncio
from playwright.async_api import async_playwright

URL = "https://heltonhb.github.io/sonoplastia/"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # viewport de celular Android
        page = await browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        errors = []
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        # ---- 1) primeira visita (online) ----
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(6000)   # dá tempo do SW instalar e precachear
        loaded = await page.evaluate("SonoPlay.loaded")
        sw = await page.evaluate("""async () => {
            const r = await navigator.serviceWorker.getRegistration();
            const controlled = !!navigator.serviceWorker.controller;
            const keys = await caches.keys();
            return { has: !!r, controlled, keys,
                     active: r && r.active ? r.active.state : null };
        }""")
        await page.evaluate('SonoPlay.play("storm")')
        await page.wait_for_timeout(1500)
        rms_online = await page.evaluate("SonoPlay.level()")
        await page.evaluate("SonoPlay.stop()")

        # ---- 2) MODO AVIÃO: recarrega tudo sem rede ----
        await page.context.set_offline(True)
        await page.reload(wait_until="load")
        await page.wait_for_timeout(5000)
        loaded_off = await page.evaluate("SonoPlay.loaded")
        await page.evaluate('SonoPlay.play("sad")')
        await page.wait_for_timeout(1500)
        rms_off = await page.evaluate("SonoPlay.level()")
        cur_off = await page.evaluate("SonoPlay.current")
        await page.evaluate("SonoPlay.stop()")
        # suspense em loop também offline
        await page.evaluate('SonoPlay.play("sus")')
        await page.wait_for_timeout(1200)
        rms_off_sus = await page.evaluate("SonoPlay.level()")
        await page.evaluate("SonoPlay.stop()")
        await page.context.set_offline(False)

        checks = {
            "HTTPS é contexto seguro (SW registrou)": sw["has"] and sw["active"] == "activated",
            "SW controla a página": sw["controlled"],
            "cache do SW criado": any(k.startswith("sonoplay") for k in sw["keys"]),
            "8/8 sons decodificados (online)": loaded["state"] == "done" and loaded["buffers"] == 8,
            "toca online": rms_online > 0.05,
            "MODO AVIÃO: 8/8 sons vêm do cache": loaded_off["state"] == "done" and loaded_off["buffers"] == 8,
            "MODO AVIÃO: toca (storm…sad)": rms_off > 0.05 and cur_off == "sad",
            "MODO AVIÃO: suspense em loop toca": rms_off_sus > 0.05,
            "zero erros de console": errors == [],
        }
        print("sw:", sw)
        print("rms online=%.3f · offline sad=%.3f · offline sus=%.3f" % (rms_online, rms_off, rms_off_sus))
        for k, v in checks.items():
            print(("  PASS  " if v else "  FAIL  ") + k)
        print("erros:", errors[:5])
        await browser.close()
        assert all(checks.values()), "alguma checagem falhou"

asyncio.run(main())
