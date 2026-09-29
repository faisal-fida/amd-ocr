"""Generates a harder synthetic test set: hard/<category>_<n>.<ext> + hard/expected.json.

Covers every category in the MC2 brief (US plates with state names and slogans,
Chinese plates, stop signs, speed limits, advisory plaques, multi-line warning
signs) under the listed adverse conditions: noise, blur, glare, low light and
off-axis angles, plus JPEG damage, low resolution and very large inputs.
Usage: python3 make_hard.py [per_category] [seed]
"""
import json
import os
import random
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_URL = "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
FONT_PATH = "NotoSansSC.ttf"

US_STATES = [
    ("CALIFORNIA", "", (190, 30, 45), (30, 40, 120)),
    ("TEXAS", "THE LONE STAR STATE", (20, 20, 20), (20, 20, 20)),
    ("NEW YORK", "EXCELSIOR", (30, 50, 130), (30, 50, 130)),
    ("FLORIDA", "SUNSHINE STATE", (230, 110, 20), (20, 110, 60)),
    ("ILLINOIS", "LAND OF LINCOLN", (180, 30, 40), (30, 30, 120)),
    ("OHIO", "BIRTHPLACE OF AVIATION", (180, 30, 40), (20, 30, 90)),
    ("ARIZONA", "GRAND CANYON STATE", (130, 40, 30), (20, 60, 40)),
    ("NEVADA", "THE SILVER STATE", (30, 50, 110), (30, 50, 110)),
    ("COLORADO", "", (20, 90, 40), (20, 90, 40)),
    ("GEORGIA", "PEACH STATE", (20, 20, 20), (20, 20, 20)),
    ("MICHIGAN", "PURE MICHIGAN", (20, 40, 110), (20, 40, 110)),
    ("WASHINGTON", "EVERGREEN STATE", (20, 60, 120), (20, 60, 120)),
]
US_FORMATS = ["DLLLDDD", "LLL DDDD", "LLL-DDDD", "DDD LLL", "LLD DDDD", "DLLDDD"]
PROVINCES = "京沪津渝冀晋辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云陕甘青宁"
CN_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # plates skip I and O
WARNINGS = [
    ["ROAD", "WORK", "AHEAD"], ["BRIDGE", "ICES BEFORE", "ROAD"], ["DETOUR"],
    ["RIGHT LANE", "ENDS"], ["SLOW", "TRAFFIC", "AHEAD"], ["ICY", "BRIDGE"],
    ["BE PREPARED", "TO STOP"], ["FLAGGER", "AHEAD"], ["LEFT LANE", "CLOSED", "AHEAD"],
    ["UNEVEN", "LANES"], ["ONE LANE", "ROAD", "AHEAD"], ["END", "ROAD WORK"],
]


def font(size, weight="Bold"):
    f = ImageFont.truetype(FONT_PATH, size)
    f.set_variation_by_name(weight)
    return f


def fill_pattern(pattern):
    L = "ABCDEFGHJKLMNPRSTUVWXYZ"
    return "".join(random.choice(L) if c == "L" else random.choice("0123456789") if c == "D" else c
                   for c in pattern)


def centered(draw, y, text, f, color, width, margin=30):
    # Shrink the font until the text fits inside the plate or sign.
    while draw.textlength(text, font=f) > width - 2 * margin and f.size > 12:
        f = font(int(f.size * 0.92))
    w = draw.textlength(text, font=f)
    draw.text(((width - w) / 2, y), text, font=f, fill=color)


def on_background(img, pad=60):
    bg = Image.new("RGB", (img.width + 2 * pad, img.height + 2 * pad),
                   tuple(random.randint(70, 140) for _ in range(3)))
    bg.paste(img, (pad, pad))
    return bg


def us_plate():
    state, slogan, top_color, num_color = random.choice(US_STATES)
    number = fill_pattern(random.choice(US_FORMATS))
    img = Image.new("RGB", (600, 300), (245, 245, 240))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4, 4, 595, 295), radius=24, outline=(40, 40, 40), width=6)
    centered(d, 18, state, font(52), top_color, 600)
    centered(d, 80, number, font(130), num_color, 600)
    if slogan:
        centered(d, 238, slogan, font(30, "Regular"), top_color, 600)
    return on_background(img), number


def cn_plate():
    number = random.choice(PROVINCES) + random.choice(CN_LETTERS) + "·" + fill_pattern(
        random.choice(["DDDDD", "LDDDD", "DDDDL", "LLDDD", "DLDDD"]))
    img = Image.new("RGB", (660, 200), (20, 70, 170))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, 651, 191), radius=12, outline=(240, 240, 240), width=5)
    centered(d, 20, number, font(120), (245, 245, 245), 660)
    return on_background(img), number


def stop_sign():
    img = Image.new("RGB", (500, 500), (230, 235, 230))
    d = ImageDraw.Draw(img)
    r, c = 230, 250
    pts = [(c + r * np.cos(np.pi / 8 + k * np.pi / 4), c + r * np.sin(np.pi / 8 + k * np.pi / 4)) for k in range(8)]
    d.polygon(pts, fill=(180, 25, 35), outline=(250, 250, 250), width=10)
    centered(d, 165, "STOP", font(140), (250, 250, 250), 500)
    return on_background(img), "STOP"


def speed_limit():
    n = random.choice(range(15, 80, 5))
    img = Image.new("RGB", (400, 520), (250, 250, 250))
    d = ImageDraw.Draw(img)
    d.rectangle((12, 12, 387, 507), outline=(20, 20, 20), width=8)
    centered(d, 30, "SPEED", font(84), (20, 20, 20), 400)
    centered(d, 130, "LIMIT", font(84), (20, 20, 20), 400)
    centered(d, 250, str(n), font(200), (20, 20, 20), 400)
    return on_background(img), f"SPEED LIMIT {n}"


def advisory():
    n = random.choice(range(10, 60, 5))
    img = Image.new("RGB", (400, 400), (245, 195, 30))
    d = ImageDraw.Draw(img)
    d.rectangle((14, 14, 385, 385), outline=(20, 20, 20), width=10)
    centered(d, 70, str(n), font(210), (20, 20, 20), 400)
    return on_background(img), str(n)


def warning():
    lines = random.choice(WARNINGS)
    color = random.choice([(245, 145, 30), (245, 200, 30)])
    size = 560
    img = Image.new("RGB", (size, size), (230, 235, 230))
    d = ImageDraw.Draw(img)
    c = size / 2
    d.polygon([(c, 10), (size - 10, c), (c, size - 10), (10, c)], fill=color, outline=(20, 20, 20), width=8)
    fsize = 64 if max(len(l) for l in lines) <= 7 else 46
    f = font(fsize)
    total = len(lines) * fsize * 1.15
    for i, line in enumerate(lines):
        centered(d, c - total / 2 + i * fsize * 1.15 - fsize * 0.2, line, f, (20, 20, 20), size)
    return on_background(img), " ".join(lines)


# ---- degradations ---------------------------------------------------------

def perspective(img):
    w, h = img.size
    j = lambda s: random.uniform(0, s)
    dst = [(j(0.18 * w), j(0.18 * h)), (w - j(0.18 * w), j(0.18 * h)),
           (w - j(0.18 * w), h - j(0.18 * h)), (j(0.18 * w), h - j(0.18 * h))]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        b += [u, v]
    coeffs = np.linalg.solve(np.array(A, float), np.array(b, float))
    return img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC, fillcolor=(90, 90, 90))


def motion_blur(img):
    k = random.randint(7, 21)
    a = np.asarray(img).astype(np.float32)
    axis = random.choice([0, 1])
    c = np.cumsum(np.pad(a, [(k, 0) if i == axis else (0, 0) for i in range(3)], mode="edge"), axis=axis)
    out = (np.take(c, range(k, c.shape[axis]), axis=axis) - np.take(c, range(0, c.shape[axis] - k), axis=axis)) / k
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def noise(img):
    a = np.asarray(img).astype(np.float32)
    return Image.fromarray((a + np.random.normal(0, random.uniform(20, 45), a.shape)).clip(0, 255).astype(np.uint8))


def low_light(img):
    a = np.asarray(img).astype(np.float32) / 255
    a = a ** random.uniform(1.8, 2.8) * random.uniform(0.35, 0.6)
    return Image.fromarray((a * 255).clip(0, 255).astype(np.uint8))


def glare(img):
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    cy, cx = random.uniform(0.2, 0.8) * h, random.uniform(0.2, 0.8) * w
    r = random.uniform(0.25, 0.5) * max(h, w)
    yy, xx = np.mgrid[0:h, 0:w]
    spot = np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * r * r)))[..., None]
    return Image.fromarray((a + spot * random.uniform(120, 200)).clip(0, 255).astype(np.uint8))


DEGRADATIONS = {
    "blur": lambda im: im.filter(ImageFilter.GaussianBlur(random.uniform(2, 4))),
    "motion": motion_blur,
    "noise": noise,
    "lowlight": low_light,
    "glare": glare,
    "angle": perspective,
    "rotate": lambda im: im.rotate(random.uniform(-15, 15), Image.BICUBIC, expand=True, fillcolor=(90, 90, 90)),
    "lowres": lambda im: im.resize((im.width // 4, im.height // 4), Image.BILINEAR),
    "huge": lambda im: im.resize((im.width * 5, im.height * 5), Image.BICUBIC),
}
GENERATORS = {"us": us_plate, "cn": cn_plate, "stop": stop_sign, "speed": speed_limit,
              "advisory": advisory, "warning": warning}


def main():
    per_cat = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
    np.random.seed(random.randint(0, 2**31))
    if not os.path.exists(FONT_PATH):
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
    os.makedirs("hard", exist_ok=True)
    expected = {}
    for cat, gen in GENERATORS.items():
        for i in range(per_cat):
            img, text = gen()
            names = random.sample(list(DEGRADATIONS), k=random.choice([1, 2, 2, 3]))
            for n in names:
                img = DEGRADATIONS[n](img)
            ext = random.choice(["png", "jpg", "tiff"])
            name = f"{cat}_{i:02d}_{'-'.join(names)}.{ext}"
            if ext == "jpg":
                img.save(f"hard/{name}", quality=random.choice([25, 40, 70, 90]))
            else:
                img.save(f"hard/{name}")
            expected[name] = text
    json.dump(expected, open("hard/expected.json", "w"), ensure_ascii=False, indent=1)
    print(len(expected), "images")


if __name__ == "__main__":
    main()
