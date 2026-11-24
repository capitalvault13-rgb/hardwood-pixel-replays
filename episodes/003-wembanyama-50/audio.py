"""Chiptune bed + SFX for Pixel Replay #003. Event times come from replay.py's timeline."""
import numpy as np, wave, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay as R

SR = 48000; D = R.DUR; N = int(SR * D); out = np.zeros(N)
rng = np.random.default_rng(3)
def sq(f, dur, duty=0.5):
    t = np.arange(int(SR * dur)) / SR; return np.where((t * f) % 1 < duty, 1.0, -1.0)
def env(n, a=0.005, r=0.08):
    e = np.ones(n); na = int(a * SR); nr = min(int(r * SR), n)
    if na: e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr); return e
def add(sig, t, g):
    i = int(t * SR); j = min(N, i + len(sig))
    if 0 <= i < N: out[i:j] += sig[:j - i] * g
def lp(x, a):
    y = np.zeros_like(x); s = 0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
note = lambda m: 440 * 2 ** ((m - 69) / 12)
def thud(t, f0, f1, g, dur):
    s = np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, int(dur * SR))) / SR)
    add(s * env(len(s), 0.002, dur * 0.8), t, g)
def whoosh(t, dur=0.5, g=1.0):
    n = rng.standard_normal(int(dur * SR)); n = lp(n, 0.08) * np.sin(np.linspace(0, np.pi, len(n))); add(n, t, g)
def crowd(t, dur, g):
    n = rng.standard_normal(int(dur * SR)); c = lp(n, 0.05)
    e = np.minimum(1, np.arange(len(c)) / (0.25 * SR)) * np.exp(-np.arange(len(c)) / SR / (dur / 2.5))
    add(c * e, t, g)
def clang(t, f0, g):
    tt = np.arange(int(0.5 * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * tt) + 0.6 * np.sin(2 * np.pi * f0 * 2.4 * tt)) * np.exp(-tt * 8)
    add(s, t, g)

# music bed: 120 bpm, A minor; lighter under the stat cards
beat = 0.5; step = beat / 2
prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (43, [55, 59, 62]), (40, [52, 56, 59])]
t = 0.0; k = 0
while t < D - 0.3:
    root, ch = prog[int(t / (beat * 4)) % 4]
    card = (R.T_D <= t < R.T_E) or t >= R.T_F
    g = 0.10 if card else 0.15
    if k % 2 == 0: s = sq(note(root), step * 0.9); add(s * env(len(s), 0.003, 0.05), t, g)
    m = ch[k % 3] + 12 + (12 if (R.T_MAKE <= t < R.T_F and k % 4 == 3) else 0)
    s = sq(note(m), step * 0.6, 0.25); add(s * env(len(s), 0.002, 0.06), t, g * 0.45)
    t += step; k += 1
t = 0
while t < D - 0.2:
    n = rng.standard_normal(int(0.03 * SR)); n = n - lp(n, 0.3); add(n * env(len(n), 0.001, 0.025), t, 0.04); t += step

# dribbles on the drive (run1 = ball on the floor)
f = 3
while R.T_B + f / R.FPS < R.T_RUN_END:
    thud(R.T_B + f / R.FPS, 170, 70, 0.45, 0.09); f += 12
# slam: rim rattle + thump + crowd
clang(R.T_SLAM, 380, 0.4); thud(R.T_SLAM, 110, 40, 0.7, 0.25); crowd(R.T_SLAM, 2.2, 1.8)
# block
whoosh(R.T_SREL, 0.3, 0.8); clang(R.T_SWAT, 700, 0.25); thud(R.T_SWAT, 140, 50, 0.6, 0.18); crowd(R.T_SWAT, 1.6, 1.2)
# halftime count-up ticks
for i in range(8):
    s = sq(note(76 + i), 0.04); add(s * env(len(s), 0.002, 0.02), R.T_D + 0.3 + i * 1.0 / 8, 0.1)
# the 50th point
whoosh(R.T_REL, 0.7, 1.0)
n = rng.standard_normal(int(0.35 * SR)); sw = n - lp(n, 0.2); add(sw * env(len(sw), 0.003, 0.3), R.T_MAKE, 0.35)
crowd(R.T_MAKE, 4.0, 2.4)
for i, m in enumerate([72, 76, 79, 84]):
    s = sq(note(m), 0.09); add(s * env(len(s), 0.002, 0.05), R.T_MAKE + 0.05 + i * 0.07, 0.14)
# caption blips
for tc in [c[0] for c in R.CAPS]:
    s = np.concatenate([sq(note(84), 0.05), sq(note(91), 0.07)]); add(s * env(len(s), 0.002, 0.03), tc + 0.02, 0.1)
# end sting
for i, m in enumerate([79, 84]):
    s = sq(note(m), 0.12); add(s * env(len(s), 0.002, 0.08), R.T_I + 1.0 + i * 0.12, 0.14)
out[-int(0.4 * SR):] *= np.linspace(1, 0, int(0.4 * SR))
out /= np.abs(out).max() * 1.12
w = wave.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio.wav'), 'wb')
w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
