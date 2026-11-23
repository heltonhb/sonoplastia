"""
Enhance SonoPlay audio:
1) storm: add rain + more thunder
2) door: "arrombada" (broken/slam)
3) window: more rangido (creaking)

Design goal: keep original spirit, just make the requested layers stronger,
then re-normalize to the same loudness spec the app uses.
"""
import numpy as np
import scipy.signal as signal
import subprocess, os

ROOT = "/home/helton/sonoplastia"
AUDIO = os.path.join(ROOT, "audio")
SR = 44100

def load_mono_44100(name):
    p = os.path.join(AUDIO, name)
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"], capture_output=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"decode {name}: {r.stderr.decode()}")
    n = len(r.stdout) // 4
    return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)[:n]

def save_stereo(name, data_mono):
    # encode back to MP3 so the app's decoder (and preload) reads it correctly
    stereo = np.column_stack([data_mono, data_mono]).astype(np.float32)
    p = os.path.join(AUDIO, name)
    # write raw f32le to a temp file, ffmpeg -> mp3
    raw = p + ".raw"
    with open(raw, "wb") as f:
        f.write(stereo.tobytes())
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-f", "f32le", "-ar", str(SR), "-ac", "2",
        "-i", raw,
        "-codec:a", "libmp3lame", "-b:a", "192k",
        "-ac", "2", "-ar", "44100", p
    ], check=True)
    os.remove(raw)

def bandpass(x, lo, hi, q=0.7):
    sos = signal.butter(4, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def lowpass(x, hi, q=0.7):
    sos = signal.butter(4, hi, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def highpass(x, lo, q=0.7):
    sos = signal.butter(4, lo, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def fade(x, t0, t1):
    """Fade in from t0 and out at t1 (both in seconds)."""
    n = len(x)
    a = np.ones(n)
    if t0 > 0:
        a[:int(t0*SR)] = np.linspace(0, 1, int(t0*SR))
    if t1 is not None:
        a[int(t1*SR):] = np.linspace(1, 0, n - int(t1*SR))
    return x * a

def lfo_amp(x, rate, depth, t0=0.0, t1=None):
    """Shimmer the amplitude with a sine LFO starting at t0."""
    if t1 is None: t1 = len(x)/SR
    t = np.arange(len(x)) / SR
    env = np.ones(len(x))
    start = int(t0*SR)
    end = min(int(t1*SR), len(env))
    if end > start:
        seg = 1 + depth * np.sin(2*np.pi*rate*np.arange(start, end)/SR)
        env[start:end] = seg
    return x * np.clip(env, 0, None)

def mix_all(base, layers, vol=1.0, dur=None):
    """mix layers onto base (which sets the original duration)."""
    n = len(base) if dur is None else int(dur*SR)
    out = base.copy()[:n] * vol
    for sig, g in layers:
        if len(sig) == 0:
            continue
        s = sig.copy()
        if len(s) > n:
            s = s[:n]
        else:
            s = np.pad(s, (0, n-len(s)))
        out = out + s * g
    return np.clip(out, -1, 1)

# ============================================================
# 1) TEMPESTADE (storm) — add rain + more thunder
# ============================================================
storm = load_mono_44100("01-tempestade.mp3")
D = len(storm)/SR
t0 = 0.04

# --- new rain layers (not present before) ---
rain_lo = np.random.randn(int((D+0.5)*SR)).astype(np.float64)
rain_lo = bandpass(rain_lo, 700, 1800, q=0.8)
rain_lo = lfo_amp(rain_lo, 0.45, 0.22)          # slow wind variability
rain_lo = fade(rain_lo, t0, D)

rain_hi = np.random.randn(int((D+0.5)*SR)).astype(np.float64)
rain_hi = bandpass(rain_hi, 2200, 4800, q=0.7)
rain_hi = fade(rain_hi, t0+0.4, D)

# --- thunder rumbles (was only two subtle ones) ---
def thunder(dur):
    s = np.random.randn(int(max(dur, 1.2)*SR)).astype(np.float64)
    s = lowpass(s, 140, q=0.5)                    # sub/low rumble
    s = lfo_amp(s, 0.3, 0.25)                     # irregular swell
    s = fade(s, 0.0, dur)
    return s

t1 = np.zeros(int(D*SR))
for off, d in [(1.6, 2.0), (4.7, 2.2), (7.4, 1.6)]:
    seg = thunder(d)
    start = int(off*SR)
    ns = min(len(seg), int((D-off)*SR))
    t1[start:start+ns] += seg[:ns]

# --- mix all ---
storm = mix_all(storm, [(rain_lo, 0.30), (rain_hi, 0.14), (t1, 1.0)], vol=1.0, dur=D)
storm = np.clip(storm, -1, 1)
save_stereo("01-tempestade.mp3", storm)

# ============================================================
# 2) PORTA (door) — arrombada (broken/slam)
# ============================================================
door = load_mono_44100("07-porta.mp3")
D = len(door)/SR

# body slam — deep, abrupt, low
slam = np.random.randn(int(0.6*SR)).astype(np.float64)
slam = highpass(slam, 120, q=1.0)
slam = lowpass(slam, 250, q=0.4)
slam = lfo_amp(slam, 4.0, 0.3)                     # tremble
slam = fade(slam, 0.0, 0.25)
slam = np.concatenate([slam, np.random.randn(int(0.3*SR)).astype(np.float64)])
slam = lowpass(slam, 220, q=0.5)

# add a violent low thump at the start (broken door hits hard)
# build a 0.5s buffer and then a "stuck" clicks layer at off>0
thump = np.zeros(int(0.5*SR))
for f0 in [120, 70, 40]:
    o = np.zeros(int(0.45*SR))
    tt = np.arange(len(o))/SR
    env = np.exp(-tt*1.2)
    o += np.sin(2*np.pi*f0*tt) * env
thump = np.concatenate([thump, o])
thump = np.clip(thump, -1, 1)

# "stuck" clicks placed at off>0 (we need a longer buffer for these)
extra = np.zeros(int((D+0.5)*SR))
for off, dur in [(1.8, 0.12), (2.4, 0.1)]:
    c = np.random.randn(int(dur*SR)).astype(np.float64)
    c = bandpass(c, 2500, 6000, q=1.5)
    c = fade(c, 0.0, dur)
    start = int(off*SR)
    ns = min(len(c), int((D-off)*SR))
    extra[start:start+ns] += c[:ns]

# screech / metal scrape (broken handle, more noise)
screech = np.random.randn(int(1.6*SR)).astype(np.float64)
screech = bandpass(screech, 1800, 5000, q=1.4)
screech = lfo_amp(screech, 6.0, 0.25)
screech = fade(screech, 0.0, 1.0)

# mix (preserve original duration D)
door = mix_all(door, [(slam, 0.6), (thump, 1.0), (screech, 0.55), (extra, 0.9)], vol=1.0, dur=D)
door = np.clip(door, -1, 1)
save_stereo("07-porta.mp3", door[:int(D*SR)])

# ============================================================
# 3) JANELA (window) — mais rangido (more creaking)
# ============================================================
win = load_mono_44100("05-janela.mp3")
D = len(win)/SR

# friction base layer (continuous)
fric = np.random.randn(int((D+0.3)*SR)).astype(np.float64)
fric = bandpass(fric, 800, 1600, q=0.8)
fric = lfo_amp(fric, 0.5, 0.2)
fric = fade(fric, 0.0, D)

# sliding brushstrokes: several contacts across the slide
for i, off in enumerate([0.12, 0.27, 0.42, 0.57, 0.72, 0.85]):
    dur = 0.35
    s = np.random.randn(int(dur*SR)).astype(np.float64)
    s = bandpass(s, 1000, 2000, q=1.0)
    tt = np.arange(len(s))/SR
    f = 900 + 700*np.sin(np.pi*np.clip(tt/0.3, 0, 1))   # 900 -> 1600 -> ~back
    f = np.interp(f, (900, 1600), (0.05, 1.0))
    phase = 2*np.pi*np.cumsum(f)*SR
    s = np.sin(phase)
    s = bandpass(s, 1000, 2000, q=1.0)
    s = lfo_amp(s, 5.0, 0.25, t0=off)   # tremble during stroke
    vol = 0.16 * (1 - i*0.02)
    ns = min(len(s), int((D-off)*SR))
    seg = s[:ns]
    needed = int((off+dur)*SR)
    if len(win) < needed:
        win = np.pad(win, (0, needed - len(win)))
    win[int(off*SR):int(off*SR)+ns] += seg*vol

# more body resonance (ring longer)
ring = np.random.randn(int(2.0*SR)).astype(np.float64)
ring = lowpass(ring, 900, q=0.5)
ring = fade(ring, 0.0, 1.2)
ns = min(len(ring), int(D*SR))
ring = ring[:ns]
# trim or extend win to exactly match the ring length
if len(win) > ns:
    win = win[:ns]
elif len(win) < ns:
    win = np.pad(win, (0, ns - len(win)))
win = win + ring*0.15

win = np.clip(win, -1, 1)
save_stereo("05-janela.mp3", win)

print("ALL DONE")
