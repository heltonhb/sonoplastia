"""
Gera o 08-melancolico.mp3 a partir da trilha Mixkit 614 "Silent Descent"
(Eugenio Mininni — Mixkit Stock Music Free License).

Uso:
  python3 make_melancolico.py <inicio_seg> <saida.mp3>

Aplica a mesma cadeia do resto do app (ver CREDITS.md):
  1) corte de 12 s
  2) compressor leve  acompressor=threshold=-26dB:ratio=5:attack=1:release=140
  3) loudnorm 2 passos, linear, alvo -18 LUFS / -2 dBTP
  4) MP3 192 kbps / 44,1 kHz / estéreo

Fonte (rebaixável):
  https://assets.mixkit.co/music/614/614.mp3
"""
import json
import os
import subprocess
import sys
import tempfile

SRC = "/tmp/opencode/614.mp3"
SRC_URL = "https://assets.mixkit.co/music/614/614.mp3"
CUT = 12.0


def run(args, **kw):
    return subprocess.run(args, check=True, capture_output=True, **kw)


def process(src, out, start=None, dur=None):
    """Corta (opcional) e aplica a cadeia padrão do app -> MP3 192k/44,1 estéreo.

    Retorna o dicionário de medição do loudnorm final.
    """
    with tempfile.TemporaryDirectory() as td:
        cut = os.path.join(td, "cut.wav")
        cmd = ["ffmpeg", "-v", "error", "-y"]
        if start is not None:
            cmd += ["-ss", str(start)]
        if dur is not None:
            cmd += ["-t", str(dur)]
        cmd += ["-i", src, "-ar", "44100", "-ac", "2", cut]
        run(cmd)

        # passo 1: medir loudness do trecho cortado
        m = run(["ffmpeg", "-v", "info", "-i", cut,
                 "-af",
                 "acompressor=threshold=-26dB:ratio=5:attack=1:release=140,"
                 "loudnorm=I=-18:TP=-2:LRA=11:print_format=json",
                 "-f", "null", "-"]).stderr.decode()
        j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])

        # passo 2: aplicar em modo linear com as medições
        run(["ffmpeg", "-v", "error", "-y", "-i", cut,
             "-af",
             "acompressor=threshold=-26dB:ratio=5:attack=1:release=140,"
             "loudnorm=I=-18:TP=-2:LRA=11:linear=true:"
             f"measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
             f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:"
             f"offset={j['target_offset']}",
             "-ar", "44100", "-ac", "2",
             "-codec:a", "libmp3lame", "-b:a", "192k", out])

    r = run(["ffmpeg", "-v", "info", "-i", out,
             "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr.decode()
    final = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    print(f"{out}: {final['input_i']} LUFS · pico {final['input_tp']} dBTP · "
          f"{os.path.getsize(out)//1024} KB")
    return final


def main():
    start = float(sys.argv[1])
    out = sys.argv[2]
    if not os.path.exists(SRC):
        run(["curl", "-sSL", "-m", "90", "-A", "Mozilla/5.0", SRC_URL, "-o", SRC])
    process(SRC, out, start=start, dur=CUT)


if __name__ == "__main__":
    main()
