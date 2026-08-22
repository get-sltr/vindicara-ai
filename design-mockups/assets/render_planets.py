import math, numpy as np
from PIL import Image

W = H = 720
cx = cy = 360
R = 332

def octave_noise(w, h, base=6, octaves=6, seed=0, squash_y=1.0):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), dtype=np.float64)
    amp, total, f = 1.0, 0.0, base
    for _ in range(octaves):
        fw = max(2, int(f)); fh = max(2, int(f * squash_y))
        small = (rng.random((fh, fw)) * 255).astype(np.uint8)
        img = Image.fromarray(small).resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(img, dtype=np.float64) / 255.0)
        total += amp; amp *= 0.55; f *= 2
    return out / total

ys, xs = np.mgrid[0:H, 0:W].astype(np.float64)
nx = (xs - cx) / R
ny = (ys - cy) / R
r2 = nx * nx + ny * ny
mask = r2 <= 1.0
nz = np.sqrt(np.clip(1 - r2, 0, 1))
lat = np.arcsin(np.clip(ny, -1, 1))
lon = np.arctan2(nx, np.clip(nz, 1e-6, 1))

# lighting
L = np.array([-0.55, -0.45, 0.70]); L = L / np.linalg.norm(L)
diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
limb = np.clip(nz, 0, 1) ** 0.35
dist = np.sqrt(np.clip(r2, 0, 4))
alpha = np.clip((1.0 - dist) * R / 1.4 + 0.5, 0, 1) * mask

def shade(col, rim_rgb):
    light = (0.16 + 0.95 * diff)[..., None] * (0.55 + 0.45 * limb)[..., None]
    out = col * light
    rim = np.clip((dist - 0.72) / 0.28, 0, 1)[..., None] * (nz[..., None]) * np.array(rim_rgb)
    out = out + rim * 0.5
    return np.clip(out, 0, 255)

def save(rgb, name, extra_alpha=None):
    a = alpha if extra_alpha is None else np.clip(alpha + extra_alpha, 0, 1)
    arr = np.dstack([rgb, a * 255]).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(name)
    print("wrote", name)

# ---------- NEPTUNE ----------
t1 = octave_noise(W, H, base=5, octaves=6, seed=1, squash_y=0.18)
t2 = octave_noise(W, H, base=10, octaves=5, seed=7, squash_y=0.25)
bands = np.sin(lat * 7.5 + (t1 - 0.5) * 3.2)
inten = np.clip(0.5 + 0.34 * bands + 0.16 * (t2 - 0.5), 0, 1)
deep = np.array([18, 38, 104]); lite = np.array([96, 156, 232])
col = deep + (lite - deep) * inten[..., None]
# Great Dark Spot
d = ((lon + 0.55) / 0.42) ** 2 + ((lat - 0.32) / 0.22) ** 2
spot = np.exp(-d * 1.6)
col = col * (1 - 0.55 * spot[..., None])
# bright cloud streaks
clouds = np.clip((t2 - 0.80) / 0.20, 0, 1) * np.clip(1 - np.abs(lat - 0.30) / 0.5, 0, 1)
col = col + clouds[..., None] * np.array([210, 225, 245]) * 0.7
save(shade(col, [90, 140, 220]), "neptune.png")

# ---------- MARS ----------
m1 = octave_noise(W, H, base=7, octaves=6, seed=21)
m2 = octave_noise(W, H, base=14, octaves=5, seed=33)
inten = np.clip(0.45 + 0.5 * (m1 - 0.5) + 0.25 * (m2 - 0.5), 0, 1)
dark = np.array([96, 38, 20]); lite = np.array([214, 128, 78])
col = dark + (lite - dark) * inten[..., None]
# dark albedo features
alb = np.clip((0.42 - m1) / 0.42, 0, 1)
col = col * (1 - 0.4 * alb[..., None])
# polar ice caps
cap = np.clip((np.abs(lat) - 1.05) / 0.4, 0, 1)
col = col + cap[..., None] * (np.array([235, 240, 245]) - col) * 0.85
save(shade(col, [200, 110, 70]), "mars.png")

# ---------- SATURN (with rings) ----------
s1 = octave_noise(W, H, base=5, octaves=6, seed=4, squash_y=0.14)
bands = np.sin(lat * 12 + (s1 - 0.5) * 1.6)
inten = np.clip(0.55 + 0.32 * bands + 0.12 * (s1 - 0.5), 0, 1)
dark = np.array([150, 116, 60]); lite = np.array([240, 218, 165])
col = dark + (lite - dark) * inten[..., None]
planet_rgb = shade(col, [220, 185, 110])

# ring system in tilted plane (vertical squash)
tilt = 0.34
rr = np.sqrt(nx * nx + (ny / tilt) ** 2)
ring_a = np.zeros((H, W))
def ringband(lo, hi, a):
    global ring_a
    band = ((rr >= lo) & (rr < hi))
    ring_a = np.where(band, a, ring_a)
ringband(1.22, 1.50, 0.55)   # C ring
ringband(1.50, 1.70, 0.92)   # B ring
ringband(1.70, 1.74, 0.15)   # Cassini division
ringband(1.74, 2.02, 0.78)   # A ring
ring_col = np.dstack([
    np.full((H, W), 224.0), np.full((H, W), 206.0), np.full((H, W), 158.0)
])
# subtle radial shading on rings
rshade = np.clip(1 - (rr - 1.2) * 0.22, 0.6, 1)[..., None]
ring_col = ring_col * rshade
in_planet = r2 <= 1.0
# back rings: above center, outside planet
back = (ring_a > 0) & (ny < 0) & (~in_planet)
# front rings: below center (cross planet + sides)
front = (ring_a > 0) & (ny >= 0)

canvas = np.zeros((H, W, 3))
ca = np.zeros((H, W))
# 1 back rings
canvas = np.where(back[..., None], ring_col, canvas)
ca = np.where(back, ring_a, ca)
# 2 planet over
canvas = np.where(in_planet[..., None], planet_rgb, canvas)
ca = np.where(in_planet, alpha, ca)
# 3 front rings over planet
fa = ring_a
canvas = np.where(front[..., None], ring_col * fa[..., None] + canvas * (1 - fa[..., None]), canvas)
ca = np.clip(np.where(front, np.maximum(ca, ring_a), ca), 0, 1)
arr = np.dstack([np.clip(canvas, 0, 255), ca * 255]).astype(np.uint8)
Image.fromarray(arr, "RGBA").save("saturn.png")
print("wrote saturn.png")
