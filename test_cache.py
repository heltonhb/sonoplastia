"""Regressão: o áudio servido é o arquivo do disco (nunca uma cópia velha de cache).

Cobre o bug em que preloadAudio usava cache:"force-cache" e o navegador
entregava um MP3 antigo do cache HTTP sem ir à rede.
"""
import asyncio
import hashlib
from playwright.async_api import async_playwright

URL = "http://localhost:8765/index.html"

async def main():
    disk = hashlib.sha256(open("audio/08-melancolico.mp3", "rb").read()).hexdigest()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        audio_reqs = []
        page.on("request", lambda r: audio_reqs.append(r.url) if ".mp3" in r.url else None)
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error",) else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        # 1) todos os 8 áudios pedidos com o cache-buster ?v=7
        with_v = [u for u in audio_reqs if "v=7" in u]
        check_v = len(set(with_v)) >= 8

        # 2) os bytes que a página usa são idênticos aos do disco
        served = await page.evaluate("""async () => {
            const ab = await (await fetch('audio/08-melancolico.mp3?v=7', {cache:'no-cache'})).arrayBuffer();
            const d = await crypto.subtle.digest('SHA-256', ab);
            return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2,'0')).join('');
        }""")

        # 3) service worker v7 ativo e com a chave nova no cache
        sw = await page.evaluate("""async () => {
            const r = await navigator.serviceWorker.getRegistration();
            if (!r) return { reg: false };
            const keys = await caches.keys();
            const name = keys.find(k => k.startsWith('sonoplay')) || '';
            const hit = name ? await (await caches.open(name)).match('audio/08-melancolico.mp3?v=7') : null;
            const st = await r.installing ? 'installing' : (r.waiting ? 'waiting' : 'active');
            return { reg: true, keys, name, hasNew: !!hit, state: st };
        }""")

        # 4) o botão toca (RMS > 0)
        await page.evaluate('SonoPlay.play("sad")')
        await page.wait_for_timeout(1200)
        rms = await page.evaluate("SonoPlay.level()")
        await page.evaluate("SonoPlay.stop()")

        checks = {
            "8 áudios pedidos com ?v=7": check_v,
            "bytes servidos == bytes do disco": served == disk,
            "SW registrado": sw.get("reg", False),
            "cache do SW tem a chave ?v=7": sw.get("hasNew", False),
            "SW ativo": sw.get("state") == "active",
            "botão toca (RMS > 0.05)": rms > 0.05,
            "zero erros de console": errors == [],
        }
        print("sha disco :", disk[:16])
        print("sha página:", served[:16])
        print("sw        :", sw)
        print("audio reqs :", len(set(audio_reqs)))
        for k, v in checks.items():
            print(("  PASS  " if v else "  FAIL  ") + k)
        print("erros:", errors)
        await browser.close()
        assert all(checks.values()), "alguma checagem falhou"

asyncio.run(main())
