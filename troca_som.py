"""
Atualiza um efeito sonoro do SonoPlay com um só comando.

Uso:
  python3 troca_som.py <origem> <alvo> [--dur SEG] [--inicio SEG]

Exemplos:
  python3 troca_som.py ~/Downloads/nova-porta.mp3 07-porta
  python3 troca_som.py baixa.wav 03-suspense --dur 11
  python3 troca_som.py trilha.mp3 08 --inicio 38 --dur 12

<alvo> é o efeito: "07", "07-porta" ou "07-porta.mp3" (os 8 de audio/).

O que ele faz, nesta ordem:
  1) processa o áudio na especificação do app (compressor leve + loudnorm
     linear −18 LUFS / −2 dBTP + MP3 192 kbps / 44,1 kHz estéreo), com corte
     opcional via --inicio/--dur
  2) faz backup do arquivo atual em audio_original_backup/
  3) grava audio/<alvo>.mp3
  4) incrementa AUDIO_VER (index.html) e V + CACHE (sw.js) — SEM ISSO o
     celular fica com o áudio antigo preso no cache
  5) imprime os próximos passos (teste e publicação)

Depois é só testar e publicar:
  python3 test_cache.py
  git add -A && git commit -m "troca o efeito <alvo>" && git push
"""
import argparse
import glob
import os
import re
import shutil
import sys
from datetime import date

import make_melancolico as chain

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(ROOT, "audio")
BACKUP = os.path.join(ROOT, "audio_original_backup")


def resolve_target(arg):
    """aceita '07', '07-porta' ou '07-porta.mp3' -> caminho completo em audio/"""
    arg = arg.removesuffix(".mp3")
    hits = sorted(glob.glob(os.path.join(AUDIO, arg + "*.mp3")))
    # prioriza casamento exato do prefixo
    exact = [h for h in hits if os.path.basename(h)[:-4] == arg]
    if exact:
        return exact[0]
    if len(hits) == 1:
        return hits[0]
    if hits:
        print("ambíguo, escolha um destes:")
        for h in hits:
            print("  ", os.path.basename(h))
        sys.exit(1)
    print(f"nenhum efeito corresponde a {arg!r}; disponíveis:")
    for h in sorted(glob.glob(os.path.join(AUDIO, "*.mp3"))):
        print("  ", os.path.basename(h))
    sys.exit(1)


def bump(path, pattern, label):
    """incrementa um número entre aspas/parênteses no arquivo"""
    src = open(path, encoding="utf-8").read()
    m = re.search(pattern, src)
    if not m:
        print(f"  !! não achei {label} em {os.path.basename(path)} — bump manual!")
        return None
    n = int(m.group(1)) + 1
    out = src[:m.start(1)] + str(n) + src[m.end(1):]
    open(path, "w", encoding="utf-8").write(out)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("origem", help="arquivo de áudio novo (mp3, wav, m4a…)")
    ap.add_argument("alvo", help="qual efeito: 07 | 07-porta | 07-porta.mp3")
    ap.add_argument("--dur", type=float, help="corta para N segundos")
    ap.add_argument("--inicio", type=float, help="começa em N segundos da origem")
    a = ap.parse_args()

    if not os.path.exists(a.origem):
        sys.exit(f"arquivo não encontrado: {a.origem}")
    destino = resolve_target(a.alvo)

    # 1) backup do atual
    os.makedirs(BACKUP, exist_ok=True)
    base = os.path.basename(destino)
    bak = os.path.join(BACKUP, f"{base[:-4]}.anterior-{date.today():%Y%m%d}.mp3")
    shutil.copy2(destino, bak)
    print(f"backup: {os.path.relpath(bak, ROOT)}")

    # 2) processa e grava por cima
    chain.process(a.origem, destino, start=a.inicio, dur=a.dur)

    # 3) quebra de cache (obrigatório)
    v1 = bump(os.path.join(ROOT, "index.html"), r'const AUDIO_VER = "(\d+)"', "AUDIO_VER")
    v2 = bump(os.path.join(ROOT, "sw.js"), r'const CACHE = "sonoplay-v(\d+)"', "CACHE")
    v3 = bump(os.path.join(ROOT, "sw.js"), r'const V = "\?v=(\d+)"', "V")
    print(f"cache: AUDIO_VER={v1} · CACHE=sonoplay-v{v2} · V=?v={v3}")

    print("""
próximo:
  1) python3 test_cache.py            # confere disco == o que a página usa
  2) python3 test_sonoplay.py         # 8/8 ainda tocam
  3) git add -A && git commit -m "troca o efeito %s" && git push
     (publica no GitHub Pages em ~1 min)
  4) no celular: reabra o app — o ?v novo força o download do áudio novo
""" % os.path.basename(destino))


if __name__ == "__main__":
    main()
